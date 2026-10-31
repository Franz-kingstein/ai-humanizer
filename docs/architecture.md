# Architecture

AI Humanizer is a two-service application: a Next.js frontend and a FastAPI
backend that owns all NLP and inference work. This document describes the
system as it is actually implemented, not an aspirational design.

## High-level flow

```
Browser (:3001)
   │  fetch  /api/analyze | /api/humanize | /api/compare
   ▼
Next.js (src/lib/api.ts)          — thin client, no business logic
   │  JSON over HTTP, CORS to backend
   ▼
FastAPI (backend/app/main.py)     — routing, validation, request IDs
   │
   ▼
HumanizationPipeline              — orchestrator (singleton)
   ├── TextAnalyzer               — all linguistic metrics
   ├── Humanizer (abstract)       — text rewriting
   │      └── TransformersHumanizer  |  OllamaHumanizer
   ├── SemanticValidator          — cosine similarity (singleton)
   ├── check_content_preservation — deterministic number/URL/date checks
   └── calculate_naturalness_score — weighted heuristic score
```

## Key structural decision: singletons

Three objects are created **once per process** and reused across requests.
This is enforced in code, not convention:

| Object | Created in | Why |
|---|---|---|
| `HumanizationPipeline` | `pipeline.get_pipeline()` | owns the transformer weights |
| `SemanticValidator` | `semantic_validator.get_semantic_validator()` | owns a SentenceTransformer |
| spaCy `Language` | loaded inside `get_pipeline()` | ~50 MB model, expensive to load |

```python
_pipeline: Optional[HumanizationPipeline] = None

def get_pipeline(settings=None, nlp=None) -> HumanizationPipeline:
    global _pipeline
    if _pipeline is None:
        if nlp is None:
            nlp = spacy.load(settings.spacy_model)
        _pipeline = HumanizationPipeline(settings, nlp)
    return _pipeline
```

`reset_pipeline()` exists for tests.

**Why this matters:** a previous version returned a fresh pipeline on every
call. Because `TransformersHumanizer.load_model()` guards on `self._loaded`
(an instance flag), each new instance re-downloaded and re-loaded the model
weights. A 4-request test sequence produced 4 full model loads. The lifespan
handler in `main.py` also built its own standalone humanizer, so startup alone
cost two loads. Both are now routed through the singleton — the process logs
exactly **one** `Model loaded successfully`.

## Request lifecycle

1. HTTP middleware assigns `X-Request-ID` (incoming header is honoured, else a
   truncated UUID is generated).
2. Route validates input against `MAX_INPUT_CHARACTERS` / `MAX_INPUT_WORDS`.
3. Route delegates to a service — **routes contain no business logic**.
4. Service does the work and returns a Pydantic response model.
5. Exception handler catches anything unhandled and returns a generic 500;
   the detail is logged server-side with the request ID.

## Privacy model

`STORE_USER_TEXT=false` (the default in `.env`).

When disabled, logs record only:

- request ID
- word count of the submitted text
- latency
- model name / device
- status and errors

The raw document is never written to a log line. Text is held in memory only
for the duration of the request — there is no database, no cache, and no
persistence layer in this milestone.

## Configuration

All runtime behaviour comes from `backend/.env`, loaded by pydantic-settings
into `app.config.Settings` (cached with `lru_cache`). Nothing behavioural is
hard-coded in the metric logic; weights, thresholds, model names and limits
are all settings.

## Future migration seams

The architecture is deliberately shaped so the inference layer can be swapped
without touching the pipeline:

- `Humanizer` is an abstract base class (`humanize`, `is_available`,
  `get_model_info`). `get_humanizer()` is a factory switching on
  `MODEL_PROVIDER`.
- `transformers` and `ollama` are implemented; `vllm` and `triton` are declared
  in the `ModelProvider` enum but not yet built.
- The pipeline consumes only the `HumanizationResult` dataclass
  (`text`, `model_info`, `processing_time_ms`), so a remote inference server
  behind Triton/vLLM returns the same shape.
- Metrics are independent of the model provider entirely.

Docker is not part of this milestone; see `deployment.md` for the current
run instructions and what a containerised layout would add.

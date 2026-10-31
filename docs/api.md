# API

Base URL: `http://127.0.0.1:8000`
Interactive docs: `http://127.0.0.1:8000/docs`

All request and response shapes are Pydantic models from
`app/models/schemas.py`. Routes contain **no business logic** — each delegates
to a service.

## Endpoints

| Method | Path | Purpose |
|---|---|---|
| GET | `/health` | liveness + device/GPU info |
| GET | `/health/model` | model-specific health |
| POST | `/api/analyze` | linguistic metrics only |
| POST | `/api/humanize` | rewrite only |
| POST | `/api/compare` | full pipeline |
| GET | `/api/models` | current + candidate models |

### GET `/health`

```json
{
  "status": "healthy",
  "version": "0.1.0",
  "model_loaded": true,
  "device": "cpu",
  "gpu_available": false,
  "gpu_memory_used_mb": null,
  "gpu_memory_total_mb": null
}
```

### GET `/health/model`

Reports whether the humanizer actually loaded. Returns
`"status": "healthy"` when loaded, `"degraded"` when not, and logs the model
name and device server-side. (Previously this endpoint duplicated `/health`
verbatim; it now reports model state.)

### POST `/api/analyze`

Request:

```json
{ "text": "string (1..20000 chars)", "include_details": true }
```

Response:

```json
{
  "request_id": "ad80f0d0",
  "analysis": {
    "basic_stats":       { "character_count", "word_count", "sentence_count", "paragraph_count", ... },
    "sentence_stats":    { "min_length", "max_length", "mean_length", "median_length",
                           "std_dev", "coefficient_of_variation", "lengths": [18,5,9] },
    "lexical_metrics":   { "type_token_ratio", "root_ttr", "corrected_ttr", "herdan_c",
                           "lexical_density", "hapax_legomena_ratio", "most_repeated_words", ... },
    "readability":       { "flesch_reading_ease", "flesch_kincaid_grade", "gunning_fog", ... },
    "pos_distribution":  { "counts", "percentages", "total_tokens" },
    "punctuation_distribution": { "counts", "percentages", "total_punctuation" },
    "conjunction_indicators":   { "coordinating", "subordinating", "correlative", "conjunctive_adverbs", "total" },
    "syntax_features":   { "dependency_distribution", "nsubj_count", "dobj_count", ... },
    "ngram_repetition":  { "repeated_bigrams", "repeated_trigrams",
                           "bigram_repetition_ratio", "trigram_repetition_ratio", ... },
    "template_phrases":  { "template_phrases_found", "total_template_occurrences",
                           "template_phrase_density", "unique_templates_used" },
    "passive_voice":     { "passive_sentences", "total_sentences", "passive_ratio",
                           "passive_examples", "note" }
  },
  "naturalness_score": {
    "score": 63.19,
    "components": { "sentence_variation": 67.5, "lexical_diversity": 100.0, ... },
    "interpretation": "...",
    "disclaimer": "This Naturalness Score is a heuristic research metric ..."
  },
  "warnings": [],
  "processing_time_ms": 12.4
}
```

Field names worth noting: POS uses `counts` (not `pos_counts`); passive voice
uses `passive_sentences` (not `passive_count`).

### POST `/api/humanize`

Request:

```json
{
  "text": "string",
  "style": "natural | academic | professional | casual | technical",
  "strength": "low | medium | high",
  "preserve_formatting": true
}
```

Response: `request_id`, `original_text`, `humanized_text`, `style`,
`strength`, `semantic_similarity`, `content_preservation_warnings[]`,
`processing_time_ms`, `model_info`.

Runs one rewrite + validation pass, **without** the retry loop or before/after
analysis. Use `/api/compare` for the complete pipeline.

### POST `/api/compare`

Same request shape as `/api/humanize`. This is the full pipeline:

```
input → original analysis → humanize (with bounded retries)
      → semantic validation → content preservation
      → humanized analysis → score → comparison
```

Response:

```json
{
  "request_id": "...",
  "original_analysis":  { ... },
  "humanized_analysis": { ... },
  "humanized_text": "...",
  "semantic_similarity": 0.8803,
  "naturalness_score_before": { "score": 63.19, "components": {...}, ... },
  "naturalness_score_after":  { "score": 60.64, "components": {...}, ... },
  "metric_comparison": {
    "basic_stats":       { "word_count": {"before","after","change"}, ... },
    "lexical_diversity": { "type_token_ratio": {...} },
    "readability":       { "flesch_reading_ease": {...} },
    "repetition":        { "bigram_repetition_ratio": {...} },
    "template_phrases":  { "template_phrase_density": {...} },
    "passive_voice":     { "passive_ratio": {...} },
    "naturalness_score": {...}
  },
  "content_preservation_warnings": [
    { "type": "missing_numbers", "message": "Numbers missing in rewritten text: ['2023']", "severity": "warning" }
  ],
  "processing_time_ms": 28408,
  "model_info": { "name": "Qwen/Qwen2.5-0.5B-Instruct", "device": "cpu", ... }
}
```

`change` is always `after − before`.

### GET `/api/models`

```json
{
  "current": { "name", "provider", "device", "loaded", "quantization" },
  "available": [ { "name", "provider", "device", "loaded", "quantization" }, ... ]
}
```

The `available` list is a **static** catalogue of candidates suitable for a
6 GB GPU — it is not produced by measurement. See `model_selection.md`.

## Validation and limits

- `text`: `min_length=1`, `max_length=20000` at the schema level.
- Routes additionally enforce `MAX_INPUT_CHARACTERS` (10000) and
  `MAX_INPUT_WORDS` (1500), returning **400** with a clear message.
- Unknown `style` / `strength` values return **422** (enum validation).

## Errors

| Code | Meaning |
|---|---|
| 400 | text exceeds configured length or word limit |
| 422 | invalid enum value or schema violation |
| 500 | `{"detail": "Internal server error"}` — specifics logged with request ID |

A global exception handler catches everything unhandled. Service-level
failures are logged as `Request <id>: analysis failed: <error>` and re-raised
as HTTP 500 with a short message.

## Request ID

Header `X-Request-ID`. If the client supplies one it is echoed back; otherwise
a truncated UUID is generated. The ID appears in every log line for that
request — and, when `STORE_USER_TEXT=false`, is the only identifier logged
(no document content).

## CORS

`CORS_ORIGINS` in `backend/.env`, defaulting to
`http://localhost:3000`, `http://127.0.0.1:3000`, `http://localhost:3001`,
`http://127.0.0.1:3001`.

## Warm-up behaviour

Models load during FastAPI startup (lifespan), not on first request:

```
Loading spaCy model: en_core_web_sm          → loaded
Loading semantic model: all-MiniLM-L6-v2     → loaded
Loading model: Qwen/Qwen2.5-0.5B-Instruct    → loaded
Application startup complete
```

Expect several seconds between process start and readiness; poll `/health`
before sending traffic. Startup logs exactly **one** model load.

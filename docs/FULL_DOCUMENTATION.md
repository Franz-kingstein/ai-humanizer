# AI Humanizer — Complete Documentation

> **Single consolidated document.** Combines architecture, NLP pipeline,
> humanization, metrics, model selection, evaluation, API, deployment and
> limitations into one reference.
>
> Generated from the actual implementation in this repository.

---

## Table of Contents

1. [Overview](#1-overview)
2. [Critical Disclaimer](#2-critical-disclaimer)
3. [Architecture](#3-architecture)
4. [NLP Pipeline](#4-nlp-pipeline)
5. [Humanization](#5-humanization)
6. [Semantic Validation & Content Preservation](#6-semantic-validation--content-preservation)
7. [Metrics & Naturalness Score](#7-metrics--naturalness-score)
8. [Model Selection](#8-model-selection)
9. [Evaluation & Testing](#9-evaluation--testing)
10. [API Reference](#10-api-reference)
11. [Deployment](#11-deployment)
12. [Limitations](#12-limitations)
13. [Current Status & Roadmap](#13-current-status--roadmap)

---

## 1. Overview

AI Humanizer is a research-oriented NLP application that analyses text for
measurable writing-pattern characteristics, rewrites it with a locally
runnable open-weight model, validates semantic preservation, and compares
linguistic metrics before and after.

**Stack**

| Layer | Technology |
|---|---|
| Frontend | Next.js 16 + TypeScript + Tailwind CSS |
| Backend | Python 3.12 + FastAPI |
| NLP | spaCy (`en_core_web_sm`), textstat |
| Rewriting | `Qwen/Qwen2.5-0.5B-Instruct` (local, CPU) |
| Semantic | `sentence-transformers/all-MiniLM-L6-v2` |
| Tests | pytest — 45 passing |

**Pipeline**

```
Input
  ↓
Original NLP analysis        ← readability, TTR, repetition, syntax, passive
  ↓
Humanization                 ← local model, 5 styles × 3 strengths
  ↓
Semantic validation          ← MiniLM cosine ≥ 0.85, bounded retry (max 2)
  ↓
Content preservation         ← numbers, percentages, dates, URLs
  ↓
Humanized NLP analysis
  ↓
Naturalness score + delta + warnings
```

All metrics are computed programmatically. **No LLM calculates any metric,
and no metric value is hard-coded.**

**Scope:** Milestone 1 is a local Ubuntu laptop POC. Not in this milestone —
Kubernetes, Helm, Triton, vLLM, Turnitin, PostgreSQL, Redis, Prometheus,
Grafana, cloud deployment, authentication, paid APIs.

---

## 2. Critical Disclaimer

**This system does not detect AI-generated text, and is not designed to evade
Turnitin or any detector.**

- No component outputs a probability of human authorship.
- No component is trained or calibrated on labeled human-vs-generated text.
- The Naturalness Score is a weighted heuristic; its weights were **chosen by
  the project authors, not empirically derived**.
- The generation prompt contains **no** instruction to bypass, evade, defeat or
  make text undetectable to any detector.
- No evaluation measures detector output before and after.

Every API response carrying the score attaches a disclaimer saying exactly
this. Do not present these numbers as detection evidence — in a paper, an
administrative process, or anywhere with consequences for a person.

Rewriting is framed as improving naturalness, readability and content
preservation, with facts, dates, numbers, URLs and named entities held fixed.

**Read §12 before interpreting any number this project produces.**

---

## 3. Architecture

### 3.1 High-level flow

```
Browser (:3001)
   │  fetch  /api/analyze | /api/humanize | /api/compare
   ▼
Next.js (src/lib/api.ts)          — thin client, no business logic
   │  JSON over HTTP, CORS
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

### 3.2 Singletons

Three objects are created **once per process** and reused across requests.
Enforced in code, not convention:

| Object | Created in | Why |
|---|---|---|
| `HumanizationPipeline` | `pipeline.get_pipeline()` | owns transformer weights |
| `SemanticValidator` | `semantic_validator.get_semantic_validator()` | owns a SentenceTransformer |
| spaCy `Language` | loaded inside `get_pipeline()` | ~50 MB, expensive to load |

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

**Why this matters:** an earlier version returned a fresh pipeline per call.
Because `TransformersHumanizer.load_model()` guards on `self._loaded` (an
*instance* flag), every new instance re-loaded the model weights — a 4-request
test produced 4 full loads. The lifespan handler also built a standalone
humanizer, costing two loads at startup alone. Both now route through the
singleton: the process logs exactly **one** `Model loaded successfully`.

### 3.3 Request lifecycle

1. Middleware assigns `X-Request-ID` (honours incoming header, else truncated UUID).
2. Route validates against `MAX_INPUT_CHARACTERS` / `MAX_INPUT_WORDS`.
3. Route delegates to a service — **routes contain no business logic**.
4. Service returns a Pydantic response model.
5. Global exception handler returns generic 500; detail logged with request ID.

### 3.4 Privacy

`STORE_USER_TEXT=false` (default). Logs record only request ID, word count,
latency, model/device, status and errors. The raw document is never logged.
No database, no cache, no persistence — text lives in memory for the request
only.

### 3.5 Configuration

All runtime behaviour comes from `backend/.env`, loaded by pydantic-settings
into `Settings` (cached via `lru_cache`). Weights, thresholds, model names and
limits are settings — nothing behavioural is hard-coded.

### 3.6 Migration seams

- `Humanizer` is an ABC (`humanize`, `is_available`, `get_model_info`);
  `get_humanizer()` is a factory switching on `MODEL_PROVIDER`.
- `transformers` and `ollama` implemented; `vllm`/`triton` declared in the
  enum but not built.
- The pipeline consumes only `HumanizationResult` (`text`, `model_info`,
  `processing_time_ms`) — transport-agnostic, so a remote server drops in.
- Metrics are independent of the provider entirely.

---

## 4. NLP Pipeline

Entry point: `TextAnalyzer.analyze(text) -> AnalysisResult`
(`backend/app/services/analyzer.py`).

### 4.1 Processing order

```
raw text
  ├─ spaCy nlp(text)  → Doc            (en_core_web_sm)
  ├─ tokenize         → words, sentences, paragraphs
  ├─ content/function split (POS-based)
  ├─ calculate_basic_stats
  ├─ calculate_sentence_stats
  ├─ calculate_lexical_metrics
  ├─ calculate_readability            (textstat)
  ├─ analyze_pos / punctuation / conjunctions / syntax
  ├─ analyze_passive_voice            (dependency parse)
  ├─ analyze_ngram_repetition
  └─ analyze_template_phrases
        ▼
  AnalysisResult (Pydantic-serialisable)
```

If spaCy is unavailable the analyzer degrades rather than failing: regex
tokenization and sentence splitting are used, and neutral empty objects are
returned for POS, dependency and passive voice. Readability and lexical
metrics still work.

### 4.2 Module map

| Module | Provides |
|---|---|
| `nlp/tokenizer.py` | `TextTokenizer`, `calculate_basic_stats`, `calculate_sentence_stats`, regex fallbacks |
| `nlp/lexical.py` | `calculate_lexical_metrics` |
| `nlp/repetition.py` | `analyze_ngram_repetition`, `analyze_template_phrases` |
| `nlp/pos.py` | `analyze_pos`, `analyze_punctuation`, `analyze_conjunctions`, `get_syntax_features` |
| `nlp/dependency.py` | `analyze_passive_voice` |
| `nlp/readability.py` | `calculate_readability` |

### 4.3 Basic statistics

Character count, character count excluding whitespace, word count, unique word
count, sentence count, paragraph count, average word length, average sentence
length.

Words are lowercased and filtered to alphabetic tokens (so `94.7%` does not
count as a word). Stopword filtering is controlled by
`USE_STOPWORDS_IN_METRICS`. Paragraphs split on blank lines first, else
single newlines.

### 4.4 Sentence statistics

Min, max, mean, median, standard deviation and coefficient of variation of
words-per-sentence, plus the raw `lengths` array (the frontend charts directly
from it).

`coefficient_of_variation = stdev / mean`, 0 for a single sentence. Uses
`statistics.stdev` (sample), returning 0 rather than raising for one sentence.
This feeds the *sentence variation* score component.

### 4.5 Lexical metrics

| Metric | Definition |
|---|---|
| `type_token_ratio` | unique / total |
| `root_ttr` | Guiraud: unique / √total |
| `corrected_ttr` | Carroll: (unique / √(2·total)) × 100 |
| `herdan_c` / `bilogarithmic_ttr` | log(unique) / log(total) |
| `summer_index` | log(log(unique)) / log(log(total)) |
| `lexical_density` | content words / total words |
| `hapax_legomena_ratio` | words occurring once / unique words |
| `hapax_dislegomena_ratio` | words occurring twice / unique words |
| `most_repeated_words` | top 10 words with count > 1 |

Content vs function words from POS:

- content: `NOUN VERB ADJ ADV PROPN`
- function: `ADP AUX CCONJ DET PART PRON SCONJ`

`summer_index` guards its logarithms (`unique > 1`, `total > e`), returning
`None` instead of raising on short text.

### 4.6 N-gram repetition

Bigrams and trigrams over the lowercased word list, counted with
`collections.Counter`:

- `repeated_bigrams` / `repeated_trigrams` — entries with count > 1
- `bigram_repetition_ratio` — Σ counts of repeated bigrams / total bigrams
- `trigram_repetition_ratio` — same for trigrams
- totals and unique counts for both orders

### 4.7 Template phrase analysis

A configurable list of 40 phrases (`DEFAULT_TEMPLATE_PHRASES`) covering
transition markers, hedging and over-used vocabulary:

```
moreover, furthermore, additionally, in conclusion,
it is important to note that, it is worth noting that,
in today's rapidly evolving world, this highlights the importance,
a key aspect is, in summary, plays a crucial role, delve into,
tapestry, landscape, realm, unleash, revolutionize, game-changer,
cutting-edge, paradigm shift, holistic approach, …
```

Case-insensitive substring matching. Results: `template_phrases_found`,
`total_template_occurrences`, `template_phrase_density` (**per 1000 words**),
`unique_templates_used`.

Measured on real inputs: natural prose ≈ `0–15`, heavily templated text ≈ `155`.

> Reported as **Template Phrase Density** — a measurable writing-pattern
> indicator, explicitly *not* a definitive AI-detection signal. See §12.

### 4.8 Syntax (spaCy)

- **POS distribution** — counts + percentages per universal POS tag.
- **Punctuation distribution** — counts per mark.
- **Conjunctions** — coordinating, subordinating, correlative, conjunctive
  adverbs, from fixed word lists.
- **Dependency features** — distribution over labels plus counts of `nsubj`,
  `dobj`, `prep`, `advcl`, `relcl`, `ccomp`, `xcomp`.
- **Passive voice (estimated)** — a sentence is passive if any `VERB` token has
  an `auxpass` child, an `nsubjpass` child, or `Voice=Pass` morphology. Up to
  5 example sentences returned.

Passive detection is an **estimate** with known limitations, and the API
returns those limitations verbatim in the `note` field.

### 4.9 Readability — and the bug that was fixed

Nine textstat measures: Flesch Reading Ease, Flesch-Kincaid Grade, Gunning
Fog, SMOG, ARI, Coleman-Liau, LIX, RIX, Dale-Chall.

Originally all nine were computed inside **one** `try` block. textstat raises
`KeyError` when its CMU dictionary cannot look up a token:

| Input | Token built | Result |
|---|---|---|
| `94.7%` | `947` | `KeyError` |
| `https://example.com` | `httpsexamplecom` | `KeyError` |
| `example.com` | `examplecom` | `KeyError` |
| `fast-changing` | `fastchanging` | `KeyError` |

Because they shared one `try`, a single such token set **all nine fields to
`null`** — any text with a number, URL or hyphen reported no readability, and
the score's readability component silently fell back to a constant 50.

**Fix — two layers:**

1. **Per-metric isolation** — `_safe()` evaluates each formula independently.
2. **Neutralising fallback** — if Flesch still fails, constructs the dictionary
   cannot handle are replaced *whole*: URLs/domains → `two`, numbers → `two`,
   letter-to-letter hyphens → space, any remaining non-alphabetic token → `two`.

The "whole construct" detail is load-bearing: replacing `94.7%` with
`two.two` only creates a new unknown token (`twotwo`) — which is why the
earlier fragment-based attempt still failed.

Four regression tests: `TestReadabilityRobustness`.

### 4.10 Empty input

`analyze("")` returns a fully-populated `AnalysisResult` of zeros/`None`
rather than raising, so the frontend can render an empty state safely.

---

## 5. Humanization

### 5.1 Abstraction

```python
class Humanizer(ABC):
    def humanize(self, text, style, strength) -> HumanizationResult: ...
    def is_available(self) -> bool: ...
    def get_model_info(self) -> Dict[str, Any]: ...
```

`HumanizationResult` carries `text`, `model_info`, `processing_time_ms`.

| Provider | Status |
|---|---|
| `TransformersHumanizer` | implemented — local `transformers` weights |
| `OllamaHumanizer` | implemented — local Ollama daemon |
| `VLLMHumanizer` | enum declared, not built |
| `TritonHumanizer` | enum declared, not built |

Selected by `MODEL_PROVIDER` through `get_humanizer()`.

### 5.2 Styles

`HumanizationStyle` selects a prompt instruction:

- **natural** — conversational, varied structures, authentic voice
- **academic** — precise terminology, formal, objective, structured argument
- **professional** — clear, concise, polished business register
- **casual** — contractions, simpler vocabulary, relaxed structure
- **technical** — precise terminology, unambiguous, detail-preserving

### 5.3 Strength

`HumanizationStrength` maps to generation parameters — this is where strength
actually takes effect:

| Strength | temperature | top_p | repetition_penalty | max_new_tokens × |
|---|---|---|---|---|
| `low` | 0.50 | 0.85 | 1.05 | 1.0 |
| `medium` | 0.70 | 0.90 | 1.10 | 1.2 |
| `high` | 0.85 | 0.95 | 1.15 | 1.5 |

Higher strength raises sampling temperature and widens nucleus sampling so the
model restructures more freely, and scales the output budget.

Note: strength comes from `get_strength_params()`, so
`HUMANIZER_TEMPERATURE` / `HUMANIZER_TOP_P` / `HUMANIZER_REPETITION_PENALTY`
in `.env` are defaults that the per-strength table overrides during generation.

### 5.4 The prompt

Built by `build_humanization_prompt()`. Contract with the model:

1. **Preserve all facts** — numbers, dates, percentages, statistics,
   measurements, named entities, technical terms, citations, URLs, proper nouns.
2. **Preserve meaning** — same information and intent.
3. **Do not add information** — no new facts, claims, examples, details.
4. **Do not remove information** — no dropping factual content.
5. **Apply the selected style.**

Plus strength level, the original text, then the instruction to return the
rewritten text. It also asks the model to vary sentence structure naturally,
reduce unnecessary repetition, reduce excessive template transitions, improve
natural readability and maintain a coherent tone.

Deliberately **absent**: any instruction about bypassing, evading or defeating
detectors or Turnitin.

### 5.5 Validation loop

```
generate
   ↓
content preservation (deterministic)
semantic similarity  (MiniLM cosine ≥ SEMANTIC_SIMILARITY_THRESHOLD)
   │
   ├── valid  → accept
   └── invalid → regenerate, up to MAX_REWRITE_ATTEMPTS (default 2)
```

Implemented in `HumanizationPipeline.compare()`. Iterates
`max_rewrite_attempts + 1` times — always terminates, never infinite. Across
attempts it keeps the result with the **highest semantic similarity**, so a
bounded loop never returns something worse than an earlier attempt.

### 5.6 Device and quantisation

`TransformersHumanizer` resolves device from `MODEL_DEVICE` (`auto` → CUDA →
MPS → CPU).

Quantisation (`none` / `8bit` / `4bit`) applies **only on CUDA**. On CPU the
code removes `quantization_config` and logs `Quantization disabled for CPU
device` — bitsandbytes kernels are not meaningful there.

Because `device_map="auto"` shards weights arbitrarily, the runtime device is
read back via `next(self.model.parameters()).device` before moving inputs.

### 5.7 Performance and memory

Generation is sequential, so output length dominates latency. `.env` sets
`HUMANIZER_MAX_NEW_TOKENS=384` (down from 1024), taking a full compare run
from ~56 s to ~15–28 s on CPU.

| Setting | Backend RSS |
|---|---|
| default threading | 2.46 GB |
| `OMP_NUM_THREADS=4 MKL_NUM_THREADS=4` | **1.47 GB** |

The model loads **once** at startup, never per request.

### 5.8 Prompt-injection note

User text is placed inside the prompt after the instructions. A large document
could contain text reading as instructions. Mitigated only by post-hoc
deterministic checks, not prevented — see §12.

---

## 6. Semantic Validation & Content Preservation

### 6.1 Semantic validation

`app/services/semantic_validator.py`

```
Original    → embedding A ┐
                          ├─ cosine similarity → semantic_similarity
Humanized   → embedding B ┘
```

- Model: `sentence-transformers/all-MiniLM-L6-v2` (configurable)
- Embeddings L2-normalised at encode time, so cosine is a plain dot product
- Threshold: `SEMANTIC_SIMILARITY_THRESHOLD`, default **0.85**

`validate()` returns `(similarity, is_valid, warning)`. Below threshold:

> Semantic similarity (0.799) below threshold (0.85). Meaning may not be fully
> preserved.

**An automated indicator, not proof of semantic equivalence.** High score means
the embeddings are close; it does not certify that facts, dates or
qualifications survived. A legitimate style change can also drop the score.

### 6.2 Content preservation

`app/services/preprocessing.py::check_content_preservation()` — fully
deterministic, regex-based, no model.

Four extractions compared as **sets**:

| Check | Pattern basis |
|---|---|
| Numbers | `\b\d+(?:[.,]\d+)?\b`, normalised (commas stripped) |
| Percentages | `\d+(?:[.,]\d+)?\s*%`, normalised |
| Dates | `MM/DD/YYYY`, `YYYY/MM/DD`, `Mon D, YYYY`, `D Mon YYYY` |
| URLs | `https?://…`, trailing sentence punctuation stripped |

Each mismatch produces explicit warnings — missing *and* unexpected, both
directions:

```
Numbers missing in rewritten text: ['2023']
Unexpected percentages in rewritten text: ['94.7%']
URLs missing in rewritten text: ['https://example.com']
```

Nothing is silently accepted. The response also carries a `details` block with
full original/rewritten/missing/extra lists and four `*_match` booleans.

**Observed failure this catches:** a real run emitted *both* the original
`https://example.com` and a hallucinated `http://example.com`. The URL check
flagged it (`urls_match: false`) — it catches invented content as well as
dropped content.

**Covered categories only:** numbers, percentages, dates, URLs. Named entities,
negation, citations and qualifiers are unprotected — see §12.

---

## 7. Metrics & Naturalness Score

Two kinds of number, which must not be conflated:

1. **Linguistic metrics** — direct, reproducible measurements (§4).
2. **Naturalness / Humanization Score** — a project-specific composite.

### 7.1 The score

Computed by `app/services/metrics.py::calculate_naturalness_score(analysis, text)`.

Named **Naturalness Score**, never "probability of human authorship". Every
response carrying it also carries:

> This Naturalness Score is a heuristic research metric based on linguistic
> features. It does NOT definitively measure whether text was written by a
> human or AI. High scores indicate more varied, diverse, and naturalistic
> writing patterns. Low scores suggest more repetitive, formulaic, or
> template-like patterns. Results should be interpreted cautiously and in
> context.

### 7.2 Weights

Stored in configuration, **not** code:

```yaml
humanization_score:
  sentence_variation: 0.20
  lexical_diversity:  0.20
  repetition:         0.20
  template_density:   0.15
  passive_voice:      0.10
  readability:        0.15
  semantic_coherence: 0.00   # reported, not weighted
```

Sum to 1.0. Changing a weight requires only an `.env` edit.

> These are **heuristic weights chosen by the project authors**. There is no
> empirical calibration behind 0.20 vs 0.15. A documented, adjustable starting
> point — not a validated instrument.

### 7.3 Component derivations (0–100)

| Component | Source metric | Mapping |
|---|---|---|
| `sentence_variation` | `sentence_stats.coefficient_of_variation` | `min(cv × 100, 100)` |
| `lexical_diversity` | `lexical_metrics.type_token_ratio` | `min(ttr × 200, 100)` |
| `repetition` | mean of bigram + trigram ratios | `max(100 − avg × 200, 0)` |
| `template_density` | density per 1000 words | `max(100 − density × 2, 0)` |
| `passive_voice` | `passive_voice.passive_ratio` | `max(100 − ratio × 200, 0)` |
| `readability` | `flesch_reading_ease` | 100 if 60–70; decay 2/point above 70, 3/point below 60; 50 if unavailable |
| `semantic_coherence` | `compute_semantic_coherence(text)` | adjacent-sentence cosine |

Interpretation bands: ≥80 high, ≥60 moderate, ≥40 low, <40 very low.

### 7.4 Four defects found and fixed

Found by measuring real inputs, not by inspection.

**1. A component was hard-coded.** `semantic_coherence` was a literal `70.0`
while carrying 10% weight — a constant contribution to every document,
violating the project's own "no hard-coded metric results" rule.

**2. Template-density mapping always returned 0.** Formula was
`100 − density × 10`. Real densities are 0–155 per 1000 words, so anything
above density 10 underflowed to 0 — *every* realistic input. Before and after
both scored 0: no signal at all.

| Text | density | old | new |
|---|---|---|---|
| natural prose | 0.00 | 0.0 | 100.0 |
| templated prose | 155.56 | 0.0 | 0.0 |

**3. The coherence metric measured the wrong thing.** The first replacement
used Jaccard overlap of content-word sets between adjacent sentences — that
rewards *literal repetition*, not coherence. Natural prose scored **0.0** while
a sentence-repeating sample scored 70. Replaced with term-frequency cosine over
adjacent sentences.

**4. Readability was silently neutral.** With Flesch returning `null` (§4.9),
the readability component fell back to a constant 50 for both texts — a third
silent no-op.

**Effect:** natural vs templated sample now separates properly:

```
AI-ish template-heavy   45.9
natural prose           70.6
```

### 7.5 Known weak component

`semantic_coherence` is weighted **0.00**. It computes a real value, but
adjacent-sentence term overlap is a weak proxy — genuine coherence often
involves zero shared content words between neighbouring sentences, while
repetitive text scores high. Rather than ship a misleading component at 10%
weight, it is reported for inspection and excluded from the total until a
better measure exists.

### 7.6 Delta / comparison

`_compare_metrics()` returns `before` / `after` / `change` triples for: word
count, sentence count, average sentence length, type-token ratio, Flesch
Reading Ease, bigram repetition ratio, template phrase density, passive ratio,
naturalness score.

`change` is always `after − before`. For inverse metrics (repetition, passive
ratio, template density) a **negative** change is the improvement.

---

## 8. Model Selection

### 8.1 Honest status

The spec called for `scripts/benchmark_models.py` measuring loading time,
inference latency, peak memory, semantic similarity, readability, lexical
diversity, repetition and template density, writing `results/model_benchmark.csv`.

**This has not been implemented.** `scripts/` and `results/` contain no
benchmark artefacts — `results/` holds only `environment_report.txt`. The
candidate list served by `GET /api/models` is static, not measured.

This section therefore describes how the current model was chosen (hardware
constraint), what the benchmark *would* measure, and what remains. **No
benchmark numbers are quoted, because none were measured.**

### 8.2 Hardware

From `results/environment_report.txt`:

| Property | Value |
|---|---|
| GPU | NVIDIA GeForce RTX 3060 Laptop |
| VRAM | 6144 MiB (6 GB) |
| Compute capability | 8.6 |
| Driver / CUDA | 575.64.03 / 12.9 |
| PyTorch | 2.5.1+cu124 |
| RAM | 7.2 GB total |
| CPU | 16 logical cores |
| OS | Ubuntu 24.04.4 LTS |

**CUDA is currently unavailable to PyTorch.** `nvidia-smi` reports the GPU
correctly and `/dev/nvidia*` nodes exist, but `torch.cuda.is_available()`
returns `False` with `CUDA unknown error`. `device_count()` returns 1 while
`get_device_name()` raises — **the count alone is not a usable health check.**

Classic post-suspend `nvidia_uvm` fault. Repair needs root:

```bash
sudo rmmod nvidia_uvm && sudo modprobe nvidia_uvm
```

**Not run** — requires a sudo password the agent does not have and did not
request. Until fixed, inference runs on CPU.

### 8.3 Current configuration

```env
MODEL_DEVICE=cpu
HUMANIZER_MODEL_NAME=Qwen/Qwen2.5-0.5B-Instruct
HUMANIZER_QUANTIZATION=8bit    # ignored on CPU; quantisation is CUDA-only
HUMANIZER_MAX_NEW_TOKENS=384
```

Selected for **CPU feasibility, not as a quality verdict**: ~0.5 B parameters in
float32 ≈ 2 GB, fitting alongside torch and spaCy. The 1.5B / 3B variants
listed by `GET /api/models` are annotated `cuda` and unsuitable while CUDA is
broken.

Measured backend RSS: **1.47 GB** with `OMP_NUM_THREADS=4 MKL_NUM_THREADS=4`
(2.46 GB at default).

### 8.4 Candidate considerations

Priority: quality, semantic preservation, local feasibility, memory, licence,
speed.

**Licences were not verified** — no model card was inspected for this
milestone. Treat every licence as unknown pending review. Do not redistribute
any model until its licence is read and confirmed.

| Model | Approx. size (fp16) | Notes |
|---|---|---|
| `Qwen/Qwen2.5-0.5B-Instruct` | ~1 GB | **in use.** Fits CPU + 6 GB VRAM |
| `Qwen/Qwen2.5-1.5B-Instruct` | ~3 GB | feasible in 4-bit on GPU |
| `Qwen/Qwen2.5-3B-Instruct` | ~6 GB | needs 4-bit to fit 6 GB VRAM |
| `microsoft/Phi-3-mini-4k-instruct` | ~7.6 GB | requires 4-bit |
| `microsoft/Phi-3.5-mini-instruct` | ~7.6 GB | requires 4-bit |
| `google/gemma-2-2b-it` | ~5 GB | strong quality at this size |
| `meta-llama/Llama-3.2-1B-Instruct` | ~2 GB | **gated** — needs HF auth |
| `meta-llama/Llama-3.2-3B-Instruct` | ~6 GB | **gated** — needs HF auth |

Both Llama entries require accepting a licence and authenticating on Hugging
Face — an external decision (licence acceptance + credential), so neither is a
default candidate.

### 8.5 What the benchmark must measure

On the same fixed sample set, per candidate:

| Metric | How |
|---|---|
| Model loading time | wall clock around `load_model()` |
| Inference latency | wall clock around `humanize()` |
| Peak memory | `tracemalloc`; `torch.cuda.max_memory_allocated()` when CUDA works |
| Semantic similarity | MiniLM cosine vs original |
| Readability | Flesch before → after |
| Lexical diversity | TTR before → after |
| Repetition | bigram/trigram ratios before → after |
| Template phrase density | per 1000 words before → after |

Plus generated outputs for **manual inspection**. Selection must not be made on
speed alone — a fast model that degrades similarity or drops numbers is worse
than a slower one that does not.

---

## 9. Evaluation & Testing

### 9.1 Test suite

```bash
cd backend
./venv/bin/python -m pytest tests/ -q
# 45 passed
```

`tests/test_nlp.py` uses short, deterministic strings so expected values are
exact.

| Area | Tests |
|---|---|
| Tokenization / word & sentence counting | `TestTokenizer` |
| Basic statistics | `TestBasicStatistics` |
| Sentence statistics (incl. CV) | `TestSentenceStatistics` |
| TTR and lexical metrics | `TestLexicalMetrics` |
| Readability | `TestReadability` |
| Readability robustness (numbers, URLs, hyphens) | `TestReadabilityRobustness` |
| N-gram repetition | `TestNGramRepetition` |
| Template phrase detection | `TestTemplatePhrases` |
| Passive voice estimation | `TestPassiveVoice` |
| POS / punctuation | `TestPOSAnalysis` |
| Full analyzer integration | `TestFullAnalysis` |
| Semantic coherence metric | `TestSemanticCoherence` |

**Known coverage gaps:**

- **No tests for the humanization path** — `humanize`, the retry loop and both
  providers are untested (need model weights).
- **No API route tests** — endpoints verified by manual `curl` only.
- Score weighting logic covered only by one determinism check.

### 9.2 Manual end-to-end verification

```bash
curl -s -X POST http://127.0.0.1:8000/api/compare \
  -H 'Content-Type: application/json' \
  -d '{"text":"...","style":"natural","strength":"medium"}' | python3 -m json.tool
```

Latest observed run (CPU, Qwen2.5-0.5B, medium):

| Field | Value |
|---|---|
| HTTP | 200 |
| Semantic similarity | 0.8803 (≥ 0.85 → pass) |
| Naturalness | 63.19 → 60.64 |
| Flesch | 43.76 → value present |
| Template density | 68.18 → 40.0 |
| Passive ratio | 0.4 → 0.25 |
| Latency | ~28 s |

Note the naturalness score **decreased**. That is honest output, not a bug:
sentence variation fell (CV 0.675 → 0.257) and carries 0.20 weight. A rewrite
can improve some components and worsen others; the score reports the net.

---

## 10. API Reference

Base URL: `http://127.0.0.1:8000` · Docs: `http://127.0.0.1:8000/docs`

All shapes are Pydantic models from `app/models/schemas.py`. Routes contain
**no business logic**.

### 10.1 Endpoints

| Method | Path | Purpose |
|---|---|---|
| GET | `/health` | liveness + device/GPU info |
| GET | `/health/model` | model-specific health |
| POST | `/api/analyze` | linguistic metrics only |
| POST | `/api/humanize` | rewrite only |
| POST | `/api/compare` | full pipeline |
| GET | `/api/models` | current + candidate models |

### 10.2 `GET /health`

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

### 10.3 `GET /health/model`

Reports whether the humanizer loaded: `"healthy"` when loaded, `"degraded"`
when not, logging model name and device server-side. (Previously duplicated
`/health` verbatim; now reports model state.)

### 10.4 `POST /api/analyze`

Request:

```json
{ "text": "string (1..20000 chars)", "include_details": true }
```

Response:

```json
{
  "request_id": "ad80f0d0",
  "analysis": {
    "basic_stats":       { "character_count", "word_count", "sentence_count", "paragraph_count" },
    "sentence_stats":    { "min_length", "max_length", "mean_length", "median_length",
                           "std_dev", "coefficient_of_variation", "lengths": [18,5,9] },
    "lexical_metrics":   { "type_token_ratio", "root_ttr", "corrected_ttr", "herdan_c",
                           "lexical_density", "hapax_legomena_ratio", "most_repeated_words" },
    "readability":       { "flesch_reading_ease", "flesch_kincaid_grade", "gunning_fog" },
    "pos_distribution":  { "counts", "percentages", "total_tokens" },
    "punctuation_distribution": { "counts", "percentages", "total_punctuation" },
    "conjunction_indicators":   { "coordinating", "subordinating", "correlative", "conjunctive_adverbs", "total" },
    "syntax_features":   { "dependency_distribution", "nsubj_count", "dobj_count" },
    "ngram_repetition":  { "repeated_bigrams", "repeated_trigrams",
                           "bigram_repetition_ratio", "trigram_repetition_ratio" },
    "template_phrases":  { "template_phrases_found", "total_template_occurrences",
                           "template_phrase_density", "unique_templates_used" },
    "passive_voice":     { "passive_sentences", "total_sentences", "passive_ratio",
                           "passive_examples", "note" }
  },
  "naturalness_score": {
    "score": 63.19,
    "components": { "sentence_variation": 67.5, "lexical_diversity": 100.0 },
    "interpretation": "...",
    "disclaimer": "This Naturalness Score is a heuristic research metric ..."
  },
  "warnings": [],
  "processing_time_ms": 12.4
}
```

Field names worth noting: POS uses `counts` (not `pos_counts`); passive voice
uses `passive_sentences` (not `passive_count`).

### 10.5 `POST /api/humanize`

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

One rewrite + validation pass — **without** the retry loop or before/after
analysis. Use `/api/compare` for the complete pipeline.

### 10.6 `POST /api/compare`

Same request shape. The full pipeline:

```
input → original analysis → humanize (bounded retries)
      → semantic validation → content preservation
      → humanized analysis → score → comparison
```

Response:

```json
{
  "request_id": "...",
  "original_analysis":  {},
  "humanized_analysis": {},
  "humanized_text": "...",
  "semantic_similarity": 0.8803,
  "naturalness_score_before": { "score": 63.19, "components": {} },
  "naturalness_score_after":  { "score": 60.64, "components": {} },
  "metric_comparison": {
    "basic_stats":       { "word_count": {"before","after","change"} },
    "lexical_diversity": { "type_token_ratio": {} },
    "readability":       { "flesch_reading_ease": {} },
    "repetition":        { "bigram_repetition_ratio": {} },
    "template_phrases":  { "template_phrase_density": {} },
    "passive_voice":     { "passive_ratio": {} },
    "naturalness_score": {}
  },
  "content_preservation_warnings": [
    { "type": "missing_numbers", "message": "Numbers missing in rewritten text: ['2023']", "severity": "warning" }
  ],
  "processing_time_ms": 28408,
  "model_info": { "name": "Qwen/Qwen2.5-0.5B-Instruct", "device": "cpu" }
}
```

`change` is always `after − before`.

### 10.7 `GET /api/models`

```json
{
  "current":  { "name", "provider", "device", "loaded", "quantization" },
  "available":[ { "name", "provider", "device", "loaded", "quantization" } ]
}
```

The `available` list is a **static** catalogue for a 6 GB GPU — not measured
results. See §8.

### 10.8 Validation and errors

- `text`: `min_length=1`, `max_length=20000` at schema level.
- Routes additionally enforce `MAX_INPUT_CHARACTERS` (10000) and
  `MAX_INPUT_WORDS` (1500) → **400**.
- Invalid `style`/`strength` → **422** (enum validation).
- **500** → `{"detail": "Internal server error"}`; specifics logged with
  request ID as `Request <id>: analysis failed: <error>`.

### 10.9 Request ID & CORS

Header `X-Request-ID` — echoed if supplied, else truncated UUID generated. It
appears in every log line for that request, and with `STORE_USER_TEXT=false`
it is the only identifier logged.

CORS: `http://localhost:3000`, `http://127.0.0.1:3000`, `http://localhost:3001`,
`http://127.0.0.1:3001`.

### 10.10 Warm-up

Models load during FastAPI startup (lifespan), not first request:

```
Loading spaCy model: en_core_web_sm          → loaded
Loading semantic model: all-MiniLM-L6-v2     → loaded
Loading model: Qwen/Qwen2.5-0.5B-Instruct    → loaded
Application startup complete
```

Expect several seconds before readiness — poll `/health` first. Startup logs
exactly **one** model load.

---

## 11. Deployment

**Milestone 1 is a local Ubuntu laptop POC.** No Docker, no Kubernetes, no
cloud, no authentication — deliberately.

### 11.1 Run

```bash
# Backend — port 8000
cd ai-humanizer/backend
OMP_NUM_THREADS=4 MKL_NUM_THREADS=4 ./venv/bin/uvicorn app.main:app \
  --host 127.0.0.1 --port 8000

# Frontend — port 3001 (separate terminal)
cd ai-humanizer/frontend
npm run dev
```

Open **http://localhost:3001**.

> Port 3000 is occupied on this machine, so Next falls back to 3001 and logs
> `⚠ Port 3000 is in use by an unknown process, using available port 3001
> instead.` `.env.local` and backend CORS both already include 3001.

> **Next.js 16.4.0 stops the dev server once** to display a security-upgrade
> notice. Run `npm run dev` a second time — it proceeds normally on retry.

### 11.2 Detached / background

```bash
cd ai-humanizer/backend
OMP_NUM_THREADS=4 MKL_NUM_THREADS=4 \
  setsid nohup ./venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000 \
  > /tmp/backend.log 2>&1 < /dev/null &

cd ai-humanizer/frontend
setsid nohup npm run dev > /tmp/frontend.log 2>&1 < /dev/null &
```

`setsid` matters: without it, child processes are reaped when the launching
shell exits and both servers die silently.

### 11.3 Stop

```bash
pkill -f "uvi[c]orn app[.]main"
pkill -f "n[e]xt de[v]"
```

The bracket expressions prevent `pkill -f` from matching its own command line
and killing the shell running it.

### 11.4 Setup from scratch

```bash
cd backend
python3 -m venv .venv
.venv/bin/pip install --upgrade pip
.venv/bin/pip install -r requirements.txt       # torch cu124 ≈ 2.5 GB
.venv/bin/python -m spacy download en_core_web_sm

cd ../frontend && npm install
```

Verify:

```bash
.venv/bin/python -m pytest tests/ -q   # expect 45 passed
curl http://127.0.0.1:8000/health      # expect 200
```

Full capture: `results/environment_report.txt`.

### 11.5 Configuration

`backend/.env` (template: `.env.example`), loaded by pydantic-settings.

| Key | Value | Note |
|---|---|---|
| `MODEL_DEVICE` | `cpu` | CUDA broken, see §8 |
| `HUMANIZER_MODEL_NAME` | `Qwen/Qwen2.5-0.5B-Instruct` | fits RAM |
| `HUMANIZER_MAX_NEW_TOKENS` | `384` | lowered from 1024 for latency |
| `SEMANTIC_SIMILARITY_THRESHOLD` | `0.85` | |
| `MAX_REWRITE_ATTEMPTS` | `2` | bounded loop |
| `STORE_USER_TEXT` | `false` | privacy default |
| `SPACY_MODEL` | `en_core_web_sm` | |

`.env` contains **no secrets** — model names and thresholds only. It is
gitignored; `.env.example` is the committed template. Gated models (Llama 3.2)
would need an `HF_TOKEN`, but none is configured or committed.

### 11.6 Memory tuning

| Threading | Backend RSS |
|---|---|
| default | 2.46 GB |
| `OMP_NUM_THREADS=4 MKL_NUM_THREADS=4` | **1.47 GB** |

On a 7.2 GB machine this matters. Keep the limits for long-running sessions.

### 11.7 CUDA repair (recommended)

```bash
sudo rmmod nvidia_uvm && sudo modprobe nvidia_uvm
python3 -c "import torch; print(torch.cuda.is_available())"
```

Then `MODEL_DEVICE=auto`, consider `HUMANIZER_QUANTIZATION=4bit`. Expected:
latency drops from CPU tens-of-seconds to interactive.

### 11.8 Health checks

```bash
curl http://127.0.0.1:8000/health         # liveness
curl http://127.0.0.1:8000/health/model   # model loaded?
curl http://127.0.0.1:8000/api/models     # catalogue
```

### 11.9 Roadmap (not implemented)

```
Docker → GPU inference → vLLM/Triton → Kubernetes → College server
```

**Docker (next)** — specified but **not built**: no `backend/Dockerfile`,
`frontend/Dockerfile` or `docker-compose.yml`. Spec requires the containerised
version to still run locally. Design already supports it: ABC + provider
factory, transport-agnostic `HumanizationResult`, all config via env vars,
models load at startup.

**Out of scope for this milestone:** Kubernetes, Helm, Triton, vLLM, Turnitin,
PostgreSQL, Redis, Prometheus, Grafana, cloud deployment, authentication,
paid APIs.

---

## 12. Limitations

**The most important section for anyone interpreting results.**

### 12.1 This is not an AI detector

- No component outputs a probability of human authorship.
- No component is trained or calibrated on labeled corpora.
- "Template Phrase Density" counts a configurable phrase list — those phrases
  ("moreover", "in conclusion", "however") occur in human writing constantly.
- Score weights (0.20 / 0.15 / 0.10 …) were **chosen by the authors, not
  empirically derived**.

Every score-bearing response attaches a disclaimer saying exactly this. Do not
present these numbers as detection evidence — in a paper, an administrative
process, or anywhere with consequences for a person.

### 12.2 This is not a detector-bypass system

- The prompt contains no instruction to bypass, evade, defeat or make text
  undetectable to any detector.
- No evaluation measures detector output before and after.
- No Turnitin integration, none planned.

### 12.3 Semantic similarity ≠ equivalence

Threshold 0.85 on MiniLM cosine is an **automated indicator only**:

- High cosine means embeddings are close — not that qualifications, negations,
  causal claims or numeric context survived.
- A model can preserve all facts yet fall below threshold after a legitimate
  style change.
- Conversely it can score well above while altering a detail the embedding
  does not weight heavily.

The deterministic checks exist because of this — and cover only four categories
(§12.5).

### 12.4 Passive voice is an estimate

Returned verbatim in every `passive_voice.note`:

1. Misses passives without a *by*-phrase (short passives)
2. Misclassifies adjectival passives ("The door is closed")
3. Does not detect get-passives ("The window got broken")
4. Accuracy varies by domain and complexity
5. Approximate indicators only

### 12.5 Content preservation covers only four categories

Numbers, percentages, dates, URLs. **Unprotected:**

- **Named entities** — a person, organisation or place can change silently.
- **Negation** — "does not improve" → "improves" produces no warning.
- **Citations and technical terms** — no check.
- **Quantifiers/qualifiers** — "most", "roughly", "up to" unprotected.
- **Ranges/versions** — `2.5-0.5B` may split in ways the regex misses.

Set comparison is also order- and duplicate-insensitive: three identical
numbers collapsing to one passes silently.

### 12.6 Readability values are sometimes approximated

textstat fails on tokens missing from its CMU dictionary. The fix neutralises
those constructs to a filler word, so scores **are returned** rather than null
— but substituting `two` for `94.7%` changes syllable/word counts slightly.
Readability for text heavy in numbers, URLs or hyphenation is directionally
right, not exact.

### 12.7 The score can move the wrong way

A rewrite improving readability and cutting template phrases can still drop the
total if sentence variation falls (weight 0.20). Observed: **63.19 → 60.64**
while improving template density (68.18 → 40.0) and passive ratio
(0.4 → 0.25).

The score is a net of trade-offs, not a monotonic "how much better" meter.
**Read the components, not just the total.**

### 12.8 `semantic_coherence` is weighted 0.00

Adjacent-sentence term cosine is a weak proxy — genuine coherence often
involves zero shared content words, while repetitive text scores high. Reported
but excluded from the total until a better measure exists.

### 12.9 CUDA is unavailable

`torch.cuda.is_available()` → `False` with `CUDA unknown error`, despite
`nvidia-smi` showing a healthy RTX 3060 (6 GB, driver 575.64.03) and
`/dev/nvidia*` present. `device_count()` returns 1 while `get_device_name()`
raises — **device count alone is not a valid health check.**

Everything runs on CPU at **15–37 seconds** per compare run. Repair needs root
and has not been run (§11.7). Until then `HUMANIZER_QUANTIZATION=8bit` has no
effect — quantisation is CUDA-only here.

### 12.10 Model quality is constrained by hardware

`Qwen/Qwen2.5-0.5B-Instruct` was chosen for CPU feasibility, not quality. A
0.5 B model rewrites less faithfully — observed real failures: dropping `2023`
from output, hallucinating a second URL variant. Both were caught by the
preservation checks, but they happened.

### 12.11 Benchmarking has not been implemented

`scripts/benchmark_models.py` does not exist. `results/` holds only
`environment_report.txt` — **no `model_benchmark.csv`, no measured numbers.**

- No candidate has been benchmarked.
- No model was selected on evidence — a hardware-constraint decision.
- `GET /api/models` is a static catalogue.
- **No licence verified** for any candidate. Llama 3.2 entries are gated.

**No benchmark figure should be quoted from this repository.**

### 12.12 Test coverage is partial

45 tests pass, covering the **NLP analysis layer only**. Untested: humanization
path, retry loop, both providers, semantic validation, content preservation,
score weighting (one determinism check), and **all API routes**. API verified
manually with `curl`.

### 12.13 Other known gaps

- **Prompt injection** — user text follows the instructions in the prompt; a
  large document could contain text reading as instructions. Mitigated only by
  post-hoc checks, not prevented.
- **No persistence, auth or rate limiting** — anyone reaching port 8000 can
  use the model.
- **Single document at a time** — no batching or queueing.
- **No frontend tests, no CI.**
- **Next.js 16.4.0 has a published security advisory**; dev server pauses once
  to display it. Not yet upgraded.
- **Input limits** fixed at 10000 chars / 1500 words.
- **English only** (`en_core_web_sm`); metrics degrade on other languages.
- **Long documents** truncate at 384 output tokens — a long input may be cut
  mid-rewrite with no warning.

---

## 13. Current Status & Roadmap

### Status

| | |
|---|---|
| Tests | **45 passing** |
| Backend | ✅ runs, model loads once at startup |
| Frontend | ✅ runs on :3001 |
| Backend RAM | 1.47 GB with thread limits |
| CUDA | ❌ unavailable — needs `sudo rmmod nvidia_uvm && sudo modprobe nvidia_uvm` |
| Benchmark | ❌ `scripts/benchmark_models.py` not built |
| Docker | ❌ not built (next milestone) |

### Known issues

1. **CUDA broken** — stale `nvidia_uvm`; CPU-only at 15–37 s per compare.
2. **No model benchmark** — model choice is a constraint decision, not
   evidence-based. No licences verified.
3. **Test coverage is analysis-only** — humanization, retry loop and all API
   routes untested.
4. **Next.js 16.4.0** security advisory — not upgraded.

### Bugs fixed during development

| Bug | Impact | Fix |
|---|---|---|
| Readability single `try` block | All 9 metrics `null` for text with numbers/URLs/hyphens | Per-metric isolation + whole-token neutralisation |
| Pipeline built per request | Model reloaded every request (4 loads / 4 requests) | Process-wide singleton |
| Lifespan built its own humanizer | 2 loads at startup alone | Routed through singleton |
| spaCy not passed to pipeline | Passive/POS/syntax metrics all empty | Loaded inside `get_pipeline()` |
| `semantic_coherence = 70.0` | Constant 10% of every score | Real computation |
| Template density `100 − d×10` | Component always 0 for real input | `100 − d×2` |
| Coherence via Jaccard | Natural prose scored 0.0 | Term-frequency cosine |
| Duplicate warnings | Same warning shown 2–3× | Dedupe by (type, message) |
| `/health/model` duplicated `/health` | No model info | Reports model state |
| URL trailing punctuation | `example.com).` treated as URL | Strip trailing chars |

### Roadmap

```
Docker → GPU inference → vLLM/Triton → Kubernetes → College server
```

Each stage only after the previous works.

---

## Appendix — Repository layout

```
ai-humanizer/
├── backend/
│   ├── app/
│   │   ├── api/routes/      health, analyze, humanize, compare, models
│   │   ├── nlp/             tokenizer, lexical, repetition, pos, dependency, readability
│   │   ├── services/        analyzer, pipeline, metrics, semantic_validator,
│   │   │                    humanizer (+ transformers/ollama), preprocessing
│   │   ├── models/          schemas (Pydantic), enums
│   │   ├── config.py        pydantic-settings
│   │   └── main.py          FastAPI app + lifespan
│   ├── tests/test_nlp.py    45 tests
│   ├── requirements.txt
│   └── .env                 ← config (not committed)
├── frontend/src/
│   ├── app/page.tsx         main GUI
│   ├── components/          TextEditor, AnalysisDisplay, Charts, MetricCard, icons
│   └── lib/                 api, types, utils
├── docs/                    this document + per-topic files
├── results/                 environment_report.txt
├── data/samples/            (empty)
└── scripts/                 (empty — benchmark not built)
```

**Document generated from the implementation as it exists in this repository.**

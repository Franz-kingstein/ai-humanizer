# Evaluation

How the system judges a rewrite, and how to evaluate the system itself.

## Semantic validation

`app/services/semantic_validator.py`.

```
Original    → embedding A ┐
                          ├─ cosine similarity → semantic_similarity
Humanized   → embedding B ┘
```

- Model: `sentence-transformers/all-MiniLM-L6-v2` (configurable)
- Embeddings are L2-normalised at encode time, so the cosine is a plain dot
  product.
- Threshold: `SEMANTIC_SIMILARITY_THRESHOLD`, default **0.85**

`validate()` returns a tuple `(similarity, is_valid, warning)`. When the score
falls below the threshold, `is_valid` is `false` and a warning is attached:

> Semantic similarity (0.799) below threshold (0.85). Meaning may not be fully
> preserved.

**This is an automated indicator, not proof of semantic equivalence.** A high
score means the embeddings are close; it does not certify that facts, dates or
qualifications survived intact. Conversely a legitimate style change can drop
the score. The deterministic checks below exist precisely because embedding
similarity cannot be trusted alone.

## Content preservation

`app/services/preprocessing.py::check_content_preservation()` — fully
deterministic, regex-based, no model involved.

Four extractions are compared as **sets** between original and rewritten:

| Check | Pattern basis |
|---|---|
| Numbers | `\b\d+(?:[.,]\d+)?\b`, normalised (commas stripped) |
| Percentages | `\d+(?:[.,]\d+)?\s*%`, normalised |
| Dates | `MM/DD/YYYY`, `YYYY/MM/DD`, `Mon D, YYYY`, `D Mon YYYY` |
| URLs | `https?://…`, trailing sentence punctuation stripped |

Each mismatch produces an explicit warning — missing items *and* unexpected
items, in both directions:

```
Numbers missing in rewritten text: ['2023']
Unexpected percentages in rewritten text: ['94.7%']
URLs missing in rewritten text: ['https://example.com']
```

Nothing is silently accepted. The response also carries a `details` block with
the full original/rewritten/missing/extra lists for each category, and four
boolean `*_match` flags.

### Observed failure this catches

A real run produced a rewrite in which the model emitted **both** the original
`https://example.com` and a hallucinated `http://example.com`. The URL check
flagged it (`urls_match: false`). This is the intended behaviour: the check
catches content the model invented as well as content it dropped.

## The rewrite loop

```
Generate
   ↓
Preservation check + Semantic check
   ↓
Similarity ≥ 0.85 ?
   ├── yes → accept
   └── no  → regenerate   (max MAX_REWRITE_ATTEMPTS = 2)
```

Bounded at `max_rewrite_attempts + 1` total generations — never an infinite
loop. The loop tracks the highest-similarity result across attempts and
returns that, so exhausting retries still yields the best candidate seen.

Cost note: each retry is another full CPU generation, so a run that exhausts
retries takes roughly 2–3× a clean run (observed ~28–37 s vs ~15 s).

## Metric comparison

`_compare_metrics()` produces `before` / `after` / `change` triples — see
`metrics.md`. Improvement direction differs by metric: for repetition,
template density and passive ratio a **negative** change is the improvement.

## Test suite

```bash
cd backend
./venv/bin/python -m pytest tests/ -q
# 45 passed
```

`tests/test_nlp.py` uses short, deterministic strings so expected values are
exact. Coverage by area:

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

Known gaps in test coverage:

- **No tests for the humanization path** — `humanize`, the retry loop and the
  transformers humanizer are untested (they need model weights).
- **No API route tests** — endpoints are verified by manual `curl` only.
- **No test asserts the 45 tests cover `metrics.py` weighting** beyond one
  determinism check.

## Manual end-to-end verification

```bash
curl -s -X POST http://127.0.0.1:8000/api/compare \
  -H 'Content-Type: application/json' \
  -d '{"text":"...","style":"natural","strength":"medium"}' | python3 -m json.tool
```

Latest observed run (CPU, Qwen2.5-0.5B, medium strength):

| Field | Value |
|---|---|
| HTTP | 200 |
| Semantic similarity | 0.8803 (≥ 0.85 → pass) |
| Naturalness | 63.19 → 60.64 |
| Flesch | 43.76 → value present |
| Template density | 68.18 → 40.0 |
| Passive ratio | 0.4 → 0.25 |
| Latency | ~28 s |

Note the naturalness score **decreased** on this run. That is honest output,
not a bug: sentence variation fell (CV 0.675 → 0.257) and that component
carries 0.20 weight. A model can improve some components and worsen others;
the score reports the net.

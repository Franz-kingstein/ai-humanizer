# Metrics

Two kinds of number come out of this system, and they must not be conflated:

1. **Linguistic metrics** — direct, reproducible measurements of the text
   (readability, TTR, repetition, passive ratio…). Defined in `nlp_pipeline.md`.
2. **The Naturalness / Humanization Score** — a project-specific *composite*
   built from weighted components.

## Naturalness / Humanization Score

Computed by `app/services/metrics.py::calculate_naturalness_score(analysis, text)`.

It is named **Naturalness Score**, never "probability of human authorship".
Every API response carrying it also carries this disclaimer verbatim:

> This Naturalness Score is a heuristic research metric based on linguistic
> features. It does NOT definitively measure whether text was written by a
> human or AI. High scores indicate more varied, diverse, and naturalistic
> writing patterns. Low scores suggest more repetitive, formulaic, or
> template-like patterns. Results should be interpreted cautiously and in
> context.

### Weights

Stored in configuration (`backend/.env` → `Settings`), **not** in code:

```yaml
humanization_score:
  sentence_variation: 0.20
  lexical_diversity:  0.20
  repetition:         0.20
  template_density:   0.15
  passive_voice:      0.10
  readability:        0.15
  semantic_coherence: 0.00   # reported, not weighted (see below)
```

They sum to 1.0. Changing a weight requires only an `.env` edit.

> These are **heuristic weights chosen by the project authors**. There is no
> empirical calibration behind 0.20 vs 0.15. They are a documented, adjustable
> starting point — not a validated instrument.

### Component derivations (0–100 scale)

| Component | Source metric | Mapping |
|---|---|---|
| `sentence_variation` | `sentence_stats.coefficient_of_variation` | `min(cv × 100, 100)` |
| `lexical_diversity` | `lexical_metrics.type_token_ratio` | `min(ttr × 200, 100)` |
| `repetition` | mean of bigram + trigram repetition ratios | `max(100 − avg × 200, 0)` — lower repetition scores higher |
| `template_density` | `template_phrases.template_phrase_density` (per 1000 words) | `max(100 − density × 2, 0)` |
| `passive_voice` | `passive_voice.passive_ratio` | `max(100 − ratio × 200, 0)` |
| `readability` | `flesch_reading_ease` | 100 if 60–70; else decay 2/point above 70, 3/point below 60; 50 if unavailable |
| `semantic_coherence` | `compute_semantic_coherence(text)` | adjacent-sentence cosine, see below |

Interpretation bands: ≥80 high, ≥60 moderate, ≥40 low, <40 very low.

### Fixes applied to this score

Three defects made the score uninformative in practice. All were found by
measuring real inputs rather than by inspection.

**1. A component was hard-coded.** `semantic_coherence` was a literal `70.0`
while carrying 10% weight — a constant contribution to every document,
violating the project's own "no hard-coded metric results" rule. It now
computes from the text.

**2. The template-density mapping always returned 0.** The formula was
`100 − density × 10`. Real densities are 0–155 per 1000 words, so anything
above density 10 underflowed to 0 — which is *every* realistic input. Both
before and after scored 0, so the component carried no signal. Now
`100 − density × 2` (0 → 100, 50+ → 0).

Measured before/after on the same inputs:

| Text | density | old component | new component |
|---|---|---|---|
| natural prose | 0.00 | 0.0 | 100.0 |
| templated prose | 155.56 | 0.0 | 0.0 |

**3. The coherence metric measured the wrong thing.** The first replacement
used Jaccard overlap of content-word sets between adjacent sentences. That
rewards *literal word repetition*, not coherence — natural prose scored **0.0**
while a sentence-repeating sample scored 70. Replaced with a term-frequency
cosine over adjacent sentences, which responds to topical continuity instead
of repeated strings.

**4. Readability was silently neutral.** With Flesch returning `null` (see
`nlp_pipeline.md`), the readability component fell back to a constant 50 for
both texts — a third silent no-op. Fixed by the readability fix.

### Effect of the fixes

Natural vs templated sample, weights applied:

```
AI-ish template-heavy   45.9
natural prose           70.6
```

Before the fixes the two separated by much less, because two of six weighted
components were constants regardless of input.

### Known weak component

`semantic_coherence` is now weighted **0.00**. It computes a real value, but
adjacent-sentence term overlap is a weak proxy — genuine coherence often
involves zero shared content words between neighbouring sentences. Rather
than ship a misleading component at 10% weight, it is reported for
inspection and excluded from the total until a better-defined measure exists.

## Delta / comparison

`_compare_metrics()` returns a `before` / `after` / `change` triple for:

- word count, sentence count, average sentence length
- type-token ratio
- Flesch Reading Ease
- bigram repetition ratio
- template phrase density
- passive ratio
- naturalness score

`change` is always `after − before`, so a positive change means the metric
rose — for inverse metrics like repetition and passive ratio, a *negative*
change is the improvement.

## What these metrics are not

- Not a detector. No component estimates the probability a human wrote text.
- Not evidence of authorship. Template phrase density and repetition describe
  writing patterns that occur in both human and generated text.
- Not calibrated against any labeled corpus.

See `limitations.md`.

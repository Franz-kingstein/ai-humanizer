# NLP Pipeline

Every metric in this system is computed programmatically from the text. **No
LLM is used to calculate any metric**, and no result is hard-coded.

Entry point: `TextAnalyzer.analyze(text) -> AnalysisResult`
(`backend/app/services/analyzer.py`).

## Processing order

```
raw text
  │
  ├─ spaCy nlp(text)  → Doc            (en_core_web_sm)
  │
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

If spaCy is unavailable the analyzer degrades rather than failing: it falls
back to regex tokenization and sentence splitting, and returns neutral empty
objects for POS, dependency and passive voice. Readability and lexical
metrics still work in that mode.

## Module map

| Module | Provides |
|---|---|
| `nlp/tokenizer.py` | `TextTokenizer`, `calculate_basic_stats`, `calculate_sentence_stats`, regex fallbacks |
| `nlp/lexical.py` | `calculate_lexical_metrics` |
| `nlp/repetition.py` | `analyze_ngram_repetition`, `analyze_template_phrases` |
| `nlp/pos.py` | `analyze_pos`, `analyze_punctuation`, `analyze_conjunctions`, `get_syntax_features` |
| `nlp/dependency.py` | `analyze_passive_voice` |
| `nlp/readability.py` | `calculate_readability` |

## Basic statistics

Character count, character count excluding whitespace, word count, unique word
count, sentence count, paragraph count, average word length, average sentence
length.

Words are lowercased and filtered to alphabetic tokens (so `94.7%` does not
count as a word). Stopword filtering is controlled by
`USE_STOPWORDS_IN_METRICS`.

Paragraphs are split on blank lines first; if the text has none, single
newlines are used.

## Sentence statistics

Min, max, mean, median, standard deviation and coefficient of variation of
words-per-sentence, plus the raw `lengths` array — the frontend charts the
distribution directly from that array.

`coefficient_of_variation = stdev / mean`, zero when there is only one
sentence. This is the input to the *sentence variation* score component.

The standard deviation uses `statistics.stdev` (sample), returning 0 for a
single sentence rather than raising.

## Lexical metrics

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

Content vs function words come from POS tags:

- content: `NOUN VERB ADJ ADV PROPN`
- function: `ADP AUX CCONJ DET PART PRON SCONJ`

`summer_index` guards its logarithms (`unique > 1`, `total > e`), returning
`None` instead of raising on short text.

## N-gram repetition

Bigrams and trigrams are extracted over the lowercased word list, counted with
`collections.Counter`, and reported as:

- `repeated_bigrams` / `repeated_trigrams` — entries with count > 1
- `bigram_repetition_ratio` — Σ counts of repeated bigrams / total bigrams
- `trigram_repetition_ratio` — same for trigrams
- totals and unique counts for both orders

## Template phrase analysis

A configurable list of 40 phrases (`DEFAULT_TEMPLATE_PHRASES` in
`repetition.py`) covers transition markers, hedging constructions and
frequently over-used vocabulary:

```
moreover, furthermore, additionally, in conclusion,
it is important to note that, it is worth noting that,
in today's rapidly evolving world, this highlights the importance,
a key aspect is, in summary, plays a crucial role, delve into,
tapestry, landscape, realm, unleash, revolutionize, game-changer,
cutting-edge, paradigm shift, holistic approach, …
```

Matching is case-insensitive substring search. Results:

- `template_phrases_found` — phrase + count
- `total_template_occurrences`
- `template_phrase_density` — **occurrences per 1000 words**
- `unique_templates_used`

Measured on real inputs, natural prose sits near `0–15` while heavily
templated text reaches `155`. This value feeds the *template density* score
component (see `metrics.md`).

> This is reported as **Template Phrase Density** — a measurable writing-
> pattern indicator. It is explicitly *not* a definitive AI-detection signal.
> See `limitations.md`.

## Syntax (spaCy)

- **POS distribution** — counts and percentages per universal POS tag.
- **Punctuation distribution** — counts per punctuation mark.
- **Conjunctions** — coordinating, subordinating, correlative, conjunctive
  adverbs, from fixed word lists.
- **Dependency features** — distribution over dependency labels plus counts of
  `nsubj`, `dobj`, `prep`, `advcl`, `relcl`, `ccomp`, `xcomp`.
- **Passive voice (estimated)** — a sentence counts as passive if any `VERB`
  token has an `auxpass` child, an `nsubjpass` child, or `Voice=Pass` in its
  morphology. Up to 5 example sentences are returned.

Passive detection is an **estimate** with known limitations, and the API
returns those limitations verbatim in the `note` field rather than presenting
the number as ground truth.

## Readability

Nine textstat measures: Flesch Reading Ease, Flesch-Kincaid Grade, Gunning
Fog, SMOG, ARI, Coleman-Liau, LIX, RIX, Dale-Chall.

### The failure mode that was fixed

Originally all nine metrics were computed inside **one** `try` block. textstat
raises `KeyError` when its CMU pronouncing dictionary cannot look up a token,
which happens for:

| Input | Token textstat builds | Result |
|---|---|---|
| `94.7%` | `947` | `KeyError` |
| `https://example.com` | `httpsexamplecom` | `KeyError` |
| `example.com` | `examplecom` | `KeyError` |
| `fast-changing` | `fastchanging` | `KeyError` |

Because they shared one `try`, a single such token set **all nine fields to
`null`** — so any text containing a number, URL or hyphenated word reported no
readability at all, and the score's readability component silently fell back
to a neutral 50.

The fix has two layers:

1. **Per-metric isolation** — `_safe()` evaluates each formula independently
   so one failure cannot nullify the others.
2. **Neutralising fallback** — if Flesch still fails, constructs that the
   dictionary cannot handle are replaced *whole* before retrying:
   URLs/domains → `two`, numbers → `two`, letter-to-letter hyphens → space,
   and any remaining non-alphabetic token → `two`.

The "whole construct" detail is load-bearing: replacing `94.7%` with
`two.two` only creates a new unknown token (`twotwo`), which is why the
earlier fragment-based attempt still failed.

Four regression tests cover these cases in `tests/test_nlp.py`
(`TestReadabilityRobustness`).

## Empty input

`analyze("")` returns a fully-populated `AnalysisResult` of zeros/`None`
instead of raising, so the frontend can render an empty state safely.

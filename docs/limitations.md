# Limitations

This document states what the system **cannot** do. It is the most important
file in this repository for anyone interpreting results.

## 1. This is not an AI detector

The system does not, and cannot, determine whether text was written by a human
or by a model.

- No component outputs a probability of human authorship.
- No component is trained or calibrated on any labeled corpus of human vs.
  generated text.
- "Template Phrase Density" measures how often a configurable list of phrases
  appears. Those phrases occur in human writing constantly — "moreover",
  "in conclusion" and "however" are ordinary English.
- The Naturalness Score is a weighted heuristic over linguistic features. Its
  weights (0.20 / 0.15 / 0.10 …) were **chosen by the project authors, not
  empirically derived**.

Every API response carrying the score attaches a disclaimer saying exactly
this. Do not present these numbers as detection evidence, in a paper, an
administrative process, or anywhere with consequences for a person.

## 2. This is not a detector-bypass system

The project deliberately does **not** position itself against Turnitin or any
similarity/AI detector.

- The generation prompt contains no instruction to bypass, evade, defeat or
  make text undetectable to any detector.
- No evaluation in this repository measures detector output before and after.
- There is no Turnitin integration and none is planned for this milestone.

Rewriting is framed as improving naturalness, readability and content
preservation — with facts, dates, numbers, URLs and named entities held fixed.

## 3. Semantic similarity is not proof of equivalence

`SEMANTIC_SIMILARITY_THRESHOLD=0.85` on MiniLM cosine similarity is an
**automated indicator only**.

- High cosine means the embeddings are close. It does **not** certify that
  qualifications, negations, causal claims or numeric context survived.
- A model can preserve all facts yet score below threshold after a legitimate
  style change.
- Conversely, it can score well above threshold while silently altering a
  detail the embedding does not weight heavily.

The deterministic number/percentage/date/URL checks exist because embedding
similarity cannot be trusted alone — and those checks only cover those four
categories (see §5).

## 4. Passive voice is an estimate

Dependency-based detection has documented failure modes, returned verbatim in
every `passive_voice.note` field:

1. Misses passives without a *by*-phrase (short passives)
2. Misclassifies adjectival passives ("The door is closed")
3. Does not detect get-passives ("The window got broken")
4. Accuracy varies by domain and sentence complexity
5. Approximate indicators only

## 5. Content preservation covers only four categories

Numbers, percentages, dates and URLs. Anything else can be silently altered:

- **Named entities** — a person, organisation or place can be changed without
  any warning.
- **Negation** — "does not improve" → "improves" produces no warning.
- **Citations and technical terms** — no check.
- **Quantifiers and qualifiers** — "most", "roughly", "up to" unprotected.
- **Numbers inside ranges or versions** — `2.5-0.5B` may be split or dropped
  in ways the regex does not flag.

Set comparison is also order-insensitive and duplicate-insensitive: three
identical numbers collapsing to one passes silently.

## 6. Readability values are sometimes approximated

textstat's syllable counter fails on tokens missing from its CMU dictionary —
numbers (`947`), URLs (`examplecom`), hyphenated compounds (`fastchanging`).

The fix neutralises those constructs to a filler word before recomputing, so
scores **are returned** rather than null. But substituting `two` for `94.7%`
changes syllable and word counts slightly, so readability for text heavy in
numbers, URLs or hyphenation is approximate — directionally right, not exact.

## 7. The Naturalness Score can move the wrong way

A rewrite improving readability and cutting template phrases can still drop
the total if sentence variation falls — that component carries 0.20. An
observed run went **63.19 → 60.64** while improving template density
(68.18 → 40.0) and passive ratio (0.4 → 0.25).

The score is a net of trade-offs, not a monotonic "how much better did this
get" meter. Read the components, not just the total.

## 8. `semantic_coherence` is reported but weighted 0.00

Adjacent-sentence term-frequency cosine is a weak proxy for coherence —
genuine coherence frequently involves **zero** shared content words between
neighbouring sentences, while repetitive text scores high. Rather than ship a
misleading component at 10% weight, it is computed and displayed but excluded
from the total until a better measure exists.

## 9. CUDA is unavailable on this machine

`torch.cuda.is_available()` returns `False` with `CUDA unknown error`, despite
`nvidia-smi` showing a healthy RTX 3060 (6 GB, driver 575.64.03) and
`/dev/nvidia*` nodes being present. `device_count()` returns 1 while
`get_device_name()` raises — **device count alone is not a valid health check.**

Consequences: everything runs on CPU, and observed latency is **15–37 seconds**
per full compare run. Repair needs root and has not been run:

```bash
sudo rmmod nvidia_uvm && sudo modprobe nvidia_uvm
```

Until then, `HUMANIZER_QUANTIZATION=8bit` in `.env` has no effect (quantisation
is CUDA-only in this codebase).

## 10. Model quality is constrained by hardware

`Qwen/Qwen2.5-0.5B-Instruct` was chosen for CPU feasibility, not quality. A
0.5 B model rewrites less faithfully than larger ones — observed real failures
include dropping `2023` from output and hallucinating a second URL variant.
Both were caught by the preservation checks, but they happened.

## 11. Benchmarking has not been implemented

`scripts/benchmark_models.py` does not exist. `results/` contains only
`environment_report.txt` — **no `model_benchmark.csv`, no measured numbers.**

Consequently:

- No candidate model has been benchmarked.
- No model was selected on evidence; the choice was a hardware-constraint
  decision.
- `GET /api/models` returns a static catalogue, not measured results.
- No licence has been verified for any candidate model. Llama 3.2 entries are
  gated and require HF authentication plus licence acceptance.

No benchmark figure should be quoted from this repository.

## 12. Test coverage is partial

45 tests pass, but they cover the **NLP analysis layer only**:

- Untested: the humanization path, the retry loop, both humanizer providers,
  semantic validation, content preservation, the score weighting logic (one
  determinism check), and **all API routes**.
- API verification has been done manually with `curl`.

## 13. Other known gaps

- **Prompt injection** — user text is embedded in the prompt after the
  instructions. A large document could contain text reading as instructions.
  Mitigated only by post-hoc deterministic checks, not prevented.
- **No persistence, no auth, no rate limiting** — anyone who can reach port
  8000 can use the model.
- **Single document at a time** — no batching, no queueing.
- **No frontend tests**, no CI.
- **Next.js 16.4.0 has a published security advisory**; the dev server pauses
  once to display it. Not yet upgraded.
- **Input limits** are configurable but fixed at 10000 chars / 1500 words.
- **English only** — `en_core_web_sm`; metrics degrade on other languages.
- **Long documents** truncate at `HUMANIZER_MAX_NEW_TOKENS=384` output tokens,
  so a long input may be cut off mid-rewrite with no warning.

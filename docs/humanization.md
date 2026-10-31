# Humanization

The humanizer rewrites text to read more naturally while preserving factual
content. It does **not** attempt to defeat AI detectors, evade Turnitin, or
make text "undetectable" — the prompt contains no such instruction, and the
project makes no detection-evasion claim anywhere.

## Abstraction

`app/services/humanizer.py` defines the contract:

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

Selection is by `MODEL_PROVIDER` through `get_humanizer()`. The pipeline only
ever sees `HumanizationResult`, so a remote server behind vLLM/Triton drops in
without pipeline changes.

## Styles

`HumanizationStyle` (`natural`, `academic`, `professional`, `casual`,
`technical`) selects a style instruction injected into the prompt:

- **natural** — conversational, varied structures, authentic voice
- **academic** — precise terminology, formal, objective, structured argument
- **professional** — clear, concise, polished business register
- **casual** — contractions, simpler vocabulary, relaxed structure
- **technical** — precise terminology, unambiguous, detail-preserving

## Strength

`HumanizationStrength` maps to generation parameters — this is where strength
actually takes effect:

| Strength | temperature | top_p | repetition_penalty | max_new_tokens × |
|---|---|---|---|---|
| `low` | 0.50 | 0.85 | 1.05 | 1.0 |
| `medium` | 0.70 | 0.90 | 1.10 | 1.2 |
| `high` | 0.85 | 0.95 | 1.15 | 1.5 |

Higher strength raises sampling temperature and widens the nucleus so the
model takes more liberty with restructuring, and scales the output budget.

Note that strength parameters come from `get_strength_params()`, so the
`HUMANIZER_TEMPERATURE` / `HUMANIZER_TOP_P` / `HUMANIZER_REPETITION_PENALTY`
values in `.env` are defaults that the per-strength table overrides during
generation.

## The prompt

Built by `build_humanization_prompt()`. Its contract with the model:

1. **Preserve all facts** — numbers, dates, percentages, statistics,
   measurements, named entities, technical terms, citations, URLs and proper
   nouns must remain exactly the same.
2. **Preserve meaning** — same information and intent.
3. **Do not add information** — no new facts, claims, examples or details.
4. **Do not remove information** — no dropping factual content.
5. **Apply the selected style.**

Plus the strength level, then the original text, then the instruction to
return the rewritten text.

The prompt additionally asks the model to vary sentence structure naturally,
reduce unnecessary repetition, reduce excessive template transitions, improve
natural readability and maintain a coherent tone.

Deliberately **absent** from the prompt: any instruction about bypassing,
evading or defeating detectors or Turnitin.

## Validation loop

```
generate
   ↓
content preservation check (deterministic)
semantic similarity check  (MiniLM cosine ≥ SEMANTIC_SIMILARITY_THRESHOLD)
   │
   ├── valid  → accept
   └── invalid → regenerate, up to MAX_REWRITE_ATTEMPTS (default 2)
```

Implemented in `HumanizationPipeline.compare()`. The loop is bounded — it
iterates `max_rewrite_attempts + 1` times and always terminates. Across
attempts it keeps the result with the **highest semantic similarity**, so a
bounded loop never returns something worse than an earlier attempt.

See `evaluation.md` for how similarity and preservation are scored.

## Device and quantisation

`TransformersHumanizer` resolves device from `MODEL_DEVICE` (`auto` →
CUDA → MPS → CPU).

Quantisation (`HUMANIZER_QUANTIZATION`: `none`, `8bit`, `4bit`) is applied
**only on CUDA**. On CPU the code removes `quantization_config` and logs
`Quantization disabled for CPU device` — bitsandbytes 4/8-bit kernels are not
meaningful there, and attempting it would fail.

Because `device_map="auto"` shards weights arbitrarily, the runtime device is
read back with `next(self.model.parameters()).device` before moving inputs,
rather than assuming the configured device.

## Performance and memory

Generation is sequential, so output length dominates latency. The current
`.env` sets `HUMANIZER_MAX_NEW_TOKENS=384` (reduced from 1024), which took a
full compare run from ~56 s to ~15–28 s on CPU.

Memory on this laptop:

| Setting | Backend RSS |
|---|---|
| default threading | 2.46 GB |
| `OMP_NUM_THREADS=4 MKL_NUM_THREADS=4` | **1.47 GB** |

The model loads **once** at application startup, never per request.

## Prompt-injection note

The user's text is placed inside the prompt after the instructions. A
sufficiently large document could contain text that reads as instructions to
the model. This is not mitigated beyond the deterministic post-hoc content
checks — see `limitations.md`.

# Model Selection

## Honest status

The project specification called for a benchmark framework
(`scripts/benchmark_models.py`) that loads each candidate, measures loading
time, inference latency, peak memory, semantic similarity, readability,
lexical diversity, repetition and template density, and writes
`results/model_benchmark.csv`.

**This has not been implemented.** `scripts/` and `results/` contain no
benchmark artefacts — `results/` holds only `environment_report.txt`. The
candidate model list is served statically by `GET /api/models`, not generated
from measurement.

This document therefore describes how the current model was chosen (by
hardware constraint), what the benchmark *would* measure, and what remains to
be built. No benchmark numbers are quoted anywhere in this repository,
because none were measured.

## Hardware constraints

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
returns `False` with `CUDA unknown error`. `torch.cuda.device_count()`
returns 1 while `torch.cuda.get_device_name()` raises — so the count alone is
not a usable health check.

The pattern (healthy driver, present device nodes, stale UVM state) is the
classic post-suspend `nvidia_uvm` module fault. Repairing it needs root:

```bash
sudo rmmod nvidia_uvm && sudo modprobe nvidia_uvm
```

This was **not** run — it requires a sudo password, which the agent does not
have and did not request. Until it is fixed, inference runs on CPU.

### Current configuration

```env
MODEL_DEVICE=cpu
HUMANIZER_MODEL_NAME=Qwen/Qwen2.5-0.5B-Instruct
HUMANIZER_QUANTIZATION=8bit    # ignored on CPU; quantisation is CUDA-only
HUMANIZER_MAX_NEW_TOKENS=384
```

`Qwen/Qwen2.5-0.5B-Instruct` was selected for CPU feasibility, not as a
quality verdict: ~0.5 B parameters in float32 is ~2 GB, which fits in RAM
alongside torch and spaCy. The 1.5B / 3B variants listed by `GET /api/models`
are annotated `cuda` and are not suitable for this box while CUDA is broken.

Measured backend RSS: **1.47 GB** with `OMP_NUM_THREADS=4 MKL_NUM_THREADS=4`
(2.46 GB at default threading).

## Candidate considerations

Priority order from the spec: quality, semantic preservation, local
inference feasibility, memory, licence, speed.

Licences were **not verified** — no model card was inspected for this
milestone. Treat every licence field below as unknown pending review. Do not
redistribute any model until its licence is read and confirmed.

| Model | Approx. size (fp16) | Notes |
|---|---|---|
| `Qwen/Qwen2.5-0.5B-Instruct` | ~1 GB | **in use.** Fits CPU + 6 GB VRAM comfortably |
| `Qwen/Qwen2.5-1.5B-Instruct` | ~3 GB | listed; feasible in 4-bit on GPU |
| `Qwen/Qwen2.5-3B-Instruct` | ~6 GB | listed; needs 4-bit to fit 6 GB VRAM |
| `microsoft/Phi-3-mini-4k-instruct` | ~7.6 GB | listed; requires 4-bit on this GPU |
| `microsoft/Phi-3.5-mini-instruct` | ~7.6 GB | listed; requires 4-bit |
| `google/gemma-2-2b-it` | ~5 GB | listed; strong quality at this size |
| `meta-llama/Llama-3.2-1B-Instruct` | ~2 GB | listed; gated — needs HF auth token |
| `meta-llama/Llama-3.2-3B-Instruct` | ~6 GB | listed; gated — needs HF auth token |

The two Llama entries are **gated on Hugging Face**: downloading them
requires accepting the licence and authenticating. That is an external
decision (licence acceptance + credential), so neither is a default candidate.

## What the benchmark must measure

For each candidate, on the same fixed sample set:

| Metric | How |
|---|---|
| Model loading time | wall clock around `load_model()` |
| Inference latency | wall clock around `humanize()` |
| Peak memory | `tracemalloc` for Python; `torch.cuda.max_memory_allocated()` when CUDA works |
| Semantic similarity | MiniLM cosine vs. original |
| Readability | Flesch before → after |
| Lexical diversity | TTR before → after |
| Repetition | bigram/trigram ratios before → after |
| Template phrase density | per 1000 words before → after |

Plus generated outputs written for **manual inspection**.

Selection must not be made on speed alone — a fast model that degrades
semantic similarity or drops numbers is worse than a slower one that does not.

## Getting CUDA working (recommended before benchmarking)

```bash
sudo rmmod nvidia_uvm && sudo modprobe nvidia_uvm
python3 -c "import torch; print(torch.cuda.is_available())"
```

Once CUDA is available, set `MODEL_DEVICE=auto` in `backend/.env` and raise
`HUMANIZER_QUANTIZATION` to `4bit` so larger candidates fit the 6 GB budget.

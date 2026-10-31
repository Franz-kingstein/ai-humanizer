# AI Humanizer

Research-oriented NLP application: analyse text for measurable writing-
pattern characteristics, rewrite it with a **locally runnable open-weight
model**, validate semantic preservation, and compare linguistic metrics
before and after.

**Milestone 1: local POC on Ubuntu.** Not a detector, not a bypass tool.

---

## ⚠️ Read first

This system **does not detect AI-generated text**, and is **not designed to
evade Turnitin or any detector**. The Naturalness Score is a heuristic over
linguistic features — no component estimates the probability a human wrote
the text, and no component is calibrated on labeled data.

See [`docs/limitations.md`](docs/limitations.md) before interpreting any
number this project produces.

---

## What it does

```
Input
  ↓
Original NLP analysis          ← readability, TTR, repetition, syntax, passive
  ↓
Humanization                   ← local model, 5 styles × 3 strengths
  ↓
Semantic validation            ← MiniLM cosine ≥ 0.85, bounded retry (max 2)
  ↓
Content preservation           ← numbers, percentages, dates, URLs
  ↓
Humanized NLP analysis
  ↓
Naturalness score + delta comparison + warnings
```

All metrics are computed programmatically. **No LLM calculates any metric,
and no metric value is hard-coded.**

## Stack

| | |
|---|---|
| Frontend | Next.js 16 + TypeScript + Tailwind CSS |
| Backend | Python 3.12 + FastAPI |
| NLP | spaCy (`en_core_web_sm`), textstat |
| Model | `Qwen/Qwen2.5-0.5B-Instruct` (local, CPU) |
| Semantic | `sentence-transformers/all-MiniLM-L6-v2` |

## Quick start

```bash
# Backend — port 8000
cd backend
OMP_NUM_THREADS=4 MKL_NUM_THREADS=4 ./venv/bin/uvicorn app.main:app \
  --host 127.0.0.1 --port 8000

# Frontend — port 3001 (separate terminal)
cd frontend
npm run dev
```

Open **http://localhost:3001**.

> Port 3000 is occupied on this machine, so Next uses 3001. `.env.local` and
> backend CORS both already include it.

> **Next.js 16.4.0 stops the dev server once** to show a security-upgrade
> notice. Run `npm run dev` a second time — it proceeds normally on retry.

### Setup from scratch

```bash
cd backend
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt        # torch cu124 ≈ 2.5 GB
.venv/bin/python -m spacy download en_core_web_sm

cd ../frontend && npm install
```

### Tests

```bash
cd backend && ./venv/bin/python -m pytest tests/ -q
# 45 passed
```

## API

| Method | Path | Purpose |
|---|---|---|
| GET | `/health` | liveness + device info |
| GET | `/health/model` | model load state |
| POST | `/api/analyze` | linguistic metrics only |
| POST | `/api/humanize` | rewrite only |
| POST | `/api/compare` | full pipeline |
| GET | `/api/models` | model catalogue |

Interactive docs: **http://127.0.0.1:8000/docs**

```bash
curl -s -X POST http://127.0.0.1:8000/api/compare \
  -H 'Content-Type: application/json' \
  -d '{"text":"...","style":"natural","strength":"medium"}'
```

Full reference: [`docs/api.md`](docs/api.md)

## Styles and strengths

**Styles:** `natural` · `academic` · `professional` · `casual` · `technical`
**Strengths:** `low` · `medium` · `high` (drives temperature, top-p,
repetition penalty and output budget)

## Privacy

`STORE_USER_TEXT=false` (default). Logs carry request ID, latency, model,
status and errors — **never the submitted document**. No database, no cache,
no persistence.

## Project structure

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
├── docs/                    architecture, nlp_pipeline, humanization, metrics,
│                            model_selection, evaluation, api, deployment, limitations
├── results/                 environment_report.txt
├── data/samples/            (empty)
└── scripts/                 (empty — benchmark not built)
```

## Documentation

| Doc | Covers |
|---|---|
| [architecture](docs/architecture.md) | services, singletons, request lifecycle, migration seams |
| [nlp_pipeline](docs/nlp_pipeline.md) | every metric, formulas, the readability bug |
| [humanization](docs/humanization.md) | prompt contract, styles, strengths, retry loop |
| [metrics](docs/metrics.md) | score weights, component derivations, fixes applied |
| [model_selection](docs/model_selection.md) | hardware constraints, candidates, **benchmark not built** |
| [evaluation](docs/evaluation.md) | similarity, preservation, test suite |
| [api](docs/api.md) | endpoints, schemas, errors |
| [deployment](docs/deployment.md) | run instructions, env setup, roadmap |
| [limitations](docs/limitations.md) | **what this cannot do** |

## Current status

| | |
|---|---|
| Tests | 45 passing |
| Backend | ✅ runs, model loads once at startup |
| Frontend | ✅ runs on :3001 |
| Backend RAM | 1.47 GB with thread limits |
| CUDA | ❌ unavailable — needs `sudo rmmod nvidia_uvm && sudo modprobe nvidia_uvm` |
| Benchmark | ❌ `scripts/benchmark_models.py` not built |
| Docker | ❌ not built (next milestone) |

### Known issues

- **CUDA broken** — stale `nvidia_uvm`; everything runs on CPU at 15–37 s
  per compare run.
- **No model benchmark** — model choice is a hardware-constraint decision,
  not evidence-based. No licences verified.
- **Test coverage is analysis-only** — humanization path, retry loop and all
  API routes are untested.
- **Next.js 16.4.0** has a published security advisory; not yet upgraded.

## Roadmap

```
Docker → GPU inference → vLLM/Triton → Kubernetes → College server
```

Not in this milestone: Kubernetes, Helm, Triton, vLLM, Turnitin, PostgreSQL,
Redis, Prometheus, Grafana, cloud deployment, authentication, paid APIs.

## Licence / models

Model licences have **not** been verified. Do not redistribute any model
until its licence is read. Llama 3.2 candidates are gated and need Hugging
Face authentication plus licence acceptance.

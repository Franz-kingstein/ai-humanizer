# Deployment

This milestone is a **local Ubuntu laptop POC**. There is no Docker, no
Kubernetes, no cloud deployment and no authentication — deliberately so.

## Current run instructions

### 1. Backend (port 8000)

```bash
cd ai-humanizer/backend
OMP_NUM_THREADS=4 MKL_NUM_THREADS=4 ./venv/bin/uvicorn app.main:app \
  --host 127.0.0.1 --port 8000
```

### 2. Frontend (port 3001)

```bash
cd ai-humanizer/frontend
npm run dev
```

Open **http://localhost:3001**.

> Port 3000 is occupied by another process on this machine, so Next falls back
> to 3001 automatically and logs: `⚠ Port 3000 is in use by an unknown
> process, using available port 3001 instead.` `.env.local` and the backend
> CORS list both already include 3001.

> **Next.js 16.4.0 stops the dev server once** to display a security-upgrade
> notice (`This command stopped to show the upgrade recommendation`). Run
> `npm run dev` a second time — it proceeds normally on retry. See
> `limitations.md`.

### Detached / background

```bash
cd ai-humanizer/backend
OMP_NUM_THREADS=4 MKL_NUM_THREADS=4 \
  setsid nohup ./venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000 \
  > /tmp/backend.log 2>&1 < /dev/null &

cd ai-humanizer/frontend
setsid nohup npm run dev > /tmp/frontend.log 2>&1 < /dev/null &
```

`setsid` matters: without it the harness reaps child processes when the
launching shell exits, and both servers die silently.

### Stop

```bash
pkill -f "uvi[c]orn app[.]main"
pkill -f "n[e]xt de[v]"
```

The bracket expressions prevent `pkill -f` from matching its own command line
and killing the shell running it.

## Environment setup (from scratch)

```bash
# 1. Python environment
cd backend
python3 -m venv .venv
.venv/bin/pip install --upgrade pip
.venv/bin/pip install -r requirements.txt      # torch cu124 is ~2.5 GB

# 2. spaCy model
.venv/bin/python -m spacy download en_core_web_sm

# 3. Frontend
cd ../frontend
npm install

# 4. Configure
cp .env.example backend/.env                   # then edit
```

Verify:

```bash
.venv/bin/python -m pytest tests/ -q    # expect 45 passed
curl http://127.0.0.1:8000/health       # expect 200
```

Full environment capture: `results/environment_report.txt`.

## Configuration

`backend/.env` (see `.env.example` for the annotated template). Loaded by
pydantic-settings; nothing behavioural is hard-coded.

Key values for this machine:

| Key | Value | Note |
|---|---|---|
| `MODEL_DEVICE` | `cpu` | CUDA currently broken, see below |
| `HUMANIZER_MODEL_NAME` | `Qwen/Qwen2.5-0.5B-Instruct` | fits RAM |
| `HUMANIZER_MAX_NEW_TOKENS` | `384` | lowered from 1024 for latency |
| `SEMANTIC_SIMILARITY_THRESHOLD` | `0.85` | |
| `MAX_REWRITE_ATTEMPTS` | `2` | bounded loop |
| `STORE_USER_TEXT` | `false` | privacy default |
| `SPACY_MODEL` | `en_core_web_sm` | |

`.env` contains no secrets — model names and thresholds only. `.env` is
gitignored; `.env.example` is the committed template. Hugging Face gated
models (Llama 3.2) would need an `HF_TOKEN`, but none is configured or
committed.

## Memory tuning

| Threading | Backend RSS |
|---|---|
| default | 2.46 GB |
| `OMP_NUM_THREADS=4 MKL_NUM_THREADS=4` | **1.47 GB** |

Of a 7.2 GB machine, this matters. Keep the thread limits for any
long-running session.

## CUDA repair (recommended)

`nvidia-smi` sees the RTX 3060 (6 GB, driver 575.64.03) but PyTorch reports
`CUDA unknown error` — the usual stale-`nvidia_uvm` state after suspend.
Requires root, **not yet run**:

```bash
sudo rmmod nvidia_uvm && sudo modprobe nvidia_uvm
python3 -c "import torch; print(torch.cuda.is_available())"
```

Then set `MODEL_DEVICE=auto` and consider `HUMANIZER_QUANTIZATION=4bit`.
Expected gains: latency drops sharply from CPU-tens-of-seconds to interactive.

## Health checks

```bash
curl http://127.0.0.1:8000/health         # liveness
curl http://127.0.0.1:8000/health/model   # model loaded?
curl http://127.0.0.1:8000/api/models     # model catalogue
```

Poll `/health` before sending traffic — models load during startup.

## Roadmap (not implemented)

Order per project spec, each stage only after the previous works:

```
Docker  →  GPU inference  →  vLLM/Triton  →  Kubernetes  →  College server
```

### Docker (next)

Specified but **not built** — no `backend/Dockerfile`, `frontend/Dockerfile`
or `docker-compose.yml` exists yet. Spec requires the containerised version to
still run locally.

Design constraints already in place for it:

- `Humanizer` ABC + provider factory → swap `transformers` for `vllm`/`triton`
  without pipeline changes
- `HumanizationResult` is transport-agnostic (`text`, `model_info`, `latency`)
- all config via env vars → maps directly onto compose `environment:`
- models load at startup, not per request → works with long-lived containers

### Explicitly out of scope for this milestone

Kubernetes, Helm, Triton, vLLM, Turnitin, PostgreSQL, Redis, Prometheus,
Grafana, cloud deployment, authentication, paid APIs.

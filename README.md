# AI Humanizer / NLP Naturalization System

A research-oriented system for analyzing writing patterns and naturalizing text using local LLMs.

## Overview

This system provides:
- **NLP Analysis Engine**: Comprehensive linguistic analysis (lexical diversity, sentence structure, readability, repetition, template phrases, passive voice)
- **Naturalization/Humanization**: Local LLM-based text rewriting with configurable style and strength
- **Semantic Validation**: Sentence-transformers based meaning preservation verification
- **Content Preservation**: Deterministic checks for numbers, dates, URLs, percentages
- **Naturalness Score**: Heuristic metric combining multiple linguistic features

## Architecture

```
ai-humanizer/
├── frontend/          # Next.js + TypeScript + Tailwind
├── backend/           # FastAPI + Python
│   └── app/
│       ├── api/routes/    # REST endpoints
│       ├── services/      # Business logic
│       ├── nlp/           # Core NLP analysis modules
│       ├── models/        # Pydantic schemas
│       └── utils/         # Helpers
├── data/samples/      # Test data
├── results/           # Benchmarks, outputs
├── scripts/           # Utility scripts
└── docs/              # Documentation
```

## Quick Start

### Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m spacy download en_core_web_sm
cp ../.env.example .env
uvicorn app.main:app --reload
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

## API Endpoints

- `GET /health` - Health check
- `GET /health/model` - Model status
- `POST /api/analyze` - Analyze text
- `POST /api/humanize` - Humanize text
- `POST /api/compare` - Analyze + humanize + compare
- `GET /api/models` - List available models

## Configuration

Copy `.env.example` to `.env` and adjust:

- `MODEL_PROVIDER`: `transformers` (local), `ollama`, `vllm`, `triton`
- `HUMANIZER_MODEL_NAME`: HuggingFace model ID (default: Qwen2.5-1.5B-Instruct)
- `SEMANTIC_SIMILARITY_THRESHOLD`: Minimum cosine similarity (default: 0.85)
- `MAX_REWRITE_ATTEMPTS`: Retry attempts for semantic validation (default: 2)
- `STORE_USER_TEXT`: Whether to log user text (default: false)

## Hardware Requirements

- **GPU**: NVIDIA RTX 3060 6GB VRAM (tested)
- **RAM**: 8GB+ system RAM recommended
- **Disk**: 10GB+ for models

Default model (Qwen2.5-1.5B-Instruct, 4-bit) uses ~1.5GB VRAM.

## Privacy

- All processing runs locally by default
- No external API calls unless configured
- `STORE_USER_TEXT=false` by default
- User text never logged in production

## License

MIT License - See LICENSE file

## Disclaimer

This is a research tool for studying writing patterns and naturalization techniques. The "Naturalness Score" is a heuristic metric, not a definitive measure of human vs. AI authorship. Semantic similarity validation does not guarantee perfect meaning preservation.
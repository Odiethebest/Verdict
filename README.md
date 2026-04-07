# Verdict: LLM Application Evaluation Platform

> A structured evaluation platform for LLM applications — covering custom scoring rubrics, automated LLM-as-Judge scoring, multi-variant experiment comparison, and human feedback collection for fine-tuning data export.

[![Python](https://img.shields.io/badge/Python-3.11-3776AB?logo=python)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?logo=fastapi)](https://fastapi.tiangolo.com/)
[![Vue](https://img.shields.io/badge/Vue-3.5-4FC08D?logo=vue.js)](https://vuejs.org/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-4169E1?logo=postgresql)](https://www.postgresql.org/)
[![Redis](https://img.shields.io/badge/Redis-7-DC382D?logo=redis)](https://redis.io/)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)

---

## Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Core Capabilities](#core-capabilities)
- [API Surface](#api-surface)
- [Getting Started](#getting-started)
- [Deployment](#deployment)
- [Documentation](#documentation)

---

## Overview

Evaluating LLM application quality is operationally harder than evaluating model benchmarks. Benchmark suites measure raw model capability; what teams actually need is a way to answer: *did this prompt change make my RAG pipeline better, and by how much?*

Verdict targets that problem. It lets teams define custom scoring rubrics tied to their specific domain, run experiments across multiple model and prompt variants against a shared test dataset, and collect structured human feedback to override automated scores — producing a curated export ready for fine-tuning pipelines.

**The evaluation target is application-layer output quality, not model-level benchmarks.**

### What It Handles

| Concern | Mechanism |
|---|---|
| Scoring rubrics | User-defined dimensions with weighted scorer prompts |
| Automated scoring | Rule-based (exact match, ROUGE-L) + LLM-as-Judge |
| Experiment management | Multi-variant runs over a shared dataset with lifecycle tracking |
| Concurrency | `asyncio.gather` with semaphore-bounded LLM API calls |
| Progress visibility | Server-Sent Events stream per experiment run |
| Human feedback | Per-result score override with `is_golden` flagging |
| Fine-tuning export | JSONL export of golden samples in standard chat format |

---

## Architecture

```
┌──────────────────────────────────────────────────────┐
│                    Vue 3 Frontend                     │
│   Datasets · Dimensions · Experiments · Leaderboard  │
└───────────────────────────┬──────────────────────────┘
                            │ REST + SSE
                            ▼
┌──────────────────────────────────────────────────────┐
│                   FastAPI Application                 │
│                                                       │
│  /datasets   /dimensions   /experiments   /results   │
│                            │                          │
│                    Experiment Runner                  │
│              (asyncio, Semaphore-bounded)             │
│                  ┌─────────┼──────────┐              │
│             ROUGE Scorer  Judge    Exact Match        │
└───────┬─────────────────────────────────┬────────────┘
        │                                 │
        ▼                                 ▼
  PostgreSQL                            Redis
  (experiments, variants,          (run progress,
   results, golden samples)         rate-limit state)
```

Infrastructure dependencies:

- PostgreSQL 16
- Redis 7
- OpenAI-compatible LLM API (configurable)

---

## Core Capabilities

- **Custom evaluation dimensions** with per-dimension scorer prompts and configurable weights.
- **Three-mode scoring pipeline**: exact match, ROUGE-L, and LLM-as-Judge with reasoning capture.
- **Multi-variant experiments**: bind N variants (model × system prompt combinations) to a single dataset and run them in parallel.
- **Real-time progress streaming** via SSE — frontend receives scored-count updates as the run proceeds.
- **Human feedback override** with golden sample promotion and inter-rater consistency tracking.
- **Fine-tuning export**: golden samples emitted as JSONL in OpenAI chat format.
- **Leaderboard view**: ranked comparison of variants by weighted aggregate score within an experiment.

---

## API Surface

### Datasets

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/datasets` | Create a dataset |
| `GET` | `/api/datasets` | List all datasets |
| `POST` | `/api/datasets/{id}/cases` | Bulk upload test cases |
| `GET` | `/api/datasets/{id}/cases` | List test cases |

### Evaluation Dimensions

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/dimensions` | Create a scoring dimension |
| `GET` | `/api/dimensions` | List dimensions |
| `PUT` | `/api/dimensions/{id}` | Update scorer prompt or weight |
| `DELETE` | `/api/dimensions/{id}` | Delete a dimension |

### Experiments

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/experiments` | Create an experiment |
| `GET` | `/api/experiments` | List experiments |
| `GET` | `/api/experiments/{id}` | Get experiment detail |
| `POST` | `/api/experiments/{id}/variants` | Add a variant (model + prompt) |
| `POST` | `/api/experiments/{id}/run` | Trigger an evaluation run |
| `GET` | `/api/experiments/{id}/stream` | SSE stream of run progress |
| `GET` | `/api/experiments/{id}/results` | Full per-case result table |
| `GET` | `/api/experiments/{id}/leaderboard` | Ranked variant summary |
| `GET` | `/api/experiments/{id}/export` | Export golden samples as JSONL |

### Results

| Method | Endpoint | Description |
|---|---|---|
| `PATCH` | `/api/results/{id}/feedback` | Submit human score override |

---

## Getting Started

### Prerequisites

- Python 3.11+
- Node.js 20+
- Docker and Docker Compose

### Local Setup

```bash
git clone https://github.com/Odiethebest/verdict.git
cd verdict
```

Start infrastructure:

```bash
docker compose up -d postgres redis
```

Configure environment:

```bash
cp backend/.env.example backend/.env
# set DATABASE_URL, REDIS_URL, OPENAI_API_KEY
```

Run backend:

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload
```

Run frontend:

```bash
cd frontend
npm install
npm run dev
```

Default local endpoints:

- Frontend: `http://localhost:5173`
- API: `http://localhost:8000`
- API docs: `http://localhost:8000/docs`

### Quick Smoke Test

```bash
# Create a dataset
curl -X POST http://localhost:8000/api/datasets \
  -H "Content-Type: application/json" \
  -d '{"name": "RAG Q&A v1", "description": "Customer support QA pairs"}'

# Create a scoring dimension
curl -X POST http://localhost:8000/api/dimensions \
  -H "Content-Type: application/json" \
  -d '{"name": "Accuracy", "weight": 0.6, "scorer_prompt": "Score the factual accuracy of the answer from 1-5..."}'

# Create and run an experiment
curl -X POST http://localhost:8000/api/experiments \
  -H "Content-Type: application/json" \
  -d '{"name": "Prompt A vs B", "dataset_id": 1, "dimension_ids": [1]}'
```

For a full end-to-end walkthrough, see [`docs/LOCAL_RUN.md`](docs/LOCAL_RUN.md).

---

## Deployment

Deployment assets are under `deploy/`:

- `deploy/Dockerfile.backend`
- `deploy/Dockerfile.frontend`
- `deploy/railway.toml`
- `deploy/railway.frontend.toml`

For full instructions, see [`docs/DEPLOYMENT.md`](docs/DEPLOYMENT.md).

---

## Documentation

- [Architecture](docs/ARCHITECTURE.md)
- [Local Development Runbook](docs/LOCAL_RUN.md)
- [Deployment Guide](docs/DEPLOYMENT.md)
- [Environment Variable Reference](docs/ENVIRONMENT.md)
- [Repository Structure](docs/STRUCTURE.md)


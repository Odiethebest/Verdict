# Verdict — Claude Code Context

This file provides context for Claude Code when working in this repository.

---

## What This Project Is

Verdict is an **application-layer LLM evaluation platform**. It is not a model benchmark tool (no MMLU, no HumanEval). The evaluation target is the output quality of LLM-powered applications — RAG pipelines, agents, prompt variants — measured against user-defined rubrics on a shared test dataset.

Key distinction from similar projects: evaluation dimensions are first-class entities with their own scorer prompts and weights, not hardcoded metrics.

---

## Commands

### Backend

```bash
cd backend

# Install dependencies
pip install -r requirements.txt

# Run migrations
alembic upgrade head

# Start dev server
uvicorn app.main:app --reload

# Run tests
pytest

# Lint
ruff check . && mypy app/
```

### Frontend

```bash
cd frontend

# Install
npm install

# Dev server
npm run dev

# Type check
npm run type-check

# Build
npm run build
```

### Infrastructure

```bash
# Start dependencies only
docker compose up -d postgres redis

# Full stack including app services
docker compose up
```

---

## Architecture Overview

```
backend/app/
├── api/          # FastAPI routers, one file per resource
├── core/         # Settings (pydantic-settings), DB session, Redis client
├── models/       # SQLAlchemy ORM models
├── schemas/      # Pydantic request/response schemas
└── services/
    ├── eval/     # Scoring engines: rouge.py, judge.py, exact.py
    └── runner/   # Experiment orchestration: runner.py, progress.py
```

The runner is the most important service. It:
1. Loads the experiment, variants, and test cases from PostgreSQL
2. Dispatches concurrent LLM calls using `asyncio.gather` with a `asyncio.Semaphore` (default cap: 20)
3. Pipes each raw output through the scoring pipeline (ROUGE → Judge → aggregate)
4. Pushes progress updates to Redis, which the SSE endpoint reads and streams to the client
5. Flushes all results to PostgreSQL in a single bulk insert at completion

---

## Key Design Decisions

**No Celery.** Task execution uses native `asyncio`. The workload is IO-bound (LLM API calls), and `asyncio.gather` with a semaphore handles concurrency cleanly without the operational overhead of a worker process. If throughput requirements grow to justify a proper job queue, the runner interface is designed to be swapped.

**Semaphore cap is configurable.** `EVAL_CONCURRENCY` env var controls it. Default is 20. Set lower if hitting rate limits on LLM provider.

**Judge scoring uses temperature=0.** Reproducibility matters more than response variety for scoring. Each case is scored once; consistency across runs is enforced by deterministic prompts, not multi-sample averaging (unless `JUDGE_SAMPLES > 1` is set).

**`is_golden` is write-once from the UI.** Once a human marks a result as golden, it can be unset but the original human score is preserved in `human_score`. The export query only includes cases where `is_golden = true`.

**Weighted aggregate score.** `final_score = Σ(dimension_score × dimension_weight)` normalized by total weight. Dimensions can be added or reweighted without re-running the experiment — scores are stored per-dimension and aggregated at query time.

**SSE over WebSocket.** Progress updates are unidirectional (server → client only), so SSE is simpler and sufficient. No need for the bidirectional complexity of WebSocket.

---

## Things to Avoid

- Do not introduce Celery or any external task queue without a concrete throughput reason.
- Do not change the `is_golden` flag logic without updating the export query in `services/export.py`.
- Do not call LLM APIs outside of `services/eval/judge.py` — all provider abstraction lives there.
- Do not add new API endpoints without a corresponding Pydantic schema — no raw `dict` responses.
- Do not run Alembic autogenerate on a dirty model state — always review generated migrations before committing.

---

## Environment Variables

See [`docs/ENVIRONMENT.md`](docs/ENVIRONMENT.md) for the full reference. Required at minimum:

```
DATABASE_URL
REDIS_URL
OPENAI_API_KEY     # or ANTHROPIC_API_KEY
EVAL_CONCURRENCY   # default: 20
```
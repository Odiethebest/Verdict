# Local Development Runbook

This document covers everything needed to run Verdict locally: infrastructure setup, environment configuration, database migrations, running the backend, and exercising the API end-to-end.

---

## Prerequisites

| Dependency | Minimum version | Notes |
|---|---|---|
| Python | 3.11 | Use `pyenv` if managing multiple versions |
| Docker | 24 | Required for PostgreSQL and Redis |
| Docker Compose | v2 | Bundled with Docker Desktop |
| Node.js | 20 | Frontend only |

Verify before proceeding:

```bash
python --version      # Python 3.11+
docker compose version
```

---

## 1. Start Infrastructure

The `docker-compose.yml` at the repository root defines PostgreSQL 16 and Redis 7. Start both:

```bash
docker compose up -d postgres redis
```

Confirm both containers are healthy before continuing:

```bash
docker compose ps
```

Both services expose health checks. Wait until their `STATUS` column reads `healthy`.

To stop and remove containers without deleting data:

```bash
docker compose down
```

To wipe the database volume and start fresh:

```bash
docker compose down -v
```

---

## 2. Configure the Environment

```bash
cd backend
cp .env.example .env
```

Open `.env` and set the required values:

```dotenv
# Required
DATABASE_URL=postgresql+asyncpg://postgres:password@localhost:5432/verdict
REDIS_URL=redis://localhost:6379/0
OPENAI_API_KEY=sk-...           # Your OpenAI API key

# Optional — defaults shown
EVAL_CONCURRENCY=20             # Max concurrent LLM API calls
JUDGE_MODEL=gpt-4o-mini         # Model used for LLM-as-Judge scoring
JUDGE_TEMPERATURE=0.0           # Temperature for judge calls (0 = deterministic)
JUDGE_SAMPLES=1                 # Samples per judge call; >1 averages scores
```

`DATABASE_URL` must use the `postgresql+asyncpg://` scheme. The plain `postgresql://` prefix is not accepted by the async driver.

---

## 3. Install Python Dependencies

```bash
cd backend
python -m venv .venv
source .venv/bin/activate       # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

---

## 4. Run Database Migrations

Alembic reads `DATABASE_URL` from the environment. With the virtualenv active:

```bash
cd backend
alembic upgrade head
```

This applies the initial migration (`0001_initial_schema`) that creates all tables. On a fresh database this takes under a second. Expected output:

```
INFO  [alembic.runtime.migration] Running upgrade  -> 0001, initial schema
```

To inspect the current migration state:

```bash
alembic current
```

To roll back one revision:

```bash
alembic downgrade -1
```

---

## 5. Start the Backend

```bash
cd backend
uvicorn app.main:app --reload
```

The server starts on `http://localhost:8000`. `--reload` watches for file changes and restarts automatically.

| Endpoint | URL |
|---|---|
| API root | `http://localhost:8000` |
| Swagger UI (interactive docs) | `http://localhost:8000/docs` |
| ReDoc | `http://localhost:8000/redoc` |

---

## 6. End-to-End Smoke Test

The following sequence exercises every major API surface area: creating a dataset, defining evaluation dimensions, configuring an experiment with variants, triggering a run, and reading results.

### 6.1 Create a Dataset

```bash
curl -s -X POST http://localhost:8000/api/datasets \
  -H "Content-Type: application/json" \
  -d '{"name": "RAG Q&A v1", "description": "Customer support QA pairs"}' \
  | jq .
```

Note the returned `id` — used as `DATASET_ID` in subsequent steps.

### 6.2 Upload Test Cases

```bash
DATASET_ID=1

curl -s -X POST http://localhost:8000/api/datasets/$DATASET_ID/cases \
  -H "Content-Type: application/json" \
  -d '{
    "cases": [
      {
        "input": "What is the return policy?",
        "reference_output": "Items can be returned within 30 days with a receipt."
      },
      {
        "input": "How do I contact support?",
        "reference_output": "Email support@example.com or call 1-800-555-0100."
      }
    ]
  }' \
  | jq .
```

### 6.3 Define Evaluation Dimensions

```bash
curl -s -X POST http://localhost:8000/api/dimensions \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Accuracy",
    "weight": 0.6,
    "scorer_prompt": "Score the factual accuracy of the answer compared to the reference. 1.0 = fully accurate, 0.0 = factually wrong."
  }' \
  | jq .

curl -s -X POST http://localhost:8000/api/dimensions \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Conciseness",
    "weight": 0.4,
    "scorer_prompt": "Score how concise the answer is. 1.0 = no unnecessary words, 0.0 = very verbose."
  }' \
  | jq .
```

### 6.4 Create an Experiment

```bash
curl -s -X POST http://localhost:8000/api/experiments \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Prompt A vs B",
    "dataset_id": 1,
    "dimension_ids": [1, 2]
  }' \
  | jq .
```

Note the returned experiment `id` — used as `EXPERIMENT_ID` below.

### 6.5 Add Variants

Each variant represents a model + system prompt combination to evaluate:

```bash
EXPERIMENT_ID=1

# Variant A: minimal system prompt
curl -s -X POST http://localhost:8000/api/experiments/$EXPERIMENT_ID/variants \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Prompt A",
    "model": "gpt-4o-mini",
    "system_prompt": "Answer the user question concisely and accurately.",
    "temperature": 0.0
  }' \
  | jq .

# Variant B: more detailed system prompt
curl -s -X POST http://localhost:8000/api/experiments/$EXPERIMENT_ID/variants \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Prompt B",
    "model": "gpt-4o-mini",
    "system_prompt": "You are a helpful customer support agent. Provide thorough, accurate answers.",
    "temperature": 0.0
  }' \
  | jq .
```

### 6.6 Trigger the Evaluation Run

```bash
curl -s -X POST http://localhost:8000/api/experiments/$EXPERIMENT_ID/run \
  | jq .
```

Returns `202 Accepted` immediately. The runner executes in the background, dispatching all variants concurrently.

### 6.7 Stream Progress

In a second terminal, watch live progress via SSE:

```bash
curl -N http://localhost:8000/api/experiments/$EXPERIMENT_ID/stream
```

Each event emitted while the run is active:

```
data: {"variant_id": 1, "completed": 1, "total": 2}
data: {"variant_id": 2, "completed": 2, "total": 2}
```

The stream closes once the experiment reaches `completed` or `failed`.

### 6.8 Read Results and Leaderboard

```bash
# Full per-case result table with per-dimension scores
curl -s http://localhost:8000/api/experiments/$EXPERIMENT_ID/results | jq .

# Variants ranked by weighted aggregate score
curl -s http://localhost:8000/api/experiments/$EXPERIMENT_ID/leaderboard | jq .
```

### 6.9 Submit Human Feedback

```bash
RESULT_ID=1

curl -s -X PATCH http://localhost:8000/api/results/$RESULT_ID/feedback \
  -H "Content-Type: application/json" \
  -d '{"human_score": 0.95, "is_golden": true}' \
  | jq .
```

Setting `is_golden: true` marks the result for inclusion in the fine-tuning export.

### 6.10 Export Golden Samples

```bash
curl -s http://localhost:8000/api/experiments/$EXPERIMENT_ID/export \
  -o golden_1.jsonl

cat golden_1.jsonl
```

Each line is a JSON object in OpenAI chat format:

```json
{"messages": [{"role": "user", "content": "..."}, {"role": "assistant", "content": "..."}]}
```

---

## 7. Running Tests

Tests use an in-memory SQLite database — no running PostgreSQL or Redis required.

```bash
cd backend
pytest
```

Run with verbose output:

```bash
pytest -v
```

Run a specific module:

```bash
pytest tests/services/test_scoring.py -v
pytest tests/api/test_datasets.py -v
```

---

## 8. Linting and Type Checking

```bash
cd backend

# Lint
ruff check .

# Type check
mypy app/
```

Both must pass with zero errors before committing.

---

## 9. Common Issues

**`asyncpg` connection refused on `alembic upgrade head`**

PostgreSQL is not yet healthy. Run `docker compose ps` and wait until the `postgres` container shows `healthy`, then retry.

**`OPENAI_API_KEY` validation error on startup**

`pydantic-settings` validates all required fields at import time. Ensure `backend/.env` exists and contains a valid key before starting `uvicorn`.

**`409 Conflict` when creating a dataset or dimension**

`name` is unique-constrained at the database level. Query `GET /api/datasets` or `GET /api/dimensions` first to check existing entries, or use a different name.

**Experiment stays in `running` status after the run completes**

The background runner encountered an unhandled exception. Check `uvicorn` stdout for the full traceback. The experiment will transition to `failed` once the exception propagates. Identify and fix the root cause, then reset the experiment status directly in PostgreSQL if needed:

```sql
UPDATE experiments SET status = 'pending', completed_at = NULL WHERE id = <id>;
```

Re-trigger with `POST /api/experiments/{id}/run`.

**Rate limit errors (429) during a run**

The runner retries automatically with exponential backoff (up to 3 attempts). If 429s persist, lower `EVAL_CONCURRENCY` in `.env` and restart the server.

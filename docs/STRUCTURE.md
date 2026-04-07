
# Repository Structure

```
verdict/
├── backend/
│   ├── app/
│   │   ├── api/                  # FastAPI routers
│   │   │   ├── datasets.py
│   │   │   ├── dimensions.py
│   │   │   ├── experiments.py
│   │   │   └── results.py
│   │   ├── core/
│   │   │   ├── config.py         # pydantic-settings, env var loading
│   │   │   ├── database.py       # SQLAlchemy async engine + session factory
│   │   │   └── redis.py          # Redis client singleton
│   │   ├── models/               # SQLAlchemy ORM models (one per entity)
│   │   │   ├── dataset.py
│   │   │   ├── dimension.py
│   │   │   ├── experiment.py
│   │   │   ├── variant.py
│   │   │   ├── result.py
│   │   │   └── test_case.py
│   │   ├── schemas/              # Pydantic request/response schemas
│   │   │   ├── dataset.py
│   │   │   ├── dimension.py
│   │   │   ├── experiment.py
│   │   │   └── result.py
│   │   ├── services/
│   │   │   ├── eval/
│   │   │   │   ├── rouge.py      # ROUGE-L scorer
│   │   │   │   ├── judge.py      # LLM-as-Judge, provider abstraction
│   │   │   │   ├── exact.py      # Exact match + normalized match
│   │   │   │   └── aggregate.py  # Weighted score aggregation
│   │   │   ├── runner/
│   │   │   │   ├── runner.py     # Experiment orchestration, asyncio.gather
│   │   │   │   └── progress.py   # Redis progress tracking, SSE feed
│   │   │   └── export.py         # JSONL golden sample export
│   │   └── main.py               # FastAPI app init, router registration
│   ├── alembic/
│   │   ├── versions/             # Migration files
│   │   └── env.py
│   ├── tests/
│   │   ├── api/                  # Route-level integration tests
│   │   └── services/             # Unit tests for scoring engines
│   ├── .env.example
│   ├── alembic.ini
│   └── requirements.txt
│
├── frontend/
│   ├── src/
│   │   ├── api/                  # Axios client, one module per resource
│   │   │   ├── experiments.ts
│   │   │   ├── datasets.ts
│   │   │   └── results.ts
│   │   ├── components/
│   │   │   ├── DimensionEditor.vue
│   │   │   ├── ExperimentCard.vue
│   │   │   ├── Leaderboard.vue
│   │   │   ├── ResultTable.vue
│   │   │   ├── RunProgress.vue   # SSE-connected progress bar
│   │   │   └── ScoreChart.vue    # ECharts score distribution
│   │   ├── stores/               # Pinia state
│   │   │   ├── experiments.ts
│   │   │   └── dimensions.ts
│   │   ├── views/
│   │   │   ├── DatasetsView.vue
│   │   │   ├── DimensionsView.vue
│   │   │   ├── ExperimentsView.vue
│   │   │   ├── ExperimentDetailView.vue
│   │   │   └── LeaderboardView.vue
│   │   ├── router/
│   │   │   └── index.ts
│   │   ├── App.vue
│   │   └── main.ts
│   ├── public/
│   ├── index.html
│   ├── package.json
│   └── vite.config.ts
│
├── deploy/
│   ├── Dockerfile.backend
│   ├── Dockerfile.frontend
│   ├── railway.toml              # Backend service
│   └── railway.frontend.toml    # Frontend service
│
├── docs/
│   ├── ARCHITECTURE.md
│   ├── DEPLOYMENT.md
│   ├── ENVIRONMENT.md
│   └── LOCAL_RUN.md
│
├── docker-compose.yml            # Local dev: postgres + redis only
└── README.md
```

## Notable Conventions

**Backend routing**: each resource (`datasets`, `dimensions`, `experiments`, `results`) maps to one router file under `api/`. Routers are thin — business logic lives in `services/`, not in route handlers.

**Scoring engines are stateless functions**: `rouge.py`, `judge.py`, and `exact.py` expose pure functions with no side effects. `aggregate.py` combines their outputs given a dimension weight map. This makes unit testing scoring logic straightforward without database fixtures.

**Runner is the only place that writes results**: no route handler writes `EvalResult` rows directly. All result persistence goes through `runner.py`. This keeps the write path auditable.

**Frontend stores mirror backend resources**: each Pinia store corresponds to one API module. Derived state (leaderboard rankings, score averages) is computed inside stores as getters, not in components.

**SSE connection lifecycle**: `RunProgress.vue` opens an SSE connection on mount and closes it when the experiment status transitions to `completed` or `failed`. The backend closes the stream from its side simultaneously. Both sides handle reconnection if the stream drops mid-run.
from __future__ import annotations

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.core.database import engine
from app.core.exceptions import ConflictError, ExperimentStateError, NotFoundError
from app.core.redis import close_redis


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    yield
    await engine.dispose()
    await close_redis()


app = FastAPI(title="Verdict", version="0.1.0", lifespan=lifespan)


@app.exception_handler(NotFoundError)
async def not_found_handler(request: Request, exc: NotFoundError) -> JSONResponse:
    return JSONResponse(status_code=404, content={"detail": str(exc)})


@app.exception_handler(ConflictError)
async def conflict_handler(request: Request, exc: ConflictError) -> JSONResponse:
    return JSONResponse(status_code=409, content={"detail": str(exc)})


@app.exception_handler(ExperimentStateError)
async def experiment_state_handler(request: Request, exc: ExperimentStateError) -> JSONResponse:
    return JSONResponse(status_code=409, content={"detail": str(exc)})


from app.api import datasets, dimensions, experiments, results  # noqa: E402

app.include_router(datasets.router, prefix="/api/datasets", tags=["datasets"])
app.include_router(dimensions.router, prefix="/api/dimensions", tags=["dimensions"])
app.include_router(experiments.router, prefix="/api/experiments", tags=["experiments"])
app.include_router(results.router, prefix="/api/results", tags=["results"])

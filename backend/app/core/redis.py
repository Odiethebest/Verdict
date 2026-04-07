from __future__ import annotations

from typing import Optional

from redis.asyncio import Redis

from app.core.config import settings

_redis: Optional[Redis] = None


def get_redis_client() -> Redis:
    global _redis
    if _redis is None:
        _redis = Redis.from_url(settings.REDIS_URL, decode_responses=True)
    return _redis


async def get_redis() -> Redis:
    return get_redis_client()


async def close_redis() -> None:
    global _redis
    if _redis is not None:
        await _redis.aclose()
        _redis = None

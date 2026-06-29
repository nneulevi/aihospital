"""Redis client factory with safe fallback when Redis is unavailable."""

from __future__ import annotations

from functools import lru_cache
from typing import Any

try:
    from ..config import (
        REDIS_CONNECT_TIMEOUT_SECONDS,
        REDIS_ENABLED,
        REDIS_SOCKET_TIMEOUT_SECONDS,
        REDIS_URL,
    )
except ImportError:  # pragma: no cover - direct script fallback.
    from config import (  # type: ignore
        REDIS_CONNECT_TIMEOUT_SECONDS,
        REDIS_ENABLED,
        REDIS_SOCKET_TIMEOUT_SECONDS,
        REDIS_URL,
    )

try:  # pragma: no cover - exercised through integration when redis is installed.
    import redis
except ImportError:  # pragma: no cover - optional dependency fallback.
    redis = None  # type: ignore


@lru_cache(maxsize=1)
def get_redis_client() -> Any | None:
    if not REDIS_ENABLED or redis is None:
        return None
    try:
        client = redis.Redis.from_url(
            REDIS_URL,
            socket_connect_timeout=REDIS_CONNECT_TIMEOUT_SECONDS,
            socket_timeout=REDIS_SOCKET_TIMEOUT_SECONDS,
            decode_responses=True,
        )
        client.ping()
        return client
    except Exception:
        return None


def redis_available() -> bool:
    return get_redis_client() is not None


def reset_redis_client_cache() -> None:
    get_redis_client.cache_clear()


"""Small Redis-backed fixed-window rate limiter."""

from __future__ import annotations

from .redis_client import get_redis_client


def allow_request(key: str, *, limit: int, window_seconds: int) -> bool:
    if limit <= 0 or window_seconds <= 0:
        return True
    client = get_redis_client()
    if client is None:
        return True
    try:
        count = int(client.incr(key))
        if count == 1:
            client.expire(key, window_seconds)
        return count <= limit
    except Exception:
        return True

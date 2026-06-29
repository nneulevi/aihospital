"""JSON cache operations with no-op fallback."""

from __future__ import annotations

import copy
import json
from typing import Any

from .redis_client import get_redis_client


def get_json(key: str) -> tuple[bool, dict[str, Any] | list[Any] | None]:
    client = get_redis_client()
    if client is None:
        return False, None
    try:
        raw = client.get(key)
        if raw is None:
            return False, None
        parsed = json.loads(raw)
        if isinstance(parsed, (dict, list)):
            return True, parsed
        return False, None
    except Exception:
        return False, None


def set_json(key: str, value: dict[str, Any] | list[Any], ttl_seconds: int) -> bool:
    client = get_redis_client()
    if client is None or ttl_seconds <= 0:
        return False
    try:
        client.setex(key, ttl_seconds, json.dumps(value, ensure_ascii=False, default=str))
        return True
    except Exception:
        return False


def clone_json(value: dict[str, Any] | list[Any]) -> dict[str, Any] | list[Any]:
    return copy.deepcopy(value)


"""Stable cache key helpers."""

from __future__ import annotations

import hashlib
import json
from typing import Any

try:
    from ..config import DEPLOY_ENV
except ImportError:  # pragma: no cover - direct script fallback.
    from config import DEPLOY_ENV  # type: ignore


def stable_json_dumps(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str)


def stable_hash(value: Any) -> str:
    raw = value if isinstance(value, str) else stable_json_dumps(value)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def build_key(module: str, kind: str, payload: Any, *, env: str = DEPLOY_ENV) -> str:
    safe_env = (env or "local").strip().lower()
    return f"headct:{safe_env}:{module}:{kind}:{stable_hash(payload)}"


def rag_retrieval_key(payload: dict[str, Any]) -> str:
    return build_key("rag", "retrieval", payload)


def llm_response_key(kind: str, payload: dict[str, Any]) -> str:
    return build_key("llm", kind, payload)


def model_result_key(kind: str, payload: dict[str, Any]) -> str:
    return build_key("model", kind, payload)


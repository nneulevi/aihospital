from __future__ import annotations

import json

from HeadCTOrchestrator.cache import cache_service
from HeadCTOrchestrator.cache.cache_keys import build_key, stable_hash, stable_json_dumps


class FakeRedis:
    def __init__(self) -> None:
        self.values: dict[str, str] = {}
        self.ttls: dict[str, int] = {}

    def get(self, key: str) -> str | None:
        return self.values.get(key)

    def setex(self, key: str, ttl: int, value: str) -> bool:
        self.values[key] = value
        self.ttls[key] = ttl
        return True


def test_stable_json_dumps_and_hash_are_order_independent() -> None:
    left = {"b": 2, "a": [3, 1]}
    right = {"a": [3, 1], "b": 2}
    assert stable_json_dumps(left) == stable_json_dumps(right)
    assert stable_hash(left) == stable_hash(right)
    assert build_key("rag", "retrieval", left).startswith("headct:")


def test_cache_service_json_round_trip(monkeypatch) -> None:
    fake = FakeRedis()
    monkeypatch.setattr(cache_service, "get_redis_client", lambda: fake)

    payload = {"status": "success", "items": [{"id": 1}]}
    assert cache_service.set_json("demo-key", payload, 30) is True
    hit, cached = cache_service.get_json("demo-key")

    assert hit is True
    assert cached == payload
    assert fake.ttls["demo-key"] == 30
    assert json.loads(fake.values["demo-key"]) == payload


def test_cache_service_noops_without_redis(monkeypatch) -> None:
    monkeypatch.setattr(cache_service, "get_redis_client", lambda: None)
    assert cache_service.set_json("demo-key", {"ok": True}, 30) is False
    assert cache_service.get_json("demo-key") == (False, None)

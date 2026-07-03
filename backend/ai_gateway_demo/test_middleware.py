"""
Tests for the AI-gateway cross-cutting features:
PII masking, rate limiting, semantic caching, and PII-masking wired into the gateway.
All pure / mocked, no model needed.

Run:  uv run pytest ai_gateway_demo/test_middleware.py -v
"""
import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from ai_gateway_demo import gateway
from ai_gateway_demo.middleware import RateLimiter, mask_pii
from ai_gateway_demo.cache import SemanticCache


def test_mask_pii_scrubs_email_and_phone():
    masked = mask_pii("email a.b@x.com or call +1 412 555 1234 please")
    assert "a.b@x.com" not in masked and "[EMAIL]" in masked
    assert "555" not in masked and "[PHONE]" in masked


def test_rate_limiter_blocks_after_limit_per_client():
    rl = RateLimiter(limit=2, window_s=60)
    rl.check("c1")
    rl.check("c1")
    with pytest.raises(HTTPException) as exc:
        rl.check("c1")           # 3rd call over limit
    assert exc.value.status_code == 429
    rl.check("c2")               # a different client is unaffected


def test_semantic_cache_hit_near_miss_far():
    cache = SemanticCache(threshold=0.95)
    cache.put([1.0, 0.0], {"answer": "A"})
    assert cache.get([1.0, 0.0]) == {"answer": "A"}   # identical -> hit
    assert cache.get([0.99, 0.02]) is not None        # near-duplicate -> hit
    assert cache.get([0.0, 1.0]) is None              # orthogonal -> miss


def test_gateway_masks_pii_before_forwarding(monkeypatch):
    captured = {}

    class FakeResp:
        def raise_for_status(self):
            pass

        def json(self):
            return {"model": "m", "dim": 1, "embedding": [0.1]}

    async def fake_post(url, json):
        captured["json"] = json
        return FakeResp()

    monkeypatch.setattr(gateway.client, "post", fake_post)
    with TestClient(gateway.app) as c:
        r = c.post("/embed", json={"text": "reach me at a@b.com"})

    assert r.status_code == 200
    assert "a@b.com" not in captured["json"]["text"]   # PII never left the gateway
    assert "[EMAIL]" in captured["json"]["text"]

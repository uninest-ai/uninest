"""
Tests for the gateway. Note we do NOT need the model or the microservice
running: we mock the downstream call. That is the point of the split, the
gateway's job (routing + error handling) is testable in isolation.

Run:  uv run pytest ai_gateway_demo/test_gateway.py -v
"""
import httpx
from fastapi.testclient import TestClient

from ai_gateway_demo import gateway


def test_health():
    with TestClient(gateway.app) as c:
        assert c.get("/health").json()["role"] == "gateway"


def test_embed_routes_to_service(monkeypatch):
    # fake the downstream embedding-service response
    class FakeResp:
        def raise_for_status(self):
            pass

        def json(self):
            return {"model": "all-MiniLM-L6-v2", "dim": 3, "embedding": [0.1, 0.2, 0.3]}

    async def fake_post(url, json):
        return FakeResp()

    monkeypatch.setattr(gateway.client, "post", fake_post)

    with TestClient(gateway.app) as c:
        r = c.post("/embed", json={"text": "cozy 2-bed near CMU"})

    assert r.status_code == 200
    assert r.json()["dim"] == 3


def test_embed_degrades_when_service_down(monkeypatch):
    async def fake_post(url, json):
        raise httpx.ConnectError("downstream down")

    monkeypatch.setattr(gateway.client, "post", fake_post)

    with TestClient(gateway.app) as c:
        r = c.post("/embed", json={"text": "hi"})

    assert r.status_code == 503  # graceful, not a 500 crash


def test_embed_rejects_empty_text():
    # Pydantic contract (min_length=1) rejects bad input at the gateway edge
    with TestClient(gateway.app) as c:
        r = c.post("/embed", json={"text": ""})
    assert r.status_code == 422

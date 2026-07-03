"""
Tests for the data layer (repository + ranking) and the gateway /search route.
Neither needs the model: repository/rank are pure-python; the gateway is mocked.

Run:  uv run pytest ai_gateway_demo/test_search.py -v
"""
import httpx
from fastapi.testclient import TestClient

from ai_gateway_demo import gateway
from ai_gateway_demo.repository import InMemoryVectorRepository, cosine_similarity, rank


def test_cosine_similarity_bounds():
    assert cosine_similarity([1, 0], [1, 0]) == 1.0   # identical
    assert cosine_similarity([1, 0], [0, 1]) == 0.0   # orthogonal
    assert cosine_similarity([0, 0], [1, 1]) == 0.0   # zero vector -> 0, no divide error


def test_repository_add_and_all():
    repo = InMemoryVectorRepository()
    repo.add(1, [1.0, 0.0], "sunny loft")
    repo.add(2, [0.0, 1.0], "quiet studio")
    assert repo.all() == {1: [1.0, 0.0], 2: [0.0, 1.0]}


def test_rank_orders_by_similarity_and_limits():
    embeddings = {1: [1.0, 0.0], 2: [0.9, 0.1], 3: [0.0, 1.0]}
    hits = rank([1.0, 0.0], embeddings, limit=2)
    assert [pid for pid, _ in hits] == [1, 2]  # closest first
    assert len(hits) == 2                       # limit respected


def test_gateway_search_routes_to_service(monkeypatch):
    class FakeResp:
        def raise_for_status(self):
            pass

        def json(self):
            return {"query": "loft", "hits": [{"property_id": 1, "score": 0.98}]}

    async def fake_post(url, json):
        return FakeResp()

    monkeypatch.setattr(gateway.client, "post", fake_post)
    with TestClient(gateway.app) as c:
        r = c.post("/search", json={"query": "loft", "limit": 3})
    assert r.status_code == 200
    assert r.json()["hits"][0]["property_id"] == 1


def test_gateway_search_degrades_when_service_down(monkeypatch):
    async def fake_post(url, json):
        raise httpx.ConnectError("down")

    monkeypatch.setattr(gateway.client, "post", fake_post)
    with TestClient(gateway.app) as c:
        r = c.post("/search", json={"query": "x"})
    assert r.status_code == 503

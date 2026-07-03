"""
Semantic caching: return a cached response when a NEW query is semantically
close (cosine >= threshold) to a previous one. AI gateways use this to skip
recomputing near-duplicate LLM/search calls (huge cost + latency win).

Reuses the same cosine helper as the data layer, so the algorithm is trivially
unit-testable with plain vectors (no model needed).

Wire-live upgrade path (kept out of the demo route to avoid an extra hop in
tests): at the gateway, embed the incoming query once (one call to the embedding
service), `get(query_vec)`; on miss, forward the real request and `put` the result.
"""
from .repository import cosine_similarity


class SemanticCache:
    def __init__(self, threshold: float = 0.95):
        self.threshold = threshold
        self._entries: list[tuple[list[float], dict]] = []

    def get(self, query_vec: list[float]) -> dict | None:
        best, best_score = None, -1.0
        for vec, resp in self._entries:
            score = cosine_similarity(query_vec, vec)
            if score > best_score:
                best, best_score = resp, score
        return best if best_score >= self.threshold else None

    def put(self, query_vec: list[float], response: dict) -> None:
        self._entries.append((query_vec, response))

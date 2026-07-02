"""
Data layer: the repository pattern.

The service must NOT know whether embeddings live in memory, Postgres, or Qdrant.
It depends on the `VectorRepository` INTERFACE, so you can swap the implementation
(in-memory here, Postgres/Qdrant in prod) without touching service logic.

In UniNest's real app the SQL currently sits INSIDE `app/services/embedding_service.py`
(`save_embedding` / `get_all_embeddings`). That coupling is exactly what a repository
removes: same idea, apply it there next.
"""
import math
from abc import ABC, abstractmethod


class VectorRepository(ABC):
    """Interface for storing + retrieving property embeddings."""

    @abstractmethod
    def add(self, property_id: int, vector: list[float], text: str) -> None: ...

    @abstractmethod
    def all(self) -> dict[int, list[float]]:
        """Return {property_id: vector} for every stored embedding."""
        ...


class InMemoryVectorRepository(VectorRepository):
    """Dict-backed repo. Great for tests/demo; swap for Postgres/Qdrant in prod."""

    def __init__(self) -> None:
        self._store: dict[int, dict] = {}

    def add(self, property_id: int, vector: list[float], text: str) -> None:
        self._store[property_id] = {"vector": vector, "text": text}

    def all(self) -> dict[int, list[float]]:
        return {pid: row["vector"] for pid, row in self._store.items()}


# --- pure-python ranking helpers (no numpy needed, so this stays test-friendly) ---
def cosine_similarity(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    return dot / (na * nb) if na and nb else 0.0


def rank(query_vec: list[float], embeddings: dict[int, list[float]], limit: int) -> list[tuple[int, float]]:
    scored = [(pid, cosine_similarity(query_vec, vec)) for pid, vec in embeddings.items()]
    scored.sort(key=lambda pair: pair[1], reverse=True)
    return scored[:limit]

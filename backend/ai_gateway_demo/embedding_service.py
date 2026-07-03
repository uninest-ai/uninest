"""
Embedding microservice: a STANDALONE FastAPI app that OWNS the model + a repository.

A standalone embedding / retrieval microservice.
- the heavy SentenceTransformer model lives HERE, loaded once per process;
- DB access is behind a `VectorRepository` (data layer), so the service logic
  (encode + rank) does not know or care where vectors are stored.

Run:  uv run uvicorn ai_gateway_demo.embedding_service:app --port 8001
"""
from fastapi import FastAPI
from sentence_transformers import SentenceTransformer  # heavy dep, isolated to THIS service

from .repository import InMemoryVectorRepository, rank
from .schemas import (
    EmbedRequest,
    EmbedResponse,
    IndexRequest,
    SearchRequest,
    SearchResponse,
    SearchHit,
)

MODEL_NAME = "all-MiniLM-L6-v2"

app = FastAPI(title="embedding-service")

_model: SentenceTransformer | None = None
repo = InMemoryVectorRepository()  # swap for a Postgres/Qdrant repo in prod, no other change


def get_model() -> SentenceTransformer:
    """Lazy-load the model once; reused across requests in this process."""
    global _model
    if _model is None:
        _model = SentenceTransformer(MODEL_NAME)
    return _model


def _encode(text: str) -> list[float]:
    return get_model().encode(text, normalize_embeddings=True).tolist()


@app.get("/health")
def health():
    return {"status": "ok", "service": "embedding", "model": MODEL_NAME, "indexed": len(repo.all())}


# `def` (sync), NOT `async def`: model inference is compute-bound, so FastAPI runs
# it in the thread pool and it does not block the event loop.
@app.post("/embed", response_model=EmbedResponse)
def embed(req: EmbedRequest) -> EmbedResponse:
    vector = _encode(req.text)
    return EmbedResponse(model=MODEL_NAME, dim=len(vector), embedding=vector)


@app.post("/index")
def index(req: IndexRequest):
    """Encode a property's text and store it via the repository."""
    repo.add(req.property_id, _encode(req.text), req.text)
    return {"indexed": req.property_id}


@app.post("/search", response_model=SearchResponse)
def search(req: SearchRequest) -> SearchResponse:
    """Encode the query, then rank stored embeddings by cosine similarity."""
    query_vec = _encode(req.query)
    hits = [
        SearchHit(property_id=pid, score=round(score, 4))
        for pid, score in rank(query_vec, repo.all(), req.limit)
    ]
    return SearchResponse(query=req.query, hits=hits)

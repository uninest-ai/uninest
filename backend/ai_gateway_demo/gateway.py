"""
AI Gateway: a lightweight FastAPI server that routes requests to microservices
AND hosts the cross-cutting AI-gateway concerns (the LiteLLM / Kong AI Proxy job):
routing + fallback, rate limiting, PII masking, observability/chargeback.

The gateway holds NO model and does NO heavy compute. That is the whole point:
one place for all the cross-cutting stuff, so the microservices stay focused.

Run:  uv run uvicorn ai_gateway_demo.gateway:app --port 8000
"""
import logging
import os
import time
from contextlib import asynccontextmanager

import httpx
from fastapi import Depends, FastAPI, HTTPException, Request

from .middleware import RateLimiter, mask_pii
from .schemas import EmbedRequest, EmbedResponse, SearchRequest, SearchResponse

logger = logging.getLogger("gateway")

# routing config: primary + optional fallback (model routing & fallback)
EMBEDDING_URL = os.getenv("EMBEDDING_SERVICE_URL", "http://localhost:8001")
FALLBACK_URL = os.getenv("EMBEDDING_SERVICE_FALLBACK_URL")  # e.g. a backup replica

client = httpx.AsyncClient(timeout=30.0)
limiter = RateLimiter(limit=100, window_s=60)  # per client-id / IP


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    await client.aclose()


app = FastAPI(title="ai-gateway", lifespan=lifespan)


# ---------- Observability & Chargeback: time + log every request ----------
@app.middleware("http")
async def observe(request: Request, call_next):
    start = time.perf_counter()
    response = await call_next(request)
    elapsed_ms = (time.perf_counter() - start) * 1000
    logger.info("%s %s -> %s %.1fms", request.method, request.url.path, response.status_code, elapsed_ms)
    # chargeback hook: attribute elapsed_ms / token counts to request.headers["x-client-id"] here
    return response


# ---------- Rate limiting: dependency that 429s an over-quota client ----------
def rate_limit(request: Request) -> None:
    key = request.headers.get("x-client-id") or (request.client.host if request.client else "anon")
    limiter.check(key)


# ---------- Routing + fallback: try primary, then fallback, else 503 ----------
async def _forward(path: str, payload: dict) -> dict:
    urls = [EMBEDDING_URL] + ([FALLBACK_URL] if FALLBACK_URL else [])
    last_error: Exception | None = None
    for url in urls:
        try:
            resp = await client.post(f"{url}{path}", json=payload)
            resp.raise_for_status()
            return resp.json()
        except httpx.HTTPError as exc:
            last_error = exc  # try the next url (fallback)
    raise HTTPException(status_code=503, detail=f"embedding-service unavailable: {last_error}")


@app.get("/health")
async def health():
    return {"status": "ok", "role": "gateway"}


# `async def`: gateway work is I/O-bound (network), so it belongs on the event loop.
@app.post("/embed", response_model=EmbedResponse, dependencies=[Depends(rate_limit)])
async def route_embed(req: EmbedRequest) -> EmbedResponse:
    payload = {"text": mask_pii(req.text)}  # never send raw PII downstream
    return EmbedResponse(**await _forward("/embed", payload))


@app.post("/search", response_model=SearchResponse, dependencies=[Depends(rate_limit)])
async def route_search(req: SearchRequest) -> SearchResponse:
    return SearchResponse(**await _forward("/search", req.model_dump()))

# ai_gateway_demo — a production-style AI Gateway

A minimal, self-contained demo of a common production pattern: **a lightweight FastAPI
gateway that routes requests to standalone FastAPI microservices**, and hosts the
cross-cutting AI concerns (rate limiting, PII masking, observability, caching,
routing/fallback) in one place. Built on top of UniNest's embedding capability.

## The pattern
```
client ─POST /embed─►  gateway (:8000)  ─async httpx─►  embedding-service (:8001)
                       holds NO model                   OWNS the model (loaded once)
```

## Files
- `gateway.py` — lightweight gateway: validates, routes async, degrades gracefully. Hosts the cross-cutting middleware.
- `embedding_service.py` — standalone service that owns the SentenceTransformer model; `/embed`, `/index`, `/search`.
- `repository.py` — the data layer (a `VectorRepository` interface + in-memory impl + cosine/rank). Swap for Postgres/Qdrant without touching the service.
- `middleware.py` — rate limiting + PII masking.
- `cache.py` — a semantic cache (cosine-based).
- `schemas.py` — shared Pydantic contracts.
- `tools.py` + `agent.py` — a tool-using "Housing Concierge" agent: orchestration loop + a swappable LLM planner (`Planner` interface, `LLMPlanner` default) + a tool-allowlist guardrail.
- `test_*.py` — pytest; the downstream service and the LLM are mocked, so no model or API key is needed.

## Why it is built this way (the lessons)
1. **Model lives in the service, not the gateway.** N gateway workers would each copy the model into memory → OOM. One shared service = one copy; the gateway stays cheap to scale.
2. **Gateway handler is `async def`, the embed handler is `def`.** Gateway work is I/O-bound (network) → event loop → high concurrency. Model inference is compute-bound → sync `def` → thread pool. The #1 mistake is a blocking call inside `async def`.
3. **Services are independently deployable + testable.** The gateway's routing/error handling is tested without the model even running (mocked downstream).
4. **Cross-cutting concerns live in the gateway,** not duplicated per service: rate limiting, PII masking, observability, routing/fallback, caching.
5. **Data access is behind a repository,** so the storage backend is swappable.
6. **The agent's orchestration loop is plain code; the LLM is swappable** behind the `Planner` interface; guardrails (the tool allowlist) are enforced in code, not the prompt.

## Run it
```bash
uv add fastapi uvicorn httpx pytest
# the embedding-service live run also needs: uv add sentence-transformers

# microservice (first run downloads the ~90MB model):
uv run uvicorn ai_gateway_demo.embedding_service:app --port 8001
# gateway:
uv run uvicorn ai_gateway_demo.gateway:app --port 8000

# try it:
curl -X POST localhost:8000/embed -H "content-type: application/json" -d '{"text":"cozy 2-bed near campus"}'

# checks (no model / API key needed):
uv run pytest ai_gateway_demo -v
uv run ruff check ai_gateway_demo
uv run mypy ai_gateway_demo
```

## What's included
- Gateway → microservice split, with a repository data layer and `/search`.
- AI-gateway middleware: routing + fallback, rate limiting, PII masking, observability, semantic cache.
- A tool-using, location-first Concierge agent.
- CI (`.github/workflows/ci.yml`): ruff + mypy + pytest on PR.
- `docker-compose.yml`: gateway + embedding-service on one network.

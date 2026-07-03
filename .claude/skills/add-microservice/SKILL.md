---
name: add-microservice
description: >-
  Scaffold a new FastAPI microservice behind the AI Gateway in this repo
  (backend/ai_gateway_demo). Use when asked to add a new service, expose a
  capability "as its own service like embedding-service", or put heavy/isolated
  work behind the gateway. Walks schema -> service -> gateway route -> tests ->
  docker-compose, and enforces the repo's async / layering / secrets rules.
  NOT for adding a plain endpoint to the monolith backend/app (that stays a
  normal route).
---

# add-microservice

Add a new microservice that lives **behind the AI Gateway**, copying the existing
`embedding-service` pattern. Read `backend/ai_gateway_demo/README.md` and the root
`AGENTS.md` first, and cite the specific rule you rely on in the PR.

## The pattern you are copying
- `embedding_service.py` = a **standalone FastAPI app** that OWNS its heavy dependency
  (the model) + a repository, and exposes `/health` plus its endpoints.
- `gateway.py` = routes to it over `httpx` and adds the cross-cutting concerns
  (rate-limit, PII mask, observability, routing/fallback).
- The service is **independently deployable and testable** (gateway tests mock it).

## Steps — do them in order, keep tests green at each step

**0 · Name it.** `<svc>` = short lowercase (`rerank`, `geocode`). Pick a free port
(embedding uses 8001). Service module = `ai_gateway_demo/<svc>_service.py`.

**1 · Contract first — `schemas.py`.** Add the Pydantic request/response models.
These ARE the cross-layer contract (AGENTS.md §2): both the gateway and the service
import them, so neither side can drift.
```python
class RerankRequest(BaseModel): ...
class RerankResponse(BaseModel): ...
```

**2 · The service — `ai_gateway_demo/<svc>_service.py`.** Start from
`service_template.py` in this skill folder. Rules:
- Heavy deps (models, big libs) load **HERE**, once per process, lazily (a `get_model()`
  global) — **never in the gateway** (AGENTS.md §4; README lesson 1: N gateway workers
  would each copy the model into memory -> OOM).
- **Compute-bound** handler -> plain `def` (FastAPI runs it in the thread pool).
  **I/O-bound** -> `async def` + `await`. NEVER block inside `async def` (AGENTS.md §3).
- If it stores anything, put data access behind a repository (AGENTS.md §2).
- Always expose `GET /health`.

**3 · Gateway route — `gateway.py`.**
- Add its URL: `RERANK_URL = os.getenv("RERANK_SERVICE_URL", "http://localhost:8002")`.
- Add `async def route_rerank(req: RerankRequest) -> RerankResponse` with
  `dependencies=[Depends(rate_limit)]`.
- If the request carries user text, mask before forwarding (`mask_pii(...)`).
- Forward via `_forward` — generalize it to take a base URL if the target is not the
  embedding service.
- `async def` because gateway work is I/O-bound.

**4 · Tests — `test_<svc>.py`** (AGENTS.md §6, red -> green):
- Service logic: unit-test the pure function; stub the heavy dep so no model/network runs.
- Gateway route: monkeypatch `_forward`, assert routing + PII is masked + over-quota -> 429.
  No real service running.

**5 · Docker — `docker-compose.yml`.** Add a block: build from
`backend/ai_gateway_demo/Dockerfile`,
`command: uv run uvicorn ai_gateway_demo.<svc>_service:app --host 0.0.0.0 --port 8002`,
on the default network. Give `ai-gateway` the env
`RERANK_SERVICE_URL=http://<svc>-service:8002` so it reaches the service by compose name.

**6 · Gates — must all pass:**
```
cd backend
uv run ruff check ai_gateway_demo
uv run mypy ai_gateway_demo
uv run pytest ai_gateway_demo -v
```

## Guardrails (do not violate)
- No heavy model in the gateway. No blocking call inside `async def`. No hardcoded
  secrets — env only (AGENTS.md do/don't).
- One service per PR (one concern, reviewable).

## Definition of done
schema + service + gateway route + tests + compose entry, `ruff`/`mypy`/`pytest` all green,
`README.md` file list + `AGENTS.md` layout line updated. PR cites the AGENTS.md rule(s) followed.

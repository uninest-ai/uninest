# HIGHARC_UPGRADE.md — continuation brief (for a fresh coding agent, e.g. Codex)

## Context
The owner is prepping for a Higharc internship (starts 2026-07-06). Role = research→production
ML engineering + agentic dev infra. The hiring manager said the day-1 task is "review + improve
our AI Gateway" (a lightweight FastAPI server that routes requests to FastAPI microservices). To
rehearse, we are upgrading THIS project (UniNest backend, a FastAPI app) into Higharc's patterns.
The owner is LEARNING, so **explain the "why" at each step**, keep changes small and reviewable,
and keep the app working at every step.

## Goal
Refactor `backend/` to mirror Higharc's stack: **AI Gateway → FastAPI microservices**, uv tooling,
layered (`api/services/data/schemas`) with a **repository** layer, async-safe I/O, pytest, GitHub
Actions CI, docker-compose on one network.

## Environment (Windows)
- Python 3.13 (`C:\Python313`).
- `uv` is installed --user at `%APPDATA%\Python\Python313\Scripts\uv.exe` and is NOT on PATH by
  default. Add that dir to PATH, or reinstall via `powershell -c "irm https://astral.sh/uv/install.ps1 | iex"`.
- uv project already initialized: `backend/pyproject.toml` (requires-python >=3.13) + `.venv/`.
- Run app: `uv run uvicorn app.main:app --reload`. Tests: `uv run pytest`.

## Done so far
1. uv initialized. `requirements.txt` stale pins fixed for Python 3.13: `Pillow>=11.0.0`,
   `numpy>=2.1.0`. (A full `uv add -r requirements.txt` is still pending because
   `sentence-transformers==2.7.0` pulls a heavy torch; do it when ready and bump any further stale
   pins the same way — the fix pattern is "old pin has no cp313 wheel → bump to a version that does".)
2. **Gateway pattern extracted** into `backend/ai_gateway_demo/` (self-contained; does NOT touch the
   running app). Files:
   - `gateway.py` — lightweight FastAPI; `async` httpx routing to the microservice; graceful 503 on
     downstream failure; holds no model.
   - `embedding_service.py` — standalone FastAPI microservice that OWNS the SentenceTransformer model
     (loaded once); `/embed` is a **sync `def`** on purpose (compute-bound → FastAPI thread pool).
   - `schemas.py` — shared Pydantic contracts.
   - `test_gateway.py` — mocks the downstream; tests routing + graceful degradation + input validation.
   - `README.md` — the pattern, the 3 lessons, and a mapping to Higharc.
   - Verify: `uv add fastapi uvicorn httpx pytest && uv run pytest ai_gateway_demo/test_gateway.py -v`
     (extracted from the real `app/services/embedding_service.py`).

## Remaining steps (do IN ORDER, small diffs, explain the why)
**Step 3 — repository/data layer + `/search`.** The DB embedding ops (`save_embedding`,
`get_all_embeddings`, the raw `text(...)` SQL) currently live inside `app/services/embedding_service.py`.
Extract them into a `data/` repository class (repository pattern): the service does logic, the
repository does DB access. Then add a `/search` endpoint (query → embed → vector search → ranked
`property_id`s) to the microservice, plus a matching gateway route and Pydantic `SearchRequest` /
`SearchResponse`.

**Step 4 — async audit.** Check the external-API code (`app/services/rapidapi_fetcher.py`,
`realtor16_fetcher.py`, `multi_source_fetcher.py`, `image_analysis.py`) for synchronous `requests` /
blocking calls used inside `async def` handlers. Fix by switching those to `httpx.AsyncClient`
(async), or make the handler plain `def` so FastAPI thread-pools it. The cardinal sin to hunt: a
blocking call inside `async def` that stalls the event loop.

**Step 5 — pytest + CI.** Expand tests for the new gateway/repository. Add `.github/workflows/ci.yml`:
on PR, `uv sync`, then `uv run pytest`, plus lint (`ruff`) and type-check (`mypy`). This is the
"sweeping changes across GitHub Actions + tox/pytest CI/CD" task.

**Step 6 — docker-compose.** Update `docker-compose.yml` to run the gateway and the embedding-service
as two containers on one bridge network (mirrors Higharc's `higharc-network`); update
`docker/backend/Dockerfile` to install deps via uv (`uv sync --frozen`).

## Conventions
- Layered: `api/` (routes: validate + call service) → `services/` (business logic) → `data/`
  (repository, DB) + `schemas/` (Pydantic contracts, cross-layer).
- `async def` for I/O-bound handlers; plain `def` for compute-bound (FastAPI thread-pools it).
  Never run a blocking call inside `async def`.
- Heavy/stateful things (a model) live in their own microservice, not the gateway.
- Small reviewable diffs; keep the app runnable at each step; branch per change.

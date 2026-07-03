# AGENTS.md — UniNest

Guidance for coding agents (Claude Code, Codex, etc.) working in this repo.
Follow these conventions so your changes fit the codebase and don't disrupt it.
Both the code generator and the reviewer should cite the specific rule they rely on.

## What this is
UniNest: a personalized housing-recommendation app.
- `backend/` — FastAPI (Python 3.13) + SQLAlchemy/Postgres + AI features (embeddings, hybrid search, Gemini image analysis).
- `frontend/` — React (Vite).
- Containerized via `docker-compose.yml`.

## Layout
- `backend/app/` — the main API, layered:
  `routes/` (API) -> `services/` (business logic) -> `models.py` / `database.py` (data) + `schemas.py` (Pydantic contracts).
- `backend/ai_gateway_demo/` — a production-style **AI Gateway** example: a lightweight gateway routing to a standalone embedding microservice, with a repository data layer and gateway middleware (routing+fallback, rate-limit, PII masking, observability, semantic cache). Read its `README.md` first.
- `backend/tests/` and `backend/ai_gateway_demo/test_*.py` — pytest.
- `.github/workflows/ci.yml` — CI: uv + ruff + mypy + pytest.

## Conventions (follow these)
1. **Python 3.13, managed with uv.** Add deps with `uv add`; run with `uv run` (`uv run pytest`, `uv run uvicorn app.main:app`). Do not use pip/`requirements.txt` for new work (uv migration in progress).
2. **Keep the layers clean.** Routes stay thin (validate input, call a service, return). Business logic goes in `services/`. Database access goes behind a repository. Pydantic `schemas` are the cross-layer contract. Do NOT put SQL in routes, or business logic in routes.
3. **Async vs sync.** Use `async def` + `await` for I/O-bound handlers (network / async DB). Use plain `def` for compute-bound work (model inference) so FastAPI runs it in the thread pool. NEVER run a blocking call inside `async def` — it freezes the event loop and stalls every request.
4. **Cross-cutting concerns live in the gateway,** not duplicated in each service: rate limiting, PII masking, auth, observability, routing/fallback.
5. **Lint + type clean.** Code must pass `uv run ruff check` and `uv run mypy` (config in `backend/pyproject.toml`).
6. **Tests.** Add pytest tests for new behavior; mock external services (see `ai_gateway_demo/test_*.py`). Prefer red -> green (write the failing test first).

## How to run / verify
```
cd backend
uv sync
uv run ruff check ai_gateway_demo
uv run mypy ai_gateway_demo
uv run pytest ai_gateway_demo -v          # fast: no model needed
uv run uvicorn app.main:app --reload      # the main API (needs DB + full deps)
```

## Do / don't
- DO keep changes small and reviewable (one concern per PR); branch per change.
- DO keep the app runnable and the tests green at every step.
- DON'T commit secrets. Config and keys come from env vars / `.env`, never hardcoded.
- DON'T load heavy models in the gateway; models live in their own microservice.

## Known issues (safe to fix, cite this section)
- `docker/backend/Dockerfile` is still Python 3.9, incompatible with the 3.10+ `X | None` syntax used in newer code. Migrate it to 3.13 + uv.
- The `requirements.txt` -> uv migration is partial (torch / sentence-transformers pending).
- A DB credential is hardcoded in `docker-compose.yml`; move it to env and rotate it.

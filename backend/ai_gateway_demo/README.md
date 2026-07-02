# ai_gateway_demo — Higharc-pattern AI Gateway (extracted from UniNest's embedding service)

A minimal, self-contained demo of the pattern Higharc uses: **a lightweight FastAPI
gateway that routes requests to standalone FastAPI microservices.** Extracted from
UniNest's `app/services/embedding_service.py`.

## The pattern
```
client ──POST /embed──►  gateway (:8000)  ──async httpx──►  embedding-service (:8001)
                         holds NO model                     OWNS the model (loaded once)
```
- **gateway.py** — lightweight, no model, no heavy compute. Validates, routes over the
  network (async), degrades gracefully if the downstream is down. This is where
  logging / rate-limit / auth middleware would live.
- **embedding_service.py** — a standalone service that owns the `SentenceTransformer`
  model. Loaded once per process, reused across requests.
- **schemas.py** — Pydantic contracts shared by both sides (the type contract).
- **test_gateway.py** — tests the gateway in isolation by mocking the downstream.

## Why it is built this way (the 3 lessons)
1. **Model lives in the service, not the gateway.** If you loaded the model in the
   gateway and ran N workers, each worker copies the model into memory → OOM. One
   shared service = one copy. The gateway stays cheap to scale.
2. **Gateway handler is `async def`, embed handler is `def`.** Gateway work is
   I/O-bound (network), so async on the event loop = high concurrency. Model inference
   is compute-bound, so a sync `def` handler is handed to the thread pool and does not
   block the event loop. The #1 mistake is putting a blocking call inside `async def`.
3. **The two services are independently deployable + testable.** The gateway's routing
   and error handling are tested without the model even running (see the mocked tests).

## Maps to Higharc
| here | Higharc |
|---|---|
| gateway.py | their AI Gateway (lightweight FastAPI router) |
| embedding-service | their `Embeddings` microservice (SBM encoder-only pathway) |
| async httpx routing | web clients → AI Gateway → microservices over `higharc-network` |
| schemas.py | their `schemas/` Pydantic contract layer |

## Run it
```bash
# extra deps this demo needs (httpx for the gateway):
uv add httpx
# (fastapi, uvicorn, sentence-transformers, numpy, pytest are already in the project)

# terminal 1 — the microservice (first run downloads the ~90MB model):
uv run uvicorn ai_gateway_demo.embedding_service:app --port 8001

# terminal 2 — the gateway:
uv run uvicorn ai_gateway_demo.gateway:app --port 8000

# try it:
curl -X POST localhost:8000/embed -H "content-type: application/json" -d '{"text":"cozy 2-bed near CMU"}'

# tests (no model / no running service needed):
uv run pytest ai_gateway_demo/test_gateway.py -v
```

## Next steps (the rest of the upgrade)
- Add a `/search` endpoint that adds a **repository/data layer** for the DB embeddings
  (the `save_embedding` / `get_all_embeddings` SQL currently sits inside the service).
- Add a **GitHub Actions** workflow running `uv run pytest` + lint + type-check on PR.
- Update `docker-compose.yml` to run gateway + service as two containers on one network
  (mirrors `higharc-network`).

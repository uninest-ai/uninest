"""
<svc>-service: a STANDALONE FastAPI app that lives behind the AI Gateway.

Copy this file to `ai_gateway_demo/<svc>_service.py`, rename the schema classes,
and fill in the TODOs. Define the request/response models in `schemas.py` first.

Run:  uv run uvicorn ai_gateway_demo.<svc>_service:app --port 8002
"""
from fastapi import FastAPI

# Define these in schemas.py FIRST (the shared cross-layer contract).
from .schemas import SvcRequest, SvcResponse  # noqa: F401  # TODO: rename to your service

app = FastAPI(title="<svc>-service")


# --- Heavy deps load HERE, once per process, lazily. NEVER in the gateway. ---
# _model = None
# def get_model():
#     global _model
#     if _model is None:
#         _model = load_expensive_thing()  # loaded once, reused across requests
#     return _model


@app.get("/health")
def health():
    return {"status": "ok", "service": "<svc>"}


# compute-bound  -> plain `def`  (FastAPI runs it in the thread pool)
# I/O-bound      -> `async def` + await  (belongs on the event loop)
# Pick ONE; never block inside an `async def`.
@app.post("/<svc>", response_model=SvcResponse)
def run(req: SvcRequest) -> SvcResponse:
    raise NotImplementedError("TODO: the actual work")  # noqa: F821

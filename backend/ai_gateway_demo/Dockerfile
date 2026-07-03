# Minimal uv-based image for the demo gateway + embedding-service (Python 3.13).
#
# Note: the repo's docker/backend/Dockerfile is still on Python 3.9, which is
# incompatible with this code (it uses 3.10+ `X | None` unions). Migrating that
# one to 3.13 + uv is the same "sweeping tooling change" as the CI migration.
FROM python:3.13-slim

# bring in the uv binary from its official image
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

# install locked deps (build context is the repo root, so paths start with backend/)
COPY backend/pyproject.toml backend/uv.lock ./
RUN uv sync --frozen --no-dev

# The embedding-service additionally needs the model libs. Kept out of the base
# install to stay light + fast; uncomment to run embedding-service live (pulls torch):
# RUN uv add sentence-transformers

COPY backend/ai_gateway_demo ./ai_gateway_demo

# the actual command (which app to run) is provided per-service by docker-compose

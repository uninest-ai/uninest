"""
Micro-benchmark for the gateway's async decision (AGENTS.md §3 / README lesson 2).

Fires N concurrent requests at three FastAPI handlers, each simulating a 50ms
downstream call, and measures how long all N take together:

  async_await   async def + await asyncio.sleep  -> non-blocking, runs concurrently
  sync_thread   def       + time.sleep           -> FastAPI threadpool (concurrent up to pool size)
  async_block   async def + time.sleep           -> BLOCKS the event loop, serializes (the bug)

No model, no network, no ports: the ASGI app is called in-process via httpx.ASGITransport.
Run:  uv run python -m ai_gateway_demo.bench_concurrency
"""
from __future__ import annotations

import asyncio
import time

import httpx
from fastapi import FastAPI

DOWNSTREAM_MS = 50
N = 50

app = FastAPI()


@app.get("/async_await")
async def async_await() -> dict:
    await asyncio.sleep(DOWNSTREAM_MS / 1000)  # non-blocking: yields the loop
    return {"ok": True}


@app.get("/sync_thread")
def sync_thread() -> dict:
    time.sleep(DOWNSTREAM_MS / 1000)  # sync def -> FastAPI runs it in the threadpool
    return {"ok": True}


@app.get("/async_block")
async def async_block() -> dict:
    time.sleep(DOWNSTREAM_MS / 1000)  # blocking call inside async def -> freezes the loop
    return {"ok": True}


async def hammer(path: str) -> dict:
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://bench") as client:

        async def one() -> float:
            t = time.perf_counter()
            resp = await client.get(path)
            resp.raise_for_status()
            return (time.perf_counter() - t) * 1000

        start = time.perf_counter()
        latencies = sorted(await asyncio.gather(*[one() for _ in range(N)]))
        wall_ms = (time.perf_counter() - start) * 1000

    return {
        "wall_ms": wall_ms,
        "req_s": N / (wall_ms / 1000),
        "p95_ms": latencies[int(0.95 * N) - 1],
    }


async def main() -> None:
    print(f"N={N} concurrent requests, each a {DOWNSTREAM_MS}ms simulated downstream call\n")
    print(f"{'handler':<14}{'total (ms)':>12}{'req/s':>10}{'p95 (ms)':>12}")
    print("-" * 48)
    for path in ("/async_await", "/sync_thread", "/async_block"):
        r = await hammer(path)
        print(f"{path[1:]:<14}{r['wall_ms']:>12.0f}{r['req_s']:>10.0f}{r['p95_ms']:>12.0f}")


if __name__ == "__main__":
    asyncio.run(main())

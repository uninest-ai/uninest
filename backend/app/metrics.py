# app/metrics.py
"""
Simple metrics middleware for tracking API performance.

Tracks:
- Request latency (p50, p95, p99 percentiles)
- Queries per second (QPS) over 1 minute window
"""

import time
from collections import deque
from fastapi import FastAPI, Request


# Global storage for metrics
lat_hist = deque(maxlen=1000)  # Last 1000 request latencies
req_1m = deque()  # Request timestamps in last 1 minute


def attach_metrics(app: FastAPI):
    """
    Attach metrics middleware and endpoint to FastAPI app.

    Usage:
        from app.metrics import attach_metrics
        app = FastAPI()
        attach_metrics(app)
    """

    @app.middleware("http")
    async def timing_middleware(request: Request, call_next):
        """Middleware to track request latency and count."""
        # Start timer
        t0 = time.perf_counter()

        # Process request
        response = await call_next(request)

        # Calculate latency in milliseconds
        dt = (time.perf_counter() - t0) * 1000
        lat_hist.append(dt)

        # Track request timestamp
        now = time.time()
        req_1m.append(now)

        # Remove requests older than 60 seconds
        while req_1m and now - req_1m[0] > 60:
            req_1m.popleft()

        return response

    @app.get("/metrics", tags=["Monitoring"])
    def get_metrics():
        """
        Get API performance metrics.

        Returns:
            - latency_ms: Request latency percentiles (p50, p95, p99) in milliseconds
            - qps_1m: Queries per second over the last 1 minute

        Example response:
            {
                "latency_ms": {"p50": 12.3, "p95": 45.6, "p99": 89.1},
                "qps_1m": 5.23
            }
        """
        # Calculate percentiles
        arr = sorted(lat_hist)
        n = len(arr)

        def percentile(p):
            """Calculate percentile from sorted array."""
            if n == 0:
                return None
            idx = min(int(p * (n - 1)), n - 1)
            return round(arr[idx], 1)

        return {
            "latency_ms": {
                "p50": percentile(0.5),   # Median
                "p95": percentile(0.95),  # 95th percentile
                "p99": percentile(0.99)   # 99th percentile
            },
            "qps_1m": round(len(req_1m) / 60, 2)  # Queries per second
        }

"""
Cross-cutting AI-gateway concerns, as reusable pieces.

These live in the GATEWAY layer on purpose: that is the whole point of having a
gateway. Mainstream AI gateways (LiteLLM, Kong AI Proxy) do exactly these:
PII masking, rate limiting, observability/chargeback, routing/fallback, caching.
"""
import re
import time
from collections import defaultdict, deque

from fastapi import HTTPException


# ---------- PII masking (security) ----------
_EMAIL = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")
_PHONE = re.compile(r"\+?\d[\d\s().-]{7,}\d")


def mask_pii(text: str) -> str:
    """Scrub emails/phones before the text ever leaves the gateway to a model."""
    text = _EMAIL.sub("[EMAIL]", text)
    text = _PHONE.sub("[PHONE]", text)
    return text


# ---------- rate limiting (fixed window per client) ----------
class RateLimiter:
    """In-memory fixed-window limiter. In prod back it with Redis so it works
    across multiple gateway workers."""

    def __init__(self, limit: int, window_s: float = 60.0):
        self.limit = limit
        self.window = window_s
        self._hits: dict[str, deque] = defaultdict(deque)

    def check(self, key: str) -> None:
        now = time.monotonic()
        q = self._hits[key]
        while q and now - q[0] > self.window:  # drop timestamps outside the window
            q.popleft()
        if len(q) >= self.limit:
            raise HTTPException(status_code=429, detail="rate limit exceeded")
        q.append(now)

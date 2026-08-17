"""In-memory sliding window rate limiter for FastAPI routes."""

import time
from collections import defaultdict
import threading
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse


class SlidingWindowRateLimiter:
    """Thread-safe in-memory sliding window rate limiter."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        # map: ip -> list of timestamps
        self._history: dict[str, list[float]] = defaultdict(list)
        # Clean up stale IP records every 5 minutes
        self._last_cleanup = time.time()

    def is_allowed(self, client_ip: str, limit: int, window_seconds: int = 60) -> tuple[bool, int]:
        """Check if request is allowed under sliding window limit.

        Returns (allowed: bool, retry_after_seconds: int).
        """
        now = time.time()
        window_start = now - window_seconds

        with self._lock:
            # Periodic cleanup of expired records
            if now - self._last_cleanup > 300:
                self._cleanup_stale(window_start)
                self._last_cleanup = now

            timestamps = self._history[client_ip]
            # Prune timestamps outside window
            valid_timestamps = [ts for ts in timestamps if ts > window_start]
            self._history[client_ip] = valid_timestamps

            if len(valid_timestamps) >= limit:
                oldest = valid_timestamps[0]
                retry_after = max(1, int(oldest + window_seconds - now))
                return False, retry_after

            valid_timestamps.append(now)
            return True, 0

    def _cleanup_stale(self, threshold: float) -> None:
        """Remove empty or outdated IP entries."""
        stale_keys = [
            ip for ip, timestamps in self._history.items()
            if not timestamps or timestamps[-1] <= threshold
        ]
        for ip in stale_keys:
            del self._history[ip]


# Singleton instance
rate_limiter = SlidingWindowRateLimiter()


class RateLimitMiddleware(BaseHTTPMiddleware):
    """FastAPI middleware applying sliding-window rate limits per client IP."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Exclude static assets and health check
        path = request.url.path
        if path.startswith("/static") or path in {"/health", "/docs", "/openapi.json"}:
            return await call_next(request)

        client_ip = _extract_client_ip(request)

        # Apply tighter limit on heavy endpoints
        if path in {"/api/generate", "/api/export/pdf", "/api/import/fetch"}:
            limit = 15  # 15 heavy generation requests per minute
        else:
            limit = 60  # 60 general API requests per minute

        allowed, retry_after = rate_limiter.is_allowed(client_ip, limit=limit, window_seconds=60)
        if not allowed:
            return JSONResponse(
                status_code=429,
                content={
                    "code": "rate_limited",
                    "message": "Too many requests. Please wait a moment before trying again.",
                },
                headers={"Retry-After": str(retry_after)},
            )

        return await call_next(request)


def _extract_client_ip(request: Request) -> str:
    """Safely extract client IP taking proxy headers into account."""
    # Check Cloudflare IP header
    cf_ip = request.headers.get("cf-connecting-ip")
    if cf_ip and cf_ip.strip():
        return cf_ip.strip()

    # Check X-Real-IP header
    real_ip = request.headers.get("x-real-ip")
    if real_ip and real_ip.strip():
        return real_ip.strip()

    # Check X-Forwarded-For header (left-most client IP)
    forwarded_for = request.headers.get("x-forwarded-for")
    if forwarded_for and forwarded_for.strip():
        client_part = forwarded_for.split(",")[0].strip()
        if client_part:
            return client_part

    return request.client.host if request.client else "unknown"

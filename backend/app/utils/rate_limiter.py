"""IP-based rate limiting with explicit trusted-proxy handling."""

import ipaddress
import threading
import time
from collections import defaultdict
from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from settings import settings


class SlidingWindowRateLimiter:
    """Thread-safe in-memory sliding-window rate limiter.

    This is suitable for a single backend instance. For horizontally scaled
    production deployments, use a shared store such as Redis.
    """

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._history: dict[str, list[float]] = defaultdict(list)
        self._last_cleanup = time.time()

    def is_allowed(self, client_ip: str, limit: int, window_seconds: int = 60) -> tuple[bool, int]:
        now = time.time()
        window_start = now - window_seconds

        with self._lock:
            if now - self._last_cleanup > 300:
                self._cleanup_stale(window_start)
                self._last_cleanup = now

            timestamps = self._history[client_ip]
            valid_timestamps = [ts for ts in timestamps if ts > window_start]
            self._history[client_ip] = valid_timestamps

            if len(valid_timestamps) >= limit:
                oldest = valid_timestamps[0]
                retry_after = max(1, int(oldest + window_seconds - now))
                return False, retry_after

            valid_timestamps.append(now)
            return True, 0

    def _cleanup_stale(self, threshold: float) -> None:
        stale_keys = [
            ip for ip, timestamps in self._history.items()
            if not timestamps or timestamps[-1] <= threshold
        ]
        for ip in stale_keys:
            del self._history[ip]


rate_limiter = SlidingWindowRateLimiter()


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Apply per-client rate limits without trusting spoofable proxy headers."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        path = request.url.path
        if path.startswith("/static") or path in {"/health", "/docs", "/openapi.json"}:
            return await call_next(request)

        client_ip = _extract_client_ip(request)
        limit = 15 if path in {"/api/generate", "/api/export/pdf", "/api/import/fetch"} else 60

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
    """Return the real client IP only when the immediate peer is trusted.

    By default proxy headers are ignored. Configure TRUSTED_PROXY_IPS with
    trusted proxy/load-balancer CIDRs when deploying behind one.
    """
    peer = request.client.host if request.client else "unknown"
    if not _is_trusted_proxy(peer):
        return peer

    # Only a trusted proxy may supply these headers.
    for header in ("cf-connecting-ip", "x-real-ip", "x-forwarded-for"):
        value = request.headers.get(header, "")
        if not value.strip():
            continue
        candidate = value.split(",")[0].strip()
        try:
            return str(ipaddress.ip_address(candidate))
        except ValueError:
            continue

    return peer


def _is_trusted_proxy(peer: str) -> bool:
    if not settings.trusted_proxy_ips:
        return False
    try:
        peer_ip = ipaddress.ip_address(peer)
    except ValueError:
        return False
    return any(peer_ip in network for network in settings.trusted_proxy_ips)

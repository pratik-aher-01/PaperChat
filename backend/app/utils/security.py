"""Security utilities for URL validation and SSRF protection."""

from functools import lru_cache
import ipaddress
import socket
from urllib.parse import urlparse


@lru_cache(maxsize=4096)
def is_safe_hostname(hostname: str) -> bool:
    """Check whether a hostname resolves to non-private/public IPs (cached)."""
    if not hostname:
        return False
    normalized = hostname.lower().strip(".")
    if normalized in {"localhost", "127.0.0.1", "0.0.0.0", "::1"}:
        return False

    try:
        ip_obj = ipaddress.ip_address(normalized)
        return not (ip_obj.is_private or ip_obj.is_loopback or ip_obj.is_reserved or ip_obj.is_link_local)
    except ValueError:
        pass

    try:
        addr_info = socket.getaddrinfo(normalized, None)
        for item in addr_info:
            ip_str = item[4][0]
            ip_obj = ipaddress.ip_address(ip_str)
            if ip_obj.is_private or ip_obj.is_loopback or ip_obj.is_reserved or ip_obj.is_link_local:
                return False
        return True
    except (socket.gaierror, ValueError, OSError):
        return False


def is_safe_url(url: str, allowed_hosts: set[str] | None = None) -> bool:
    """Validate that a URL is safe to fetch (HTTP/HTTPS only, no private/loopback IPs)."""
    if not url or not isinstance(url, str):
        return False

    try:
        parsed = urlparse(url.strip())
    except Exception:
        return False

    # 1. Scheme check: only http and https allowed
    if parsed.scheme.lower() not in {"http", "https"}:
        return False

    hostname = parsed.hostname
    if not hostname:
        return False

    normalized_host = hostname.lower().strip(".")

    # 2. Whitelist match if provided
    if allowed_hosts is not None:
        matches_allowed = any(
            normalized_host == host or normalized_host.endswith(f".{host}")
            for host in allowed_hosts
        )
        if not matches_allowed:
            return False

    # 3. Check IP safety with cached DNS lookup
    return is_safe_hostname(normalized_host)


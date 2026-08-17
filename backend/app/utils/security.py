"""Security utilities for URL validation and SSRF protection."""

import ipaddress
import socket
from urllib.parse import urlparse


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

    # 2. Block direct localhost / loopback identifiers
    if normalized_host in {"localhost", "127.0.0.1", "0.0.0.0", "::1"}:
        return False

    # 3. If allowed hosts whitelist is provided, check matching
    if allowed_hosts is not None:
        matches_allowed = any(
            normalized_host == host or normalized_host.endswith(f".{host}")
            for host in allowed_hosts
        )
        if not matches_allowed:
            return False

    # 4. Resolve IP and check against private / reserved IP ranges
    try:
        # Check if the hostname is directly an IP address
        try:
            ip_obj = ipaddress.ip_address(normalized_host)
            if ip_obj.is_private or ip_obj.is_loopback or ip_obj.is_reserved or ip_obj.is_link_local:
                return False
        except ValueError:
            # It's a domain name - resolve to IP addresses
            addr_info = socket.getaddrinfo(normalized_host, None)
            for item in addr_info:
                ip_str = item[4][0]
                ip_obj = ipaddress.ip_address(ip_str)
                if ip_obj.is_private or ip_obj.is_loopback or ip_obj.is_reserved or ip_obj.is_link_local:
                    return False
    except (socket.gaierror, ValueError, OSError):
        # If domain resolution fails, fail closed if domain was not whitelisted
        if allowed_hosts is None:
            return False

    return True

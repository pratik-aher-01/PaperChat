"""Unit tests for security utilities and HTTP security middleware."""

import pytest
from fastapi.testclient import TestClient

from app.main import create_app
from app.utils.security import is_safe_url


def test_is_safe_url_blocks_unsafe_schemes() -> None:
    """Blocks non-HTTP/HTTPS schemes."""
    assert not is_safe_url("file:///etc/passwd")
    assert not is_safe_url("file://chatgpt.com/etc/passwd")
    assert not is_safe_url("data:text/html,<script>alert(1)</script>")
    assert not is_safe_url("javascript:alert(1)")
    assert not is_safe_url("gopher://127.0.0.1:70")
    assert not is_safe_url("")
    assert not is_safe_url("   ")


def test_is_safe_url_blocks_internal_and_private_ips() -> None:
    """Blocks loopback, private, and link-local IP addresses."""
    assert not is_safe_url("http://localhost:8000/test")
    assert not is_safe_url("http://127.0.0.1:8000/test")
    assert not is_safe_url("http://127.0.0.2:8000/test")
    assert not is_safe_url("http://0.0.0.0:8000/test")
    assert not is_safe_url("http://192.168.1.1/admin")
    assert not is_safe_url("http://10.0.0.1/admin")
    assert not is_safe_url("http://172.16.0.1/admin")
    assert not is_safe_url("http://169.254.169.254/latest/meta-data")


def test_is_safe_url_allows_valid_public_https_urls() -> None:
    """Allows standard public URLs."""
    allowed = {"chatgpt.com", "claude.ai", "gemini.google.com"}
    assert is_safe_url("https://chatgpt.com/share/test", allowed_hosts=allowed)
    assert is_safe_url("https://claude.ai/share/test", allowed_hosts=allowed)
    assert is_safe_url("https://gemini.google.com/share/test", allowed_hosts=allowed)
    assert not is_safe_url("https://evil.com/share/test", allowed_hosts=allowed)


def test_api_sets_security_headers() -> None:
    """FastAPI responses include standard HTTP security headers and CSP."""
    app = create_app()
    client = TestClient(app)

    response = client.get("/health")
    assert response.headers.get("X-Content-Type-Options") == "nosniff"
    assert response.headers.get("X-Frame-Options") == "SAMEORIGIN"
    assert response.headers.get("X-XSS-Protection") == "1; mode=block"
    assert response.headers.get("Referrer-Policy") == "strict-origin-when-cross-origin"
    assert "Content-Security-Policy" in response.headers
    assert "Permissions-Policy" in response.headers


def test_parser_walk_obj_bounds_recursion() -> None:
    """JSON tree walker terminates safely on deeply nested structures."""
    from app.parsers.claude import _walk_obj

    # Build deeply nested object with 50 layers
    nested: dict = {"data": "deep"}
    for _ in range(50):
        nested = {"child": nested}

    items = list(_walk_obj(nested, max_depth=10))
    # Should stop at depth 10, not traverse all 50
    assert len(items) <= 12

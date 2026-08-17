"""Global concurrency limiter for browser-intensive operations."""

import threading
from concurrent.futures import ThreadPoolExecutor

# Cap concurrent heavy Playwright browser sessions at 4 to prevent CPU/memory exhaustion
MAX_CONCURRENT_BROWSERS = 4
_browser_semaphore = threading.Semaphore(MAX_CONCURRENT_BROWSERS)


def acquire_browser_slot(timeout: float = 60.0) -> bool:
    """Acquire a slot in the browser execution semaphore."""
    return _browser_semaphore.acquire(timeout=timeout)


def release_browser_slot() -> None:
    """Release a slot in the browser execution semaphore."""
    _browser_semaphore.release()

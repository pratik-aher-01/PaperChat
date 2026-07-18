"""HTTP acquisition implementation."""

from time import perf_counter
from urllib.request import Request, urlopen

from app.acquisition.base import BaseFetcher
from app.domain.fetch_result import FetchResult
from exceptions import AcquisitionException


class HttpFetcher(BaseFetcher):
    """Fetch raw HTML over HTTP without browser rendering."""

    async def fetch(self, url: str) -> FetchResult:
        """Fetch raw HTML for the supplied URL."""
        started_at = perf_counter()
        request = Request(url, headers={"User-Agent": "PaperChat/0.1.0"})

        try:
            with urlopen(request, timeout=30) as response:
                content = response.read().decode("utf-8", errors="replace")
                final_url = response.geturl()
                status = response.status
        except OSError as exc:
            raise AcquisitionException(f"HTTP acquisition failed: {exc}") from exc

        return FetchResult(
            url=url,
            final_url=final_url,
            title="",
            html=content,
            status=status,
            fetch_time_ms=round((perf_counter() - started_at) * 1000),
            metadata={"fetcher": "HttpFetcher", "rendered": False},
        )

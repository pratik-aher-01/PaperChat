"""HTTP acquisition implementation."""

from time import perf_counter
from urllib.request import Request, urlopen

from app.acquisition.base import BaseFetcher
from app.domain.fetch_result import FetchResult
from app.utils.security import is_safe_url
from exceptions import AcquisitionException
from settings import settings


class HttpFetcher(BaseFetcher):
    """Fetch raw HTML over HTTP without browser rendering."""

    async def fetch(self, url: str) -> FetchResult:
        """Fetch raw HTML for the supplied URL with SSRF and size protections."""
        started_at = perf_counter()
        if not is_safe_url(url):
            raise AcquisitionException("Blocked unsafe or invalid URL.")

        request = Request(url, headers={"User-Agent": "PaperChat/0.1.0"})

        try:
            with urlopen(request, timeout=30) as response:
                final_url = response.geturl()
                if not is_safe_url(final_url):
                    raise AcquisitionException("Blocked unsafe redirect destination.")

                content_length = response.headers.get("Content-Length")
                if content_length:
                    try:
                        if int(content_length) > settings.max_acquisition_bytes:
                            raise AcquisitionException("Remote document is too large.")
                    except ValueError:
                        pass

                content_bytes = response.read(settings.max_acquisition_bytes + 1)
                if len(content_bytes) > settings.max_acquisition_bytes:
                    raise AcquisitionException("Remote document is too large.")

                content = content_bytes.decode("utf-8", errors="replace")
                status = response.status
        except AcquisitionException:
            raise
        except OSError as exc:
            raise AcquisitionException("HTTP acquisition failed.") from exc

        return FetchResult(
            url=url,
            final_url=final_url,
            title="",
            html=content,
            status=status,
            fetch_time_ms=round((perf_counter() - started_at) * 1000),
            metadata={"fetcher": "HttpFetcher", "rendered": False},
        )

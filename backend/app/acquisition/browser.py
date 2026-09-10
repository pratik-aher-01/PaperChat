"""Browser-based rendered HTML acquisition."""

import asyncio
from collections.abc import Callable
from time import sleep
from time import perf_counter
from typing import Any

from playwright.sync_api import Error as PlaywrightError, Page, sync_playwright

from app.acquisition.base import BaseFetcher
from app.acquisition.concurrency import acquire_browser_slot, release_browser_slot
from app.domain.fetch_result import FetchResult
from app.utils.security import is_safe_url
from exceptions import AcquisitionException
from settings import settings


class BrowserFetcher(BaseFetcher):
    """Fetch fully rendered pages using a headless browser."""

    def __init__(self, timeout_ms: int = 45_000) -> None:
        """Initialize the browser fetcher."""
        self._timeout_ms = timeout_ms

    async def fetch(self, url: str) -> FetchResult:
        """Fetch fully rendered HTML for the supplied URL."""
        return await asyncio.to_thread(self._fetch_sync, url)

    def _fetch_sync(self, url: str) -> FetchResult:
        """Fetch fully rendered HTML in a worker thread."""
        if not is_safe_url(url):
            raise AcquisitionException("Blocked unsafe or invalid URL.")

        if not acquire_browser_slot(timeout=45.0):
            raise AcquisitionException("Server is experiencing high render load. Please retry in a few moments.")

        started_at = perf_counter()
        try:
            with sync_playwright() as playwright:
                browser = playwright.chromium.launch(
                    headless=True,
                    args=["--disable-dev-shm-usage", "--disable-gpu", "--no-sandbox"],
                )
                try:
                    page = browser.new_page()
                    page.set_default_timeout(self._timeout_ms)
                    _setup_security_routes(page)
                    response = page.goto(
                        url,
                        wait_until="domcontentloaded",
                        timeout=self._timeout_ms,
                    )
                    _wait_for_render_settle(page)
                    collected_messages = _collect_lazy_rendered_messages(page)

                    title = _retry_page_read(page.title)
                    html = _retry_page_read(page.content)
                    if len(html.encode("utf-8", errors="ignore")) > settings.max_acquisition_bytes:
                        raise AcquisitionException("Rendered document is too large.")
                    html = _append_collected_messages(html, collected_messages)
                    if len(html.encode("utf-8", errors="ignore")) > settings.max_acquisition_bytes:
                        raise AcquisitionException("Rendered document is too large.")

                    fetch_time_ms = _elapsed_ms(started_at)
                    status = response.status if response is not None else None

                    return FetchResult(
                        url=url,
                        final_url=page.url,
                        title=title,
                        html=html,
                        status=status,
                        fetch_time_ms=fetch_time_ms,
                        metadata=_metadata(
                            status=status,
                            collected_messages=len(collected_messages),
                        ),
                    )
                finally:
                    browser.close()
        except AcquisitionException:
            raise
        except PlaywrightError as exc:
            raise AcquisitionException("Browser acquisition failed.") from exc
        finally:
            release_browser_slot()


def _setup_security_routes(page: Page) -> None:
    """Intercept all sub-resource requests and abort unsafe or private destinations."""
    def _route_handler(route: Any) -> None:
        try:
            req_url = route.request.url
            if req_url.startswith("data:image/") or req_url.startswith("data:font/"):
                route.continue_()
                return
            if not is_safe_url(req_url):
                route.abort()
                return
            route.continue_()
        except Exception:
            route.abort()

    try:
        page.route("**/*", _route_handler)
    except Exception:
        pass


def _elapsed_ms(started_at: float) -> int:
    """Return elapsed milliseconds from a performance timestamp."""
    return round((perf_counter() - started_at) * 1000)


def _wait_for_render_settle(page: Page) -> None:
    """Wait for late client-side rendering without long idle timeouts."""
    selectors = (
        "[data-message-author-role]",
        "article",
        "user-query",
        "model-response",
        ".user-query",
        ".model-response",
        ".response-container",
        "message-content",
        ".font-claude-message",
        ".ds-markdown",
        "[data-testid*='message']",
    )
    for selector in selectors:
        try:
            page.wait_for_selector(selector, timeout=4_000)
            page.wait_for_timeout(300)
            return
        except PlaywrightError:
            continue
    page.wait_for_timeout(1_000)


def _collect_lazy_rendered_messages(page: Page) -> list[str]:
    """Scroll through SPA content and preserve virtualized message nodes across the full page."""
    _scroll_to_top(page)

    seen: set[str] = set()
    messages: list[str] = []

    for msg in _visible_message_snapshots(page):
        seen.add(msg["key"])
        messages.append(msg["html"])

    _walk_chat_surface_down(page, seen=seen, messages=messages)

    return messages


def _scroll_to_top(page: Page) -> None:
    """Scroll repeatedly to top edge until position stabilizes at top."""
    last_position = -1
    stable_reads = 0

    for _ in range(60):
        try:
            state = _scroll_chat_surface(page, "up")
            page.keyboard.press("Home")
            page.wait_for_timeout(150)
        except PlaywrightError:
            break

        position = int(state.get("position", 0))
        if position <= 15 or position == last_position:
            stable_reads += 1
        else:
            stable_reads = 0

        if position <= 15 and stable_reads >= 3:
            break

        last_position = position


def _walk_chat_surface_down(
    page: Page,
    *,
    seen: set[str],
    messages: list[str],
) -> None:
    """Walk down the full chat surface step-by-step, collecting visible message snapshots."""
    stable_reads = 0
    last_position = -1
    last_extent = -1

    for _ in range(250):
        for message in _visible_message_snapshots(page):
            key = message["key"]
            if key in seen:
                continue
            seen.add(key)
            messages.append(message["html"])

        try:
            state = _scroll_chat_surface(page, "down")
            page.keyboard.press("PageDown")
            page.wait_for_timeout(200)
        except PlaywrightError:
            break

        position = int(state.get("position", 0))
        extent = int(state.get("extent", 0))
        viewport = int(state.get("viewport", 0))

        at_edge = position + viewport >= extent - 20
        stable = position == last_position and extent == last_extent

        if at_edge and stable:
            stable_reads += 1
        else:
            stable_reads = 0

        if stable_reads >= 4:
            break

        last_position = position
        last_extent = extent

    for message in _visible_message_snapshots(page):
        key = message["key"]
        if key not in seen:
            seen.add(key)
            messages.append(message["html"])


def _scroll_chat_surface(page: Page, direction: str) -> dict[str, int]:
    """Scroll the conversation surface in direction ('up', 'down', 'top', 'bottom')."""
    return page.evaluate(
        """(direction) => {
            const messageSelector = '[data-message-author-role], user-query, model-response, .user-query, .model-response, article, [data-testid*=\"message\"], .font-claude-message, .ds-markdown';
            const scrollables = Array.from(document.querySelectorAll('body, body *'))
                .filter((node) => {
                    const style = window.getComputedStyle(node);
                    const overflow = `${style.overflowY} ${style.overflow}`;
                    return /(auto|scroll)/.test(overflow)
                        && node.scrollHeight > node.clientHeight + 40;
                });

            const withMessages = scrollables
                .filter((node) => node.querySelector(messageSelector))
                .sort((a, b) => (b.scrollHeight - b.clientHeight) - (a.scrollHeight - a.clientHeight));

            const documentRoot = document.scrollingElement || document.documentElement;
            const root = withMessages[0]
                || scrollables.sort((a, b) => (b.scrollHeight - b.clientHeight) - (a.scrollHeight - a.clientHeight))[0]
                || documentRoot;

            const viewport = root === documentRoot
                ? window.innerHeight || document.documentElement.clientHeight
                : root.clientHeight;
            const extent = root === documentRoot
                ? Math.max(documentRoot.scrollHeight, document.body.scrollHeight)
                : root.scrollHeight;
            const current = root === documentRoot
                ? window.scrollY || documentRoot.scrollTop || 0
                : root.scrollTop;
            const step = Math.max(Math.round(viewport * 0.75), 450);

            let next = current;
            if (direction === 'top') {
                next = 0;
            } else if (direction === 'bottom') {
                next = extent;
            } else if (direction === 'up') {
                next = Math.max(0, current - step);
            } else {
                next = Math.min(extent, current + step);
            }

            if (root === documentRoot) {
                window.scrollTo(0, next);
                if (document.body) document.body.scrollTop = next;
                if (document.documentElement) document.documentElement.scrollTop = next;
            } else {
                root.scrollTop = next;
                root.dispatchEvent(new Event('scroll', { bubbles: true }));
                window.scrollBy(0, direction === 'up' ? -step : step);
            }

            return {
                position: Math.round(next),
                extent: Math.round(extent),
                viewport: Math.round(viewport)
            };
        }""",
        direction,
    )


def _visible_message_snapshots(page: Page) -> list[dict[str, str]]:
    """Read currently mounted message nodes from the page."""
    try:
        snapshots = page.evaluate(
            """() => {
                const selector = '[data-message-author-role], user-query, model-response, .user-query, .model-response, message-content, .response-container, article, [data-testid*=\"message\"], .font-claude-message, .ds-markdown';
                const allNodes = Array.from(document.querySelectorAll(selector));
                const topLevelNodes = allNodes.filter(node => !allNodes.some(other => other !== node && other.contains(node)));

                return topLevelNodes
                    .map((node) => {
                        const role = node.getAttribute('data-message-author-role')
                            || node.getAttribute('data-message-role')
                            || (node.tagName.toLowerCase().includes('user') || String(node.className).includes('user') ? 'user' : 'assistant');
                        const id = node.getAttribute('data-message-id')
                            || node.getAttribute('data-testid')
                            || node.id
                            || '';
                        const text = (node.innerText || node.textContent || '')
                            .replace(/\\s+/g, ' ')
                            .trim();
                        const key = id ? `id:${id}` : `${role}:${text.slice(0, 200)}`;
                        return {
                            key: key,
                            html: node.outerHTML || ''
                        };
                    })
                    .filter((item) => item.html && item.key && item.key.length > 3);
            }"""
        )
    except PlaywrightError:
        return []

    if not isinstance(snapshots, list):
        return []

    return [
        {"key": str(item.get("key", "")), "html": str(item.get("html", ""))}
        for item in snapshots
        if isinstance(item, dict) and item.get("key") and item.get("html")
    ]


def _append_collected_messages(html: str, messages: list[str]) -> str:
    """Append preserved message nodes so parsers can see virtualized content."""
    if not messages:
        return html

    collected = "\n".join(messages)
    payload = (
        '<section data-paperchat-collected-messages="true" hidden>'
        f"{collected}"
        "</section>"
    )
    if "</body>" in html:
        return html.replace("</body>", f"{payload}</body>", 1)
    return f"{html}{payload}"


def _retry_page_read(read: Callable[[], str], attempts: int = 5) -> str:
    """Retry page reads while a SPA is still navigating or mutating."""
    last_error: PlaywrightError | None = None
    for attempt in range(attempts):
        try:
            return read()
        except PlaywrightError as exc:
            last_error = exc
            if "navigating and changing the content" not in str(exc):
                raise
            sleep(0.5 * (attempt + 1))

    if last_error is not None:
        raise last_error
    return ""


def _metadata(status: int | None, collected_messages: int = 0) -> dict[str, Any]:
    """Build acquisition metadata."""
    return {
        "fetcher": "BrowserFetcher",
        "rendered": True,
        "http_status": status,
        "collected_messages": collected_messages,
    }

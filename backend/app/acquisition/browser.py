"""Browser-based rendered HTML acquisition."""

import asyncio
from collections.abc import Callable
from time import sleep
from time import perf_counter
from typing import Any

from playwright.sync_api import Error as PlaywrightError, Page, sync_playwright

from app.acquisition.base import BaseFetcher
from app.domain.fetch_result import FetchResult
from exceptions import AcquisitionException


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
        started_at = perf_counter()
        try:
            with sync_playwright() as playwright:
                browser = playwright.chromium.launch(headless=True)
                try:
                    page = browser.new_page()
                    response = page.goto(
                        url,
                        wait_until="domcontentloaded",
                        timeout=self._timeout_ms,
                    )
                    _wait_for_render_settle(page)
                    collected_messages = _collect_lazy_rendered_messages(page)

                    title = _retry_page_read(page.title)
                    html = _retry_page_read(page.content)
                    html = _append_collected_messages(html, collected_messages)
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
        except PlaywrightError as exc:
            raise AcquisitionException(f"Browser acquisition failed: {exc}") from exc


def _elapsed_ms(started_at: float) -> int:
    """Return elapsed milliseconds from a performance timestamp."""
    return round((perf_counter() - started_at) * 1000)


def _wait_for_render_settle(page: Page) -> None:
    """Wait for late client-side rendering without failing on active apps."""
    try:
        page.wait_for_load_state("networkidle", timeout=10_000)
    except PlaywrightError:
        page.wait_for_timeout(2_000)


def _collect_lazy_rendered_messages(page: Page) -> list[str]:
    """Scroll through SPA content and preserve virtualized message nodes."""
    seen: set[str] = set()
    messages: list[str] = []

    try:
        page.keyboard.press("End")
        _scroll_chat_surface(page, "bottom")
        page.wait_for_timeout(500)
    except PlaywrightError:
        return messages

    _walk_chat_surface(page, direction="up", collect=False, seen=seen, messages=messages)

    seen.clear()
    messages.clear()

    try:
        _scroll_chat_surface(page, "top")
        page.keyboard.press("Home")
        page.wait_for_timeout(600)
    except PlaywrightError:
        return messages

    _walk_chat_surface(page, direction="down", collect=True, seen=seen, messages=messages)

    return messages


def _walk_chat_surface(
    page: Page,
    *,
    direction: str,
    collect: bool,
    seen: set[str],
    messages: list[str],
) -> None:
    """Walk a virtualized chat surface in one direction."""
    stable_reads = 0
    last_position = -1
    last_extent = -1

    for _ in range(90):
        if collect:
            for message in _visible_message_snapshots(page):
                key = message["key"]
                if key in seen:
                    continue
                seen.add(key)
                messages.append(message["html"])

        try:
            state = _scroll_chat_surface(page, direction)
            page.wait_for_timeout(350)
        except PlaywrightError:
            break

        position = int(state.get("position", 0))
        extent = int(state.get("extent", 0))
        viewport = int(state.get("viewport", 0))
        at_edge = position <= 24 if direction == "up" else position + viewport >= extent - 24
        stable = position == last_position and extent == last_extent

        if at_edge or stable:
            stable_reads += 1
        else:
            stable_reads = 0

        if stable_reads >= 4:
            break

        last_position = position
        last_extent = extent

    if collect:
        for message in _visible_message_snapshots(page):
            key = message["key"]
            if key not in seen:
                seen.add(key)
                messages.append(message["html"])


def _scroll_chat_surface(page: Page, direction: str) -> dict[str, int]:
    """Scroll the most likely ChatGPT conversation surface."""
    return page.evaluate(
        """(direction) => {
            const messageSelector = '[data-message-author-role]';
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
            const step = Math.max(viewport * 0.82, 650);

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
            } else {
                root.scrollTop = next;
                root.dispatchEvent(new Event('scroll', { bubbles: true }));
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
            """() => Array.from(document.querySelectorAll('[data-message-author-role]'))
                .map((node, index) => {
                    const role = node.getAttribute('data-message-author-role') || '';
                    const id = node.getAttribute('data-message-id')
                        || node.getAttribute('data-testid')
                        || node.id
                        || '';
                    const text = (node.innerText || node.textContent || '')
                        .replace(/\\s+/g, ' ')
                        .trim();
                    return {
                        key: id || `${role}:${text.slice(0, 240)}:${index}`,
                        html: node.outerHTML || ''
                    };
                })
                .filter((item) => item.html && item.key)"""
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

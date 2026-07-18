"""PDF exporter using Playwright."""

import asyncio
from pathlib import Path

from playwright.sync_api import Error as PlaywrightError, sync_playwright

from app.renderer.themes import DEFAULT_STYLESHEET_PATH, DEFAULT_STYLESHEET_URL
from exceptions import ExporterException


class PdfExporter:
    """Export rendered HTML to PDF."""

    async def export(self, html: str) -> bytes:
        """Export HTML to a PDF byte stream."""
        return await asyncio.to_thread(self._export_sync, html)

    def _export_sync(self, html: str) -> bytes:
        """Render PDF in a worker thread."""
        html = _prepare_html_for_pdf(html)
        try:
            with sync_playwright() as playwright:
                browser = playwright.chromium.launch(headless=True)
                try:
                    page = browser.new_page()
                    page.emulate_media(media="print")
                    page.set_content(html, wait_until="networkidle")
                    return page.pdf(
                        format="A4",
                        print_background=True,
                        prefer_css_page_size=True,
                        display_header_footer=True,
                        margin={
                            "top": "16mm",
                            "right": "16mm",
                            "bottom": "22mm",
                            "left": "16mm",
                        },
                        header_template=(
                            '<div style="width:100%;font-size:8px;color:#98a2b3;'
                            'padding:0 16mm;text-align:left;">PaperChat</div>'
                        ),
                        footer_template=(
                            '<div style="width:100%;font-size:9px;color:#667085;'
                            'padding:0 16mm;text-align:right;">'
                            'Page <span class="pageNumber"></span> of '
                            '<span class="totalPages"></span></div>'
                        ),
                    )
                finally:
                    browser.close()
        except PlaywrightError as exc:
            raise ExporterException(f"PDF export failed: {exc}") from exc


def _prepare_html_for_pdf(html: str) -> str:
    """Point stylesheet links at the local file system for PDF generation."""
    stylesheet_uri = _file_uri(DEFAULT_STYLESHEET_PATH)
    return html.replace(DEFAULT_STYLESHEET_URL, stylesheet_uri)


def _file_uri(path: Path) -> str:
    """Return a browser-readable file URI."""
    return path.resolve().as_uri()

"""PDF exporter using Playwright."""

import asyncio
from pathlib import Path

from app.renderer.themes import DEFAULT_STYLESHEET_PATH, DEFAULT_STYLESHEET_URL
from exceptions import ExporterException


class PdfExporter:
    """Export rendered HTML to PDF."""

    async def export(
        self,
        html: str,
        *,
        page_format: str = "A4",
        margin: str = "normal",
        show_headers: bool = True,
    ) -> bytes:
        """Export HTML to a PDF byte stream."""
        return await asyncio.to_thread(
            self._export_sync,
            html,
            page_format=page_format,
            margin=margin,
            show_headers=show_headers,
        )

    def _export_sync(
        self,
        html: str,
        *,
        page_format: str = "A4",
        margin: str = "normal",
        show_headers: bool = True,
    ) -> bytes:
        """Render PDF in a worker thread."""
        html = _prepare_html_for_pdf(html)
        margin_dict = _margin_bounds(margin)
        paper_format = _format_name(page_format)
        try:
            from playwright.sync_api import Error as PlaywrightError, sync_playwright

            with sync_playwright() as playwright:
                browser = playwright.chromium.launch(headless=True)
                try:
                    page = browser.new_page()
                    page.emulate_media(media="print")
                    page.set_content(html, wait_until="load")
                    try:
                        page.evaluate(
                            """() => {
                                if (typeof renderMathInElement === 'function') {
                                    renderMathInElement(document.body, {
                                        delimiters: [
                                            {left: '$$', right: '$$', display: true},
                                            {left: '\\[', right: '\\]', display: true},
                                            {left: '$', right: '$', display: false},
                                            {left: '\\(', right: '\\)', display: false}
                                        ],
                                        throwOnError: false
                                    });
                                }
                            }"""
                        )
                        page.wait_for_timeout(300)
                    except Exception:
                        pass
                    return page.pdf(
                        format=paper_format,
                        print_background=True,
                        prefer_css_page_size=True,
                        display_header_footer=show_headers,
                        margin=margin_dict,
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
        except ImportError as exc:
            raise ExporterException(
                "Playwright PDF export is unavailable. Install playwright and Chromium."
            ) from exc
        except PlaywrightError as exc:
            raise ExporterException(f"PDF export failed: {exc}") from exc


def _prepare_html_for_pdf(html: str) -> str:
    """Inline default stylesheet content directly into HTML for Playwright PDF export."""
    try:
        css_content = DEFAULT_STYLESHEET_PATH.read_text(encoding="utf-8")
        style_block = f"<style>\n{css_content}\n</style>"
        link_tag = f'<link rel="stylesheet" href="{DEFAULT_STYLESHEET_URL}" />'
        if link_tag in html:
            return html.replace(link_tag, style_block, 1)
        if "</head>" in html:
            return html.replace("</head>", f"{style_block}\n</head>", 1)
        return f"{style_block}\n{html}"
    except OSError:
        stylesheet_uri = _file_uri(DEFAULT_STYLESHEET_PATH)
        return html.replace(DEFAULT_STYLESHEET_URL, stylesheet_uri)


def _file_uri(path: Path) -> str:
    """Return a browser-readable file URI."""
    return path.resolve().as_uri()


def _margin_bounds(margin: str) -> dict[str, str]:
    """Map margin setting to Playwright margin bounds."""
    m = margin.lower().strip()
    if m == "narrow":
        return {"top": "10mm", "right": "10mm", "bottom": "14mm", "left": "10mm"}
    if m == "wide":
        return {"top": "24mm", "right": "24mm", "bottom": "30mm", "left": "24mm"}
    return {"top": "16mm", "right": "16mm", "bottom": "22mm", "left": "16mm"}


def _format_name(page_format: str) -> str:
    """Normalize page format for Playwright PDF export."""
    fmt = page_format.upper().strip()
    if fmt in {"A4", "LETTER", "LEGAL"}:
        return fmt.capitalize() if fmt != "A4" else "A4"
    return "A4"

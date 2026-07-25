"""PDF export and one-call generation API routes."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response, status
from pydantic import BaseModel, Field

from app.acquisition.base import BaseFetcher
from app.api.importer import (
    get_browser_fetcher,
    get_conversation_normalizer,
    get_importer_factory,
    get_parser_factory,
)
from app.api.renderer import ConversationInput, conversation_from_input, get_html_renderer
from app.domain.conversation import Conversation
from app.exporters.pdf import PdfExporter
from app.importers.factory import ImporterFactory
from app.parsers.factory import ParserFactory
from app.renderer.html_renderer import HtmlRenderer
from app.services.conversation_normalizer import ConversationNormalizer
from exceptions import AcquisitionException, ExporterException, ParserException, RendererException
from logger import logger

router = APIRouter(prefix="/api", tags=["export"])


class GenerateOptions(BaseModel):
    """Optional PDF rendering and exporter configuration."""

    layout: str = "single"
    page_format: str = "A4"
    font_family: str = "inter"
    font_size: str = "medium"
    line_spacing: str = "normal"
    margin: str = "normal"
    theme: str = "default"
    show_cover: bool = True
    show_headers: bool = True


class GenerateRequest(BaseModel):
    """Request payload for one-call PDF generation."""

    url: str = Field(min_length=1)
    options: GenerateOptions = Field(default_factory=GenerateOptions)


def get_pdf_exporter() -> PdfExporter:
    """Provide the Playwright PDF exporter."""
    return PdfExporter()


@router.post("/export/pdf")
async def export_pdf(
    payload: ConversationInput,
    renderer: Annotated[HtmlRenderer, Depends(get_html_renderer)],
    exporter: Annotated[PdfExporter, Depends(get_pdf_exporter)],
) -> Response:
    """Render and export a conversation as a PDF download."""
    conversation = conversation_from_input(payload)
    opts = payload.options if isinstance(payload.options, dict) else payload.options.model_dump()
    try:
        custom_renderer = HtmlRenderer(
            layout=str(opts.get("layout", "single")),
            font_family=str(opts.get("font_family", "inter")),
            font_size=str(opts.get("font_size", "medium")),
            line_spacing=str(opts.get("line_spacing", "normal")),
            theme=str(opts.get("theme", "default")),
            show_cover=bool(opts.get("show_cover", True)),
            page_format=str(opts.get("page_format", "A4")),
            margin=str(opts.get("margin", "normal")),
        )
        html = custom_renderer.render(conversation)
        pdf = await exporter.export(
            html,
            page_format=str(opts.get("page_format", "A4")),
            margin=str(opts.get("margin", "normal")),
            show_headers=bool(opts.get("show_headers", True)),
        )
    except RendererException as exc:
        raise _structured_error(422, "renderer_failed", str(exc)) from exc
    except ExporterException as exc:
        raise _structured_error(status.HTTP_502_BAD_GATEWAY, "pdf_failed", str(exc)) from exc
    except Exception as exc:
        logger.exception("Unexpected PDF export failure")
        raise _structured_error(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            "pdf_failed",
            "Unexpected PDF export failure.",
        ) from exc

    return _pdf_response(pdf, filename=_pdf_filename(conversation.title))


@router.post("/generate")
async def generate_pdf(
    payload: GenerateRequest,
    importer_factory: Annotated[ImporterFactory, Depends(get_importer_factory)],
    fetcher: Annotated[BaseFetcher, Depends(get_browser_fetcher)],
    parser_factory: Annotated[ParserFactory, Depends(get_parser_factory)],
    normalizer: Annotated[ConversationNormalizer, Depends(get_conversation_normalizer)],
    renderer: Annotated[HtmlRenderer, Depends(get_html_renderer)],
    exporter: Annotated[PdfExporter, Depends(get_pdf_exporter)],
) -> Response:
    """Run the complete share-link to PDF pipeline."""
    try:
        conversation = await _conversation_from_url(
            url=payload.url,
            importer_factory=importer_factory,
            fetcher=fetcher,
            parser_factory=parser_factory,
            normalizer=normalizer,
        )
        opts = payload.options
        custom_renderer = HtmlRenderer(
            layout=opts.layout,
            font_family=opts.font_family,
            font_size=opts.font_size,
            line_spacing=opts.line_spacing,
            theme=opts.theme,
            show_cover=opts.show_cover,
            page_format=opts.page_format,
            margin=opts.margin,
        )
        html = custom_renderer.render(conversation)
        pdf = await exporter.export(
            html,
            page_format=opts.page_format,
            margin=opts.margin,
            show_headers=opts.show_headers,
        )
    except HTTPException:
        raise
    except RendererException as exc:
        raise _structured_error(422, "renderer_failed", str(exc)) from exc
    except ExporterException as exc:
        raise _structured_error(status.HTTP_502_BAD_GATEWAY, "pdf_failed", str(exc)) from exc
    except Exception as exc:
        logger.exception("Unexpected generation failure for %s", payload.url)
        raise _structured_error(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            "generation_failed",
            "Unexpected generation failure.",
        ) from exc

    return _pdf_response(pdf, filename=_pdf_filename(conversation.title))


async def _conversation_from_url(
    url: str,
    importer_factory: ImporterFactory,
    fetcher: BaseFetcher,
    parser_factory: ParserFactory,
    normalizer: ConversationNormalizer,
) -> Conversation:
    """Run detection, acquisition, parsing, and normalization."""
    importer = importer_factory.get_importer(url)
    if importer is None:
        raise _structured_error(status.HTTP_400_BAD_REQUEST, "unsupported_platform", "Unsupported import URL.")

    parser = parser_factory.get_parser(importer.platform)
    if parser is None:
        raise _structured_error(
            status.HTTP_501_NOT_IMPLEMENTED,
            "parser_missing",
            f"No parser is registered for {importer.platform}.",
        )

    try:
        fetch_result = await fetcher.fetch(url)
        conversation = parser.parse(fetch_result)
        return normalizer.normalize(conversation)
    except NotImplementedError as exc:
        raise _structured_error(status.HTTP_501_NOT_IMPLEMENTED, "parser_not_implemented", str(exc)) from exc
    except AcquisitionException as exc:
        raise _structured_error(status.HTTP_502_BAD_GATEWAY, "fetch_failed", str(exc)) from exc
    except ParserException as exc:
        raise _structured_error(422, "parser_failed", str(exc)) from exc


def _pdf_response(pdf: bytes, filename: str) -> Response:
    """Build a PDF download response."""
    return Response(
        content=pdf,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


def _pdf_filename(title: str) -> str:
    """Create a safe PDF filename."""
    safe = "".join(char if char.isalnum() else "-" for char in title.lower()).strip("-")
    return f"{safe or 'paperchat-conversation'}.pdf"


def _structured_error(status_code: int, code: str, message: str) -> HTTPException:
    """Create a structured API error."""
    return HTTPException(status_code=status_code, detail={"code": code, "message": message})

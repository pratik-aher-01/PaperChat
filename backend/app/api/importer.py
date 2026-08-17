"""Import detection API routes."""

from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from app.acquisition.base import BaseFetcher
from app.acquisition.factory import FetcherFactory
from app.domain.enums import Platform
from app.domain.fetch_result import FetchResult
from app.importers.base import BaseImporter
from app.importers.factory import ImporterFactory
from app.importers.registry import ImporterRegistry, create_default_registry
from app.parsers.factory import ParserFactory
from app.parsers.registry import ParserRegistry, create_default_parser_registry
from app.services.conversation_normalizer import ConversationNormalizer
from exceptions import AcquisitionException, ParserException
from logger import logger
from settings import settings

router = APIRouter(prefix="/api/import", tags=["import"])
DEBUG_HTML_PATH = Path(__file__).resolve().parents[2] / "debug" / "chat.html"


class ImportDetectRequest(BaseModel):
    """Request payload for import platform detection."""

    url: str = Field(min_length=1, max_length=2048)


class ImportDetectResponse(BaseModel):
    """Response payload for import platform detection."""

    platform: Platform
    supported: bool
    importer: str | None = None


class ImportFetchResponse(BaseModel):
    """Response payload for import acquisition."""

    platform: Platform
    status: str
    title: str
    html_length: int
    fetch_time_ms: int


class ParsedMessageResponse(BaseModel):
    """Response payload for one parsed message."""

    id: str
    role: str
    plain_text: str


class ImportParseResponse(BaseModel):
    """Response payload for conversation parsing."""

    platform: Platform
    title: str
    message_count: int
    messages: list[ParsedMessageResponse]


def get_importer_registry() -> ImporterRegistry:
    """Provide the configured importer registry."""
    return create_default_registry()


def get_importer_factory(
    registry: Annotated[ImporterRegistry, Depends(get_importer_registry)],
) -> ImporterFactory:
    """Provide an importer factory."""
    return ImporterFactory(registry=registry)


def get_fetcher_factory() -> FetcherFactory:
    """Provide a fetcher factory."""
    return FetcherFactory()


def get_browser_fetcher(
    factory: Annotated[FetcherFactory, Depends(get_fetcher_factory)],
) -> BaseFetcher:
    """Provide the default rendered-page fetcher."""
    return factory.create_browser_fetcher()


def get_parser_registry() -> ParserRegistry:
    """Provide the configured parser registry."""
    return create_default_parser_registry()


def get_parser_factory(
    registry: Annotated[ParserRegistry, Depends(get_parser_registry)],
) -> ParserFactory:
    """Provide a parser factory."""
    return ParserFactory(registry=registry)


def get_conversation_normalizer() -> ConversationNormalizer:
    """Provide a conversation normalizer."""
    return ConversationNormalizer()


@router.post(
    "/detect",
    response_model=ImportDetectResponse,
    response_model_exclude_none=True,
)
def detect_importer(
    payload: ImportDetectRequest,
    factory: Annotated[ImporterFactory, Depends(get_importer_factory)],
) -> ImportDetectResponse:
    """Detect whether a URL belongs to a supported import platform."""
    importer = factory.get_importer(payload.url)
    if importer is None:
        return ImportDetectResponse(platform=Platform.UNKNOWN, supported=False)

    return _supported_response(importer)


@router.post("/fetch", response_model=ImportFetchResponse)
async def fetch_import_source(
    payload: ImportDetectRequest,
    importer_factory: Annotated[ImporterFactory, Depends(get_importer_factory)],
    fetcher: Annotated[BaseFetcher, Depends(get_browser_fetcher)],
) -> ImportFetchResponse:
    """Fetch rendered HTML for a supported import URL."""
    importer = importer_factory.get_importer(payload.url)
    if importer is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported import URL.",
        )

    try:
        result = await fetcher.fetch(payload.url)
    except AcquisitionException as exc:
        logger.warning("Acquisition failed for %s: %s", payload.url, exc)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(exc),
        ) from exc
    except Exception as exc:
        logger.exception("Unexpected acquisition failure for %s", payload.url)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Unexpected acquisition failure.",
        ) from exc

    _save_debug_html(result)
    return ImportFetchResponse(
        platform=importer.platform,
        status="success",
        title=result.title,
        html_length=len(result.html),
        fetch_time_ms=result.fetch_time_ms,
    )


@router.post("/parse", response_model=ImportParseResponse)
async def parse_import_source(
    payload: ImportDetectRequest,
    importer_factory: Annotated[ImporterFactory, Depends(get_importer_factory)],
    fetcher: Annotated[BaseFetcher, Depends(get_browser_fetcher)],
    parser_factory: Annotated[ParserFactory, Depends(get_parser_factory)],
    normalizer: Annotated[ConversationNormalizer, Depends(get_conversation_normalizer)],
) -> ImportParseResponse:
    """Fetch, parse, and normalize a supported conversation URL."""
    importer = importer_factory.get_importer(payload.url)
    if importer is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported import URL.",
        )

    parser = parser_factory.get_parser(importer.platform)
    if parser is None:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail=f"No parser is registered for {importer.platform}.",
        )

    try:
        fetch_result = await fetcher.fetch(payload.url)
        _save_debug_html(fetch_result)
        conversation = parser.parse(fetch_result)
        normalized = normalizer.normalize(conversation)
    except NotImplementedError as exc:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail=str(exc),
        ) from exc
    except AcquisitionException as exc:
        logger.warning("Acquisition failed for %s: %s", payload.url, exc)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(exc),
        ) from exc
    except ParserException as exc:
        logger.warning("Parsing failed for %s: %s", payload.url, exc)
        raise HTTPException(
            status_code=422,
            detail=str(exc),
        ) from exc
    except Exception as exc:
        logger.exception("Unexpected parse failure for %s", payload.url)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unexpected parse failure.",
        ) from exc

    return ImportParseResponse(
        platform=normalized.platform,
        title=normalized.title,
        message_count=len(normalized.messages),
        messages=[
            ParsedMessageResponse(
                id=message.id,
                role=message.role,
                plain_text=message.plain_text,
            )
            for message in normalized.messages
        ],
    )


def _supported_response(importer: BaseImporter) -> ImportDetectResponse:
    """Build a supported-platform detection response."""
    return ImportDetectResponse(
        platform=importer.platform,
        supported=True,
        importer=importer.__class__.__name__,
    )


def _save_debug_html(result: FetchResult) -> None:
    """Save fetched HTML for local debugging only when debug mode is enabled."""
    if not settings.debug:
        return
    try:
        DEBUG_HTML_PATH.parent.mkdir(parents=True, exist_ok=True)
        DEBUG_HTML_PATH.write_text(result.html, encoding="utf-8")
    except OSError as exc:
        logger.warning("Could not save debug HTML to %s: %s", DEBUG_HTML_PATH, exc)

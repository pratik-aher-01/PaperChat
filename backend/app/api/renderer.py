"""Rendering API routes and conversation DTOs."""

from typing import Any

from fastapi import APIRouter, HTTPException, Response, status
from pydantic import BaseModel, Field

from app.domain.conversation import Conversation
from app.domain.content_block import ContentBlock
from app.domain.enums import Platform
from app.domain.message import Message
from app.domain.metadata import ConversationMetadata
from app.renderer.html_renderer import HtmlRenderer
from exceptions import RendererException
from logger import logger
from settings import settings

router = APIRouter(prefix="/api/render", tags=["render"])


class ContentBlockInput(BaseModel):
    """API input for a message content block."""

    type: str = Field(default="markdown", max_length=64)
    text: str = Field(max_length=500_000)


class MessageInput(BaseModel):
    """API input for a conversation message."""

    id: str = Field(max_length=128)
    role: str = Field(max_length=64)
    plain_text: str = Field(max_length=1_000_000)
    content_blocks: list[ContentBlockInput] = Field(default_factory=list, max_length=100)


class ConversationMetadataInput(BaseModel):
    """API input for conversation metadata."""

    source_url: str = Field(default="", max_length=2048)
    final_url: str = Field(default="", max_length=2048)
    title: str = Field(default="", max_length=500)
    raw_html: str = Field(default="", max_length=10_000_000)
    fetch_time_ms: int = Field(default=0, ge=0)
    extra: dict[str, Any] = Field(default_factory=dict)


class ConversationInput(BaseModel):
    """API input for a normalized conversation."""

    platform: Platform
    title: str = Field(max_length=500)
    messages: list[MessageInput] = Field(min_length=1, max_length=2000)
    metadata: ConversationMetadataInput = Field(default_factory=ConversationMetadataInput)
    raw_html: str = Field(default="", max_length=10_000_000)
    options: dict[str, Any] = Field(default_factory=dict)


def conversation_from_input(payload: ConversationInput) -> Conversation:
    """Convert an API payload into the Conversation domain model."""
    metadata = ConversationMetadata(
        source_url=payload.metadata.source_url,
        final_url=payload.metadata.final_url,
        title=payload.metadata.title or payload.title,
        raw_html=payload.metadata.raw_html or payload.raw_html,
        fetch_time_ms=payload.metadata.fetch_time_ms,
        extra=payload.metadata.extra,
    )
    return Conversation(
        platform=payload.platform,
        title=payload.title,
        messages=tuple(
            Message(
                id=message.id,
                role=message.role,
                plain_text=message.plain_text,
                content_blocks=tuple(
                    ContentBlock(type=block.type, text=block.text)
                    for block in message.content_blocks
                ),
            )
            for message in payload.messages
        ),
        metadata=metadata,
        raw_html=payload.raw_html or metadata.raw_html,
    )


def get_html_renderer() -> HtmlRenderer:
    """Provide the default HTML renderer."""
    return HtmlRenderer(layout=settings.document_layout)


@router.post("/html", response_class=Response)
def render_html(payload: ConversationInput) -> Response:
    """Render a conversation as a complete HTML document."""
    try:
        opts = payload.options
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
        html = custom_renderer.render(conversation_from_input(payload))
    except RendererException as exc:
        logger.warning("Rendering failed: %s", exc)
        raise HTTPException(
            status_code=422,
            detail={"code": "renderer_failed", "message": str(exc)},
        ) from exc
    except Exception as exc:
        logger.exception("Unexpected rendering failure")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"code": "renderer_failed", "message": "Unexpected rendering failure."},
        ) from exc

    return Response(content=html, media_type="text/html; charset=utf-8")

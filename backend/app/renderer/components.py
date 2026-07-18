"""Reusable HTML components for rendered documents."""

from dataclasses import dataclass
from html import escape


@dataclass(frozen=True)
class Heading:
    """Rendered heading metadata for the table of contents."""

    level: int
    text: str
    anchor: str


@dataclass(frozen=True)
class MetadataItem:
    """A compact metadata field shown in the document front matter."""

    label: str
    value: str


def render_cover_stat(label: str, value: str) -> str:
    """Render one cover page statistic."""
    return (
        '<div class="cover-stat">'
        f"<dt>{escape(label)}</dt>"
        f"<dd>{escape(value)}</dd>"
        "</div>"
    )


def render_metadata_item(item: MetadataItem) -> str:
    """Render one metadata card item."""
    return (
        '<div class="metadata-item">'
        f"<dt>{escape(item.label)}</dt>"
        f"<dd>{_link_or_text(item.value)}</dd>"
        "</div>"
    )


def render_toc_item(heading: Heading) -> str:
    """Render one dotted-leader TOC item."""
    return (
        f'<li class="toc-level-{heading.level}">'
        f'<a href="#{escape(heading.anchor, quote=True)}">'
        f'<span class="toc-title">{escape(heading.text)}</span>'
        '<span class="toc-leader"></span>'
        '<span class="toc-page"></span>'
        "</a>"
        "</li>"
    )


def render_section(
    *,
    section_id: str,
    label: str,
    index: int,
    role: str,
    content: str,
) -> str:
    """Render one conversation message as a document section."""
    return (
        f'<article class="message message-{escape(role)}" '
        f'id="{escape(section_id, quote=True)}">'
        '<header class="message-header">'
        f'<span class="message-index">{index:02d}</span>'
        f'<p>{escape(label)}</p>'
        "</header>"
        f'<div class="message-content">{content}</div>'
        "</article>"
    )


def _link_or_text(value: str) -> str:
    """Render URLs as links."""
    escaped = escape(value)
    if value.startswith(("http://", "https://")):
        return f'<a href="{escaped}">{escaped}</a>'
    return escaped

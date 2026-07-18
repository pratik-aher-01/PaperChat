"""HTML renderer for normalized conversations."""

from datetime import datetime
from html import escape
import re
from uuid import uuid4

from app.domain.conversation import Conversation
from app.domain.message import Message
from app.renderer.base import BaseRenderer
from app.renderer.components import (
    Heading,
    MetadataItem,
    render_cover_stat,
    render_metadata_item,
    render_section,
    render_toc_item,
)
from app.renderer.template_engine import TemplateEngine
from app.renderer.themes import DEFAULT_STYLESHEET_URL, DEFAULT_TEMPLATE
from exceptions import RendererException


class HtmlRenderer(BaseRenderer):
    """Render conversations as professional printable HTML."""

    def __init__(self, template_engine: TemplateEngine | None = None) -> None:
        """Initialize the renderer."""
        self._template_engine = template_engine or TemplateEngine()

    def render(self, conversation: Conversation) -> str:
        """Render a conversation into a complete HTML document."""
        if not conversation.messages:
            raise RendererException("Conversation must contain at least one message.")

        headings: list[Heading] = []
        body = "\n".join(
            self._render_message(message, index, headings)
            for index, message in enumerate(conversation.messages, start=1)
        )
        generated_date = datetime.now().strftime("%B %d, %Y")
        toc = self._render_toc(headings)
        metadata = self._render_metadata(conversation, generated_date)
        cover_stats = self._render_cover_stats(conversation, generated_date)

        return self._template_engine.render(
            DEFAULT_TEMPLATE,
            {
                "title": escape(conversation.title or "Conversation"),
                "subtitle": escape(_subtitle_for(conversation)),
                "stylesheet_url": DEFAULT_STYLESHEET_URL,
                "platform": escape(_display_platform(str(conversation.platform))),
                "generated_date": escape(generated_date),
                "cover_stats": cover_stats,
                "metadata": metadata,
                "toc": toc,
                "body": body,
            },
        )

    def _render_cover_stats(self, conversation: Conversation, generated_date: str) -> str:
        """Render compact cover page stats."""
        items = [
            ("Platform", _display_platform(str(conversation.platform))),
            ("Generated", generated_date),
            ("Total Pages", "Shown in footer"),
            ("Messages", str(len(conversation.messages))),
            ("Theme", "Technical Handbook"),
            ("Generator", "PaperChat"),
        ]
        return "\n".join(render_cover_stat(label, value) for label, value in items)

    def _render_metadata(self, conversation: Conversation, generated_date: str) -> str:
        """Render document metadata."""
        metadata = conversation.metadata
        items = [
            MetadataItem("Document", conversation.title or metadata.title or "Conversation"),
            MetadataItem("Platform", _display_platform(str(conversation.platform))),
            MetadataItem("Generated", generated_date),
            MetadataItem("Messages", str(len(conversation.messages))),
            MetadataItem("Theme", "Technical Handbook"),
            MetadataItem("Source", metadata.source_url),
            MetadataItem("Final URL", metadata.final_url),
        ]
        return "\n".join(
            render_metadata_item(item)
            for item in items
            if item.value
        )

    def _render_message(
        self,
        message: Message,
        index: int,
        headings: list["Heading"],
    ) -> str:
        """Render one conversation message."""
        content = _markdown_to_html(message.plain_text, headings)
        return render_section(
            section_id=message.id,
            label=_role_label(message.role),
            index=index,
            role=_class_token(message.role),
            content=content,
        )

    def _render_toc(self, headings: list["Heading"]) -> str:
        """Render a table of contents."""
        if not headings:
            return '<p class="toc-empty">No document headings were detected.</p>'
        items = "\n".join(render_toc_item(heading) for heading in headings)
        return f"<ol>{items}</ol>"


def _markdown_to_html(markdown: str, headings: list[Heading]) -> str:
    """Convert normalized markdown-like text to semantic HTML."""
    blocks = _split_blocks(markdown)
    html_blocks: list[str] = []
    for block in blocks:
        html_blocks.append(_block_to_html(block, headings))
    return "\n".join(html_blocks)


def _split_blocks(markdown: str) -> list[str]:
    """Split markdown into blocks while keeping fenced code intact."""
    blocks: list[str] = []
    current: list[str] = []
    in_code = False
    for line in markdown.splitlines():
        if line.startswith("```"):
            current.append(line)
            in_code = not in_code
            continue
        if not in_code and not line.strip():
            if current:
                blocks.append("\n".join(current))
                current = []
            continue
        current.append(line)
    if current:
        blocks.append("\n".join(current))
    return blocks


def _block_to_html(block: str, headings: list[Heading]) -> str:
    """Render a markdown block."""
    stripped = block.strip()
    if stripped.startswith("```"):
        return _render_code_block(stripped)
    if _is_heading(stripped):
        return _render_heading(stripped, headings)
    if _is_footnote(stripped):
        return _render_footnote(stripped)
    if _is_table(stripped):
        return _render_table(stripped)
    if _is_list(stripped):
        return _render_list(stripped)
    if stripped.startswith(">"):
        return _render_blockquote(stripped)
    if stripped in {"---", "***", "___"}:
        return '<hr class="page-break" />'
    if stripped == "[[PAGE_BREAK]]":
        return '<div class="page-break"></div>'
    if _is_image(stripped):
        return _render_image(stripped)
    return f"<p>{_render_inline(stripped)}</p>"


def _render_code_block(block: str) -> str:
    """Render fenced code."""
    lines = block.splitlines()
    language = lines[0].removeprefix("```").strip()
    code = "\n".join(lines[1:-1] if len(lines) > 1 else [])
    language_token = _class_token(language) if language else ""
    language_class = f" language-{language_token}" if language_token else ""
    label_text = language or "code"
    label = f'<figcaption>{escape(label_text)}</figcaption>'
    return (
        f'<figure class="code-block{language_class}">'
        f"{label}<pre><code>{escape(code)}</code></pre></figure>"
    )


def _render_heading(block: str, headings: list[Heading]) -> str:
    """Render a heading and register it for the TOC."""
    marker, text = block.split(" ", 1)
    level = min(len(marker), 4)
    anchor = _anchor(text)
    headings.append(Heading(level=level, text=text, anchor=anchor))
    return f'<h{level} id="{anchor}">{_render_inline(text)}</h{level}>'


def _render_table(block: str) -> str:
    """Render a markdown table."""
    rows = [
        [cell.strip() for cell in line.strip().strip("|").split("|")]
        for line in block.splitlines()
        if line.strip()
    ]
    if len(rows) < 2:
        return f"<p>{_render_inline(block)}</p>"

    header = rows[0]
    body = rows[2:] if _is_separator_row(rows[1]) else rows[1:]
    head = "".join(f"<th>{_render_inline(cell)}</th>" for cell in header)
    body_rows = "\n".join(
        "<tr>" + "".join(f"<td>{_render_inline(cell)}</td>" for cell in row) + "</tr>"
        for row in body
    )
    return (
        '<div class="table-wrap"><table>'
        f"<thead><tr>{head}</tr></thead><tbody>{body_rows}</tbody>"
        "</table></div>"
    )


def _render_list(block: str) -> str:
    """Render a markdown list with hierarchy."""
    lines = block.splitlines()
    html, _ = _render_list_lines(lines, 0, 0)
    return html


def _render_list_lines(lines: list[str], start: int, indent: int) -> tuple[str, int]:
    """Render list lines recursively."""
    ordered = _line_is_ordered(lines[start])
    tag = "ol" if ordered else "ul"
    items: list[str] = []
    index = start
    while index < len(lines):
        line_indent = _leading_spaces(lines[index])
        if line_indent < indent:
            break
        if line_indent > indent:
            nested, index = _render_list_lines(lines, index, line_indent)
            if items:
                items[-1] = items[-1].removesuffix("</li>") + nested + "</li>"
            continue

        text = _strip_list_marker(lines[index])
        task = _task_state(text)
        if task is None:
            items.append(f"<li>{_render_inline(text)}</li>")
        else:
            checked, task_text = task
            state = " checked" if checked else ""
            items.append(
                '<li class="task-list-item">'
                f'<input type="checkbox" disabled{state} />'
                f"<span>{_render_inline(task_text)}</span>"
                "</li>"
            )
        index += 1
    return f"<{tag}>{''.join(items)}</{tag}>", index


def _render_blockquote(block: str) -> str:
    """Render a blockquote."""
    text = "\n".join(line.removeprefix(">").strip() for line in block.splitlines())
    return f"<blockquote>{_markdown_to_html(text, [])}</blockquote>"


def _render_image(block: str) -> str:
    """Render image markdown with placeholder support."""
    match = re.match(r"!\[(?P<alt>[^\]]*)\]\((?P<src>[^)]+)\)", block)
    if not match:
        return '<figure class="image-placeholder"><span>Image placeholder</span></figure>'
    alt = match.group("alt")
    src = match.group("src")
    return (
        '<figure class="document-image">'
        f'<img src="{escape(src, quote=True)}" alt="{escape(alt, quote=True)}" />'
        f"<figcaption>{escape(alt) or 'Image'}</figcaption></figure>"
    )


def _render_footnote(block: str) -> str:
    """Render a future-ready footnote block."""
    match = re.match(r"^\[\^(?P<label>[^\]]+)\]:\s*(?P<text>.*)$", block, re.S)
    if not match:
        return f"<p>{_render_inline(block)}</p>"
    return (
        '<aside class="footnote">'
        f'<sup>{escape(match.group("label"))}</sup>'
        f"<p>{_render_inline(match.group('text').strip())}</p>"
        "</aside>"
    )


def _render_inline(text: str) -> str:
    """Render inline markdown safely."""
    escaped = escape(text)
    escaped = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", escaped)
    escaped = re.sub(r"(?<!\*)\*([^*]+)\*(?!\*)", r"<em>\1</em>", escaped)
    escaped = re.sub(r"`([^`]+)`", r"<code>\1</code>", escaped)
    escaped = re.sub(r"!\[([^\]]*)\]\(([^)]+)\)", r'<span class="image-ref">\1</span>', escaped)
    escaped = re.sub(
        r"\[([^\]]+)\]\((https?://[^)]+)\)",
        r'<a href="\2">\1</a>',
        escaped,
    )
    return escaped.replace("\n", "<br />")


def _anchor(text: str) -> str:
    """Create a heading anchor."""
    slug = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return slug or f"section-{uuid4().hex[:8]}"


def _is_heading(block: str) -> bool:
    return bool(re.match(r"^#{1,6}\s+\S", block))


def _is_table(block: str) -> bool:
    lines = block.splitlines()
    return len(lines) >= 2 and "|" in lines[0] and _is_separator_row(
        [cell.strip() for cell in lines[1].strip().strip("|").split("|")]
    )


def _is_separator_row(row: list[str]) -> bool:
    return all(re.match(r"^:?-{3,}:?$", cell) for cell in row)


def _is_list(block: str) -> bool:
    return bool(re.match(r"^\s*(?:[-*+]|\d+\.)\s+", block))


def _line_is_ordered(line: str) -> bool:
    return bool(re.match(r"^\s*\d+\.\s+", line))


def _leading_spaces(line: str) -> int:
    return len(line) - len(line.lstrip(" "))


def _strip_list_marker(line: str) -> str:
    return re.sub(r"^\s*(?:[-*+]|\d+\.)\s+", "", line).strip()


def _is_image(block: str) -> bool:
    return block.startswith("![") or block == "[[IMAGE]]"


def _is_footnote(block: str) -> bool:
    return bool(re.match(r"^\[\^[^\]]+\]:", block))


def _task_state(text: str) -> tuple[bool, str] | None:
    match = re.match(r"^\[(?P<state>[ xX])\]\s+(?P<text>.+)$", text)
    if not match:
        return None
    return match.group("state").lower() == "x", match.group("text")


def _display_platform(platform: str) -> str:
    return platform.replace("_", " ").title()


def _role_label(role: str) -> str:
    labels = {
        "user": "Prompt",
        "assistant": "Response",
        "system": "Context",
        "tool": "Reference",
    }
    return labels.get(role.lower(), role.replace("_", " ").title())


def _class_token(value: str) -> str:
    token = re.sub(r"[^a-z0-9_-]+", "-", value.lower()).strip("-")
    return token or "plain"


def _subtitle_for(conversation: Conversation) -> str:
    if conversation.metadata.title and conversation.metadata.title != conversation.title:
        return conversation.metadata.title
    return "A structured study document generated from an AI conversation"

"""HTML renderer for normalized conversations."""

from datetime import datetime
from html import escape
import re
from uuid import uuid4

from app.domain.conversation import Conversation
from app.domain.message import Message
from app.renderer.base import BaseRenderer
from app.renderer.components import render_section, render_toc_prompt_item
from app.renderer.template_engine import TemplateEngine
from app.renderer.themes import DEFAULT_STYLESHEET_URL, DEFAULT_TEMPLATE
from exceptions import RendererException


class HtmlRenderer(BaseRenderer):
    """Render conversations as professional printable HTML."""

    def __init__(
        self,
        template_engine: TemplateEngine | None = None,
        layout: str = "single",
        font_family: str = "inter",
        font_size: str = "medium",
        line_spacing: str = "normal",
        theme: str = "default",
        show_cover: bool = True,
        page_format: str = "A4",
        margin: str = "normal",
    ) -> None:
        """Initialize the renderer."""
        self._template_engine = template_engine or TemplateEngine()
        self._layout = layout if layout in {"single", "two-column", "auto"} else "single"
        self._font_family = font_family.lower()
        self._font_size = font_size.lower()
        self._line_spacing = line_spacing.lower()
        self._theme = theme.lower()
        self._show_cover = show_cover
        self._page_format = page_format.upper().strip()
        self._margin = margin.lower().strip()

    def render(self, conversation: Conversation) -> str:
        """Render a conversation into a complete HTML document."""
        if not conversation.messages:
            raise RendererException("Conversation must contain at least one message.")

        # Only the user's own prompts count as "questions" and drive the TOC.
        # Assistant responses are never counted or listed separately - they
        # live under the prompt that produced them.
        prompts = [message for message in conversation.messages if _is_user_message(message)]

        body = "\n".join(
            self._render_message(message, index)
            for index, message in enumerate(conversation.messages, start=1)
        )
        generated_date = datetime.now().strftime("%d %B %Y")
        question_count = len(prompts)
        question_word = "question" if question_count == 1 else "questions"
        question_count_str = f"{question_count} {question_word}"
        source_url = conversation.metadata.source_url or conversation.metadata.final_url or ""
        source_url_short = _shorten_url(source_url)
        toc = self._render_toc(prompts)
        summary_line = self._render_summary_line(conversation, len(prompts), generated_date)

        layout_classes = [
            f"layout-{self._layout}",
            f"font-{self._font_family}",
            f"size-{self._font_size}",
            f"spacing-{self._line_spacing}",
            f"theme-{self._theme}",
        ]
        if not self._show_cover:
            layout_classes.append("no-cover")

        page_size_str = "letter portrait" if self._page_format == "LETTER" else ("legal portrait" if self._page_format == "LEGAL" else "A4 portrait")
        page_margin_str = "10mm 10mm 12mm 10mm" if self._margin == "narrow" else ("28mm 24mm 32mm 24mm" if self._margin == "wide" else "18mm 16mm 22mm 16mm")

        return self._template_engine.render(
            DEFAULT_TEMPLATE,
            {
                "title": escape(conversation.title or "Conversation"),
                "subtitle": escape(_subtitle_for(conversation)),
                "stylesheet_url": DEFAULT_STYLESHEET_URL,
                "platform": escape(_display_platform(str(conversation.platform))),
                "generated_date": escape(generated_date),
                "question_count_str": escape(question_count_str),
                "source_url": escape(source_url),
                "source_url_short": escape(source_url_short),
                "layout_class": " ".join(layout_classes),
                "page_size": page_size_str,
                "page_margin": page_margin_str,
                "summary_line": summary_line,
                "toc": toc,
                "body": body,
            },
        )

    def _render_summary_line(self, conversation: Conversation, prompt_count: int, generated_date: str) -> str:
        """Render the single fixed summary line shown on the cover of every PDF.

        This replaces the old multi-row stat grid and metadata card with one
        predefined, consistently-formatted line: platform, question count,
        generation date.
        """
        platform = _display_platform(str(conversation.platform))
        question_word = "question" if prompt_count == 1 else "questions"
        parts = [platform, f"{prompt_count} {question_word}", generated_date]
        return escape(" · ".join(parts))

    def _render_message(self, message: Message, index: int) -> str:
        """Render one conversation message."""
        content = _markdown_to_html(message.plain_text)
        return render_section(
            section_id=message.id,
            label=_role_label(message.role),
            index=index,
            role=_class_token(message.role),
            content=content,
        )

    def _render_toc(self, prompts: list[Message]) -> str:
        """Render a table of contents built from the user's own prompts, in order.

        Rather than pulling every markdown heading out of the model's
        responses (which produced hundreds of noisy sub-entries), the TOC
        is now exactly what the person actually asked: one numbered entry
        per prompt, in the order it was sent, linking to that prompt's
        section in the body.
        """
        if not prompts:
            return '<p class="toc-empty">No prompts were detected in this conversation.</p>'
        items = "\n".join(
            render_toc_prompt_item(index, _toc_label(message.plain_text), message.id)
            for index, message in enumerate(prompts, start=1)
        )
        return f'<ol class="toc-list">{items}</ol>'


def _markdown_to_html(markdown: str) -> str:
    """Convert normalized markdown-like text to semantic HTML."""
    blocks = _split_blocks(markdown)
    return "\n".join(_block_to_html(block) for block in blocks)


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


def _block_to_html(block: str) -> str:
    """Render a markdown block."""
    stripped = block.strip()
    if _is_math_block(stripped):
        return f'<div class="math-block">{escape(stripped)}</div>'
    if stripped.startswith("```"):
        return _render_code_block(stripped)
    if _is_heading(stripped):
        return _render_heading(stripped)
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


def _is_math_block(block: str) -> bool:
    """Return whether a block is a LaTeX display math formula."""
    return (
        (block.startswith("$$") and block.endswith("$$"))
        or (block.startswith("\\[") and block.endswith("\\]"))
        or block.startswith(("\\begin{equation}", "\\begin{align}", "\\begin{gather}"))
    )


def _render_code_block(block: str) -> str:
    """Render fenced code."""
    lines = block.splitlines()
    language = lines[0].removeprefix("```").strip()
    code = "\n".join(lines[1:-1] if len(lines) > 1 else [])
    language_token = _class_token(language) if language else ""
    language_class = f" language-{language_token}" if language_token else ""
    label_text = language or "code"
    label = f'<figcaption>{escape(label_text)}</figcaption>'
    highlighted = _highlight_code(code, language)
    return (
        f'<figure class="code-block{language_class}">'
        f'{label}<pre><code class="highlight">{highlighted}</code></pre></figure>'
    )


def _highlight_code(code: str, language: str) -> str:
    """Syntax-highlight code without letting lexer failures break rendering."""
    try:
        from pygments import highlight
        from pygments.formatters import HtmlFormatter
        from pygments.lexers import TextLexer, get_lexer_by_name
        from pygments.util import ClassNotFound
    except ImportError:
        return escape(code)

    try:
        lexer = get_lexer_by_name(language) if language else TextLexer()
    except (ClassNotFound, ValueError):
        lexer = TextLexer()

    formatter = HtmlFormatter(nowrap=True)
    return highlight(code, lexer, formatter)


def _render_heading(block: str) -> str:
    """Render a heading. No longer registered anywhere for the TOC -
    the TOC is prompt-driven now - but the anchor id is kept so in-body
    deep links still work."""
    marker, text = block.split(" ", 1)
    level = min(len(marker), 4)
    anchor = _anchor(text)
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
    return f"<blockquote>{_markdown_to_html(text)}</blockquote>"


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
    """Render inline markdown safely while preserving LaTeX math formulas."""
    math_placeholders: list[str] = []

    def _preserve_math(match: re.Match[str]) -> str:
        idx = len(math_placeholders)
        math_content = match.group(0)
        math_placeholders.append(f'<span class="math-inline">{escape(math_content)}</span>')
        return f"__PAPERCHAT_MATH_{idx}__"

    # Preserve \( ... \) and $ ... $ inline math formulas
    processed = re.sub(r"\\\((.*?)\\\)", _preserve_math, text, flags=re.DOTALL)
    processed = re.sub(r"(?<!\$)\$([^\$\n]+)\$(?!\$)", _preserve_math, processed)

    escaped = escape(processed)
    escaped = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", escaped)
    escaped = re.sub(r"(?<!\*)\*([^*]+)\*(?!\*)", r"<em>\1</em>", escaped)
    escaped = re.sub(r"`([^`]+)`", r"<code>\1</code>", escaped)
    escaped = re.sub(r"!\[([^\]]*)\]\(([^)]+)\)", r'<span class="image-ref">\1</span>', escaped)
    escaped = re.sub(
        r"\[([^\]]+)\]\((https?://[^)]+)\)",
        r'<a href="\2">\1</a>',
        escaped,
    )

    for idx, placeholder in enumerate(math_placeholders):
        escaped = escaped.replace(f"__PAPERCHAT_MATH_{idx}__", placeholder)

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
    return labels.get(str(role).lower(), str(role).replace("_", " ").title())


def _class_token(value: str) -> str:
    token = re.sub(r"[^a-z0-9_-]+", "-", str(value).lower()).strip("-")
    return token or "plain"


def _is_user_message(message: Message) -> bool:
    """A message counts as one of the person's own questions only if it's
    actually a user turn - not a system/tool message and not the model's
    response to it."""
    return str(message.role).lower() == "user"


def _toc_label(prompt_text: str) -> str:
    """Turn a raw user prompt into a short, clean TOC label.

    Uses exactly what was typed - collapsed to one line and capped in
    length - rather than trying to infer a "nicer" topic title. Keeps the
    TOC honest to what was actually asked, including messy or meta prompts.
    """
    normalized = " ".join(prompt_text.strip().split())
    if not normalized:
        return "Untitled prompt"
    label = normalized[0].upper() + normalized[1:]
    if len(label) > 90:
        label = label[:87].rstrip() + "…"
    return label


def _subtitle_for(conversation: Conversation) -> str:
    if conversation.metadata.title and conversation.metadata.title != conversation.title:
        return conversation.metadata.title
    return "A structured study document generated from an AI conversation"


def _shorten_url(url: str) -> str:
    """Shorten a source URL for the cover page link display."""
    if not url:
        return "Source link"
    clean = url.removeprefix("https://").removeprefix("http://").removeprefix("www.")
    if len(clean) > 34:
        return clean[:31] + "..."
    return clean
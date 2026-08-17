"""Gemini conversation parser."""

from collections.abc import Iterable
from html import escape
import json
from uuid import uuid4

from bs4 import BeautifulSoup, NavigableString, Tag

from app.domain.content_block import ContentBlock
from app.domain.conversation import Conversation
from app.domain.enums import Platform
from app.domain.fetch_result import FetchResult
from app.domain.message import Message
from app.domain.metadata import ConversationMetadata
from app.parsers.base import BaseParser
from exceptions import ParserException


class GeminiParser(BaseParser):
    """Parse Gemini shared conversations from rendered HTML."""

    platform = Platform.GEMINI
    user_selectors = (
        "user-query",
        ".user-query",
        "[data-test-id='user-query']",
        ".query-text",
        "[data-role='user']",
    )
    assistant_selectors = (
        "model-response",
        ".model-response",
        "[data-test-id='model-response']",
        ".response-container",
        ".message-content",
        "[data-role='model']",
        "[data-role='assistant']",
    )

    def parse(self, fetch_result: FetchResult) -> Conversation:
        """Parse a Gemini document into a conversation."""
        soup = BeautifulSoup(fetch_result.html, "html.parser")
        dom_messages = tuple(self._extract_messages(soup))
        embedded_messages = tuple(_extract_messages_from_embedded_data(soup))
        messages = embedded_messages if len(embedded_messages) > len(dom_messages) else dom_messages

        if not messages:
            messages = tuple(self._extract_fallback_messages(soup))

        if not messages:
            raise ParserException("No Gemini messages were found in the fetched HTML.")

        title = _extract_title(soup, fetch_result.title)
        metadata = ConversationMetadata(
            source_url=fetch_result.url,
            final_url=fetch_result.final_url,
            title=title,
            raw_html=fetch_result.html,
            fetch_time_ms=fetch_result.fetch_time_ms,
            extra={"http_status": fetch_result.status},
        )

        return Conversation(
            platform=self.platform,
            title=title,
            messages=messages,
            metadata=metadata,
            raw_html=fetch_result.html,
        )

    def _extract_messages(self, soup: BeautifulSoup) -> Iterable[Message]:
        """Extract user and model messages from Gemini DOM elements."""
        collected_container = soup.select_one('[data-paperchat-collected-messages="true"]')
        search_root = collected_container if isinstance(collected_container, Tag) else soup

        candidates: list[tuple[int, Tag, str]] = []
        for selector in self.user_selectors:
            for tag in search_root.select(selector):
                if isinstance(tag, Tag):
                    candidates.append((_node_offset(tag), tag, "user"))

        for selector in self.assistant_selectors:
            for tag in search_root.select(selector):
                if isinstance(tag, Tag):
                    candidates.append((_node_offset(tag), tag, "assistant"))

        # Sort candidate tags top-to-bottom by DOM position
        candidates.sort(key=lambda item: item[0])

        seen: set[str] = set()
        index = 1

        for _, node, role in candidates:
            # Skip child nodes nested inside already processed parent message containers
            if any(other is not node and node in other.descendants for _, other, _ in candidates):
                continue

            content_node = self._find_content_node(node)
            plain_text = _node_to_markdown(content_node)
            if not plain_text:
                continue

            message_id = _message_id(node, index)
            dedupe_key = f"{role}:{plain_text[:400]}"
            if dedupe_key in seen:
                continue
            seen.add(dedupe_key)

            index += 1
            yield Message(
                id=message_id,
                role=role,
                plain_text=plain_text,
                content_blocks=(ContentBlock(type="markdown", text=plain_text),),
            )

    def _extract_fallback_messages(self, soup: BeautifulSoup) -> Iterable[Message]:
        """Extract conversation messages when Gemini DOM uses non-standard containers."""
        articles = soup.find_all(["article", "section"])
        index = 1
        seen: set[str] = set()

        for article in articles:
            if not isinstance(article, Tag):
                continue
            text = _node_to_markdown(article)
            if not text or len(text) < 5:
                continue
            role = "user" if "user" in article.get("class", []) or "query" in str(article.get("class", [])) else "assistant"
            key = f"{role}:{text[:300]}"
            if key in seen:
                continue
            seen.add(key)
            yield Message(
                id=f"gemini-fallback-{index}",
                role=role,
                plain_text=text,
                content_blocks=(ContentBlock(type="markdown", text=text),),
            )
            index += 1

    def _find_content_node(self, node: Tag) -> Tag:
        """Find inner content container if available."""
        for selector in (".markdown", ".message-content", ".user-select-text", ".query-text", "message-content"):
            child = node.select_one(selector)
            if isinstance(child, Tag):
                return child
        return node


def _node_offset(node: Tag) -> int:
    """Calculate approximate line offset of a tag in DOM."""
    return node.sourceline if node.sourceline is not None else 0


def _extract_title(soup: BeautifulSoup, fallback: str) -> str:
    """Extract page title."""
    if soup.title and soup.title.string:
        clean = soup.title.string.replace("- Gemini", "").replace("Gemini -", "").strip()
        if clean:
            return clean
    heading = soup.select_one("h1, .conversation-title, .title")
    if isinstance(heading, Tag):
        text = heading.get_text(" ", strip=True)
        if text:
            return text
    return fallback.strip()


def _message_id(node: Tag, index: int) -> str:
    """Generate a stable message identifier."""
    for attr in ("id", "data-message-id", "data-id"):
        val = node.get(attr)
        if isinstance(val, str) and val.strip():
            return val.strip()
    return f"gemini-msg-{index}-{uuid4().hex[:8]}"


def _extract_messages_from_embedded_data(soup: BeautifulSoup) -> Iterable[Message]:
    """Extract messages from Gemini inline JSON payloads."""
    messages: list[Message] = []
    seen: set[str] = set()

    for script in soup.find_all("script"):
        if not isinstance(script, Tag):
            continue
        text = script.string or script.get_text()
        if not text or ("AF_initDataCallback" not in text and "window.WIZ_global_data" not in text and not text.strip().startswith("{")):
            continue

        for item in _walk_json_payloads(text):
            if isinstance(item, dict):
                role = _json_role(item)
                text_val = _json_text(item)
                if role and text_val:
                    key = f"{role}:{text_val[:300]}"
                    if key not in seen:
                        seen.add(key)
                        messages.append(
                            Message(
                                id=f"gemini-json-{len(messages)+1}",
                                role=role,
                                plain_text=text_val,
                                content_blocks=(ContentBlock(type="markdown", text=text_val),),
                            )
                        )
    return messages


def _json_role(data: dict[object, object]) -> str | None:
    """Determine role from JSON dict."""
    for key in ("role", "author", "type", "sender"):
        val = data.get(key)
        if isinstance(val, str):
            val_lower = val.lower()
            if "user" in val_lower or "human" in val_lower:
                return "user"
            if "model" in val_lower or "assistant" in val_lower or "gemini" in val_lower or "bot" in val_lower:
                return "assistant"
    return None


def _json_text(data: dict[object, object]) -> str:
    """Extract text from JSON dict."""
    for key in ("text", "content", "parts", "message"):
        val = data.get(key)
        if isinstance(val, str) and val.strip():
            return val.strip()
        if isinstance(val, list):
            parts = [str(p).strip() for p in val if isinstance(p, str) and str(p).strip()]
            if parts:
                return "\n\n".join(parts)
    return ""


def _walk_json_payloads(text: str) -> Iterable[object]:
    """Search text for inline JSON data."""
    start = 0
    while True:
        idx = text.find("{", start)
        if idx == -1:
            break
        end = text.rfind("}")
        if end <= idx:
            break
        snippet = text[idx : end + 1]
        try:
            parsed = json.loads(snippet)
            yield from _walk_obj(parsed)
            break
        except Exception:
            start = idx + 1


def _walk_obj(obj: object, depth: int = 0, max_depth: int = 25) -> Iterable[object]:
    """Recursively walk nested JSON structure with recursion depth limit."""
    if depth > max_depth:
        return
    yield obj
    if isinstance(obj, dict):
        for v in obj.values():
            yield from _walk_obj(v, depth + 1, max_depth)
    elif isinstance(obj, list):
        for elem in obj:
            yield from _walk_obj(elem, depth + 1, max_depth)


def _node_to_markdown(node: Tag) -> str:
    """Convert HTML node tree into clean Markdown."""
    parts = [_child_to_markdown(child, list_depth=0) for child in node.children]
    return _join_blocks(parts)


def _child_to_markdown(node: Tag | NavigableString, list_depth: int) -> str:
    """Convert child node to Markdown."""
    if isinstance(node, NavigableString):
        return str(node)
    if not isinstance(node, Tag):
        return ""

    classes = set(node.get("class", []) if isinstance(node.get("class"), list) else [])
    if "katex-html" in classes:
        return ""

    math = _extract_latex_math(node)
    if math is not None:
        return math

    name = node.name.lower()
    if name in {"script", "style", "svg", "button"}:
        return ""
    if name in {"h1", "h2", "h3", "h4", "h5", "h6"}:
        level = int(name[1])
        return f"{'#' * level} {_inline_text(node)}"
    if name == "p":
        return _inline_text(node)
    if name == "br":
        return "\n"
    if name == "pre":
        return _code_block(node)
    if name == "code":
        return f"`{node.get_text()}`"
    if name in {"ul", "ol"}:
        return _list_to_markdown(node, ordered=name == "ol", list_depth=list_depth)
    if name == "table":
        return _table_to_markdown(node)
    if name == "blockquote":
        text = _join_blocks(_child_to_markdown(child, list_depth) for child in node.children)
        return "\n".join(f"> {line}" if line else ">" for line in text.split("\n"))
    if name == "a":
        label = _inline_text(node)
        href = node.get("href")
        if isinstance(href, str) and href.strip() and label:
            return f"[{label}]({href.strip()})"
        return label

    return _join_blocks(_child_to_markdown(child, list_depth) for child in node.children)


def _inline_text(node: Tag) -> str:
    """Extract inline text while preserving formatting, code, links, and math."""
    parts: list[str] = []
    for child in node.children:
        if isinstance(child, NavigableString):
            parts.append(str(child))
        elif isinstance(child, Tag):
            classes = set(child.get("class", []) if isinstance(child.get("class"), list) else [])
            if "katex-html" in classes:
                continue

            math = _extract_latex_math(child)
            if math is not None:
                parts.append(f" {math} ")
                continue

            name = child.name.lower()
            if name in {"strong", "b"}:
                parts.append(f" **{_inline_text(child).strip()}** ")
            elif name in {"em", "i"}:
                parts.append(f" *{_inline_text(child).strip()}* ")
            elif name in {"del", "s", "strike"}:
                parts.append(f" ~~{_inline_text(child).strip()}~~ ")
            elif name == "code":
                parts.append(f" `{child.get_text()}` ")
            elif name == "br":
                parts.append("\n")
            elif name == "a":
                label = _inline_text(child).strip()
                href = child.get("href")
                if isinstance(href, str) and href.strip() and label:
                    parts.append(f" [{label}]({href.strip()}) ")
                else:
                    parts.append(f" {label} ")
            elif name == "img":
                alt = child.get("alt", "Image")
                src = child.get("src", "")
                parts.append(f"\n\n![{alt}]({src})\n\n")
            elif name == "hr":
                parts.append("\n\n---\n\n")
            else:
                parts.append(_inline_text(child))
    return " ".join(" ".join(parts).split())


def _code_block(node: Tag) -> str:
    """Convert pre tags into code blocks without token corruption."""
    code = node.find("code")
    language = _language_from_code(code) if isinstance(code, Tag) else ""
    text = code.get_text() if isinstance(code, Tag) else node.get_text()
    return f"```{language}\n{text.strip()}\n```"


def _language_from_code(code: Tag) -> str:
    """Extract code block language."""
    classes = code.get("class", [])
    if not isinstance(classes, list):
        return ""
    for class_name in classes:
        if isinstance(class_name, str) and class_name.startswith("language-"):
            return class_name.removeprefix("language-")
    return ""


def _list_to_markdown(node: Tag, ordered: bool, list_depth: int) -> str:
    """Convert list element to Markdown."""
    lines: list[str] = []
    index = 1
    for child in node.children:
        if isinstance(child, Tag) and child.name.lower() == "li":
            marker = f"{index}." if ordered else "-"
            prefix = "  " * list_depth + marker
            item_text = _node_to_markdown(child)
            if item_text:
                lines.append(f"{prefix} {item_text}")
            index += 1
    return "\n".join(lines)


def _table_to_markdown(node: Tag) -> str:
    """Convert HTML table to Markdown table."""
    rows = [
        [_inline_text(cell) for cell in row.find_all(["th", "td"], recursive=False)]
        for row in node.find_all("tr")
    ]
    rows = [row for row in rows if row]
    if not rows:
        return ""

    header = rows[0]
    separator = ["---"] * len(header)
    body = rows[1:]
    lines = [_markdown_row(header), _markdown_row(separator)]
    lines.extend(_markdown_row(row) for row in body)
    return "\n".join(lines)


def _markdown_row(values: list[str]) -> str:
    """Format row cells."""
    escaped_values = [escape(value, quote=False).replace("|", "\\|") for value in values]
    return f"| {' | '.join(escaped_values)} |"


def _extract_latex_math(node: Tag) -> str | None:
    """Extract LaTeX math formulas."""
    annotation = node.find("annotation", attrs={"encoding": "application/x-tex"})
    if isinstance(annotation, Tag) and annotation.string:
        tex = annotation.string.strip()
        classes = set(node.get("class", []) if isinstance(node.get("class"), list) else [])
        if "katex-display" in classes or "math-display" in classes or node.name == "div":
            return f"\n\n$$ {tex} $$\n\n"
        return f" $ {tex} $ "

    for attr in ("data-formula", "data-tex", "data-math"):
        val = node.get(attr)
        if isinstance(val, str) and val.strip():
            tex = val.strip()
            return f" $ {tex} $ "

    return None


def _join_blocks(parts: Iterable[str]) -> str:
    """Join block parts into clean markdown string."""
    cleaned = [part.strip() for part in parts if part and part.strip()]
    return "\n\n".join(cleaned)

"""ChatGPT conversation parser."""

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


class ChatGPTParser(BaseParser):
    """Parse ChatGPT shared conversations from rendered HTML."""

    platform = Platform.CHATGPT
    message_selector = "[data-message-author-role]"
    content_selectors = (
        ".markdown",
        "[data-message-content]",
        ".whitespace-pre-wrap",
    )

    def parse(self, fetch_result: FetchResult) -> Conversation:
        """Parse a ChatGPT document into a conversation."""
        soup = BeautifulSoup(fetch_result.html, "html.parser")
        dom_messages = tuple(self._extract_messages(soup))
        embedded_messages = tuple(_extract_messages_from_embedded_data(soup))
        messages = embedded_messages if len(embedded_messages) > len(dom_messages) else dom_messages
        if not messages:
            raise ParserException("No ChatGPT messages were found in the fetched HTML.")

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
        """Extract messages using ChatGPT semantic role attributes."""
        seen: set[str] = set()
        for index, node in enumerate(self._message_nodes(soup), start=1):
            if not isinstance(node, Tag):
                continue

            role = self._normalize_role(node.get("data-message-author-role"))
            if role is None:
                continue

            content_node = self._find_content_node(node)
            plain_text = _node_to_markdown(content_node)
            if not plain_text:
                continue

            message_id = _message_id(node, index)
            dedupe_key = _dedupe_key(node=node, role=role, plain_text=plain_text)
            if dedupe_key in seen:
                continue
            seen.add(dedupe_key)

            yield Message(
                id=message_id,
                role=role,
                plain_text=plain_text,
                content_blocks=(ContentBlock(type="markdown", text=plain_text),),
            )

    def _message_nodes(self, soup: BeautifulSoup) -> list[Tag]:
        """Return message nodes, preferring ordered scroll-collected snapshots."""
        collected_selector = (
            f'[data-paperchat-collected-messages="true"] {self.message_selector}'
        )
        collected = [node for node in soup.select(collected_selector) if isinstance(node, Tag)]
        if collected:
            return collected
        return [node for node in soup.select(self.message_selector) if isinstance(node, Tag)]

    def _find_content_node(self, node: Tag) -> Tag:
        """Find the semantic content container for a ChatGPT message."""
        for selector in self.content_selectors:
            content_node = node.select_one(selector)
            if isinstance(content_node, Tag):
                return content_node
        return node

    def _normalize_role(self, role: object) -> str | None:
        """Normalize ChatGPT role labels."""
        if not isinstance(role, str):
            return None
        normalized = role.strip().lower()
        if normalized in {"user", "assistant", "system"}:
            return normalized
        return None


def _extract_title(soup: BeautifulSoup, fallback: str) -> str:
    """Extract a document title."""
    if soup.title and soup.title.string:
        return soup.title.string.strip()
    heading = soup.select_one("h1")
    if isinstance(heading, Tag):
        return heading.get_text(" ", strip=True)
    return fallback.strip()


def _message_id(node: Tag, index: int) -> str:
    """Return a stable message id when one exists."""
    for attribute in ("data-message-id", "data-testid", "id"):
        value = node.get(attribute)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return f"message-{index}-{uuid4().hex[:8]}"


def _dedupe_key(node: Tag, role: str, plain_text: str) -> str:
    """Create a stable key for duplicate virtualized message nodes."""
    for attribute in ("data-message-id", "data-testid", "id"):
        value = node.get(attribute)
        if isinstance(value, str) and value.strip():
            return f"id:{value.strip()}"
    normalized_text = " ".join(plain_text.split())
    return f"text:{role}:{normalized_text[:500]}"


def _extract_latex_math(node: Tag) -> str | None:
    """Extract raw TeX from KaTeX / MathJax DOM nodes if present."""
    classes = set(node.get("class", []) if isinstance(node.get("class"), list) else [])

    # Check for KaTeX annotation tag (contains clean raw TeX source)
    annotation = node.find("annotation", attrs={"encoding": "application/x-tex"})
    if isinstance(annotation, Tag) and annotation.string:
        tex = annotation.string.strip()
        if "katex-display" in classes or "math-display" in classes or node.name == "div":
            return f"\n\n$$ {tex} $$\n\n"
        return f" $ {tex} $ "

    # Check for MathJax or data-formula / data-tex attribute
    for attr in ("data-formula", "data-tex", "data-math"):
        val = node.get(attr)
        if isinstance(val, str) and val.strip():
            tex = val.strip()
            if "katex-display" in classes or "math-display" in classes or node.name == "div":
                return f"\n\n$$ {tex} $$\n\n"
            return f" $ {tex} $ "

    return None


def _node_to_markdown(node: Tag) -> str:
    """Convert semantic HTML content to markdown-like text."""
    parts = [_child_to_markdown(child, list_depth=0) for child in node.children]
    return _join_blocks(parts)


def _child_to_markdown(node: Tag | NavigableString, list_depth: int) -> str:
    """Convert a DOM node to markdown-like text."""
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
    """Extract inline text from a node while preserving inline code and links."""
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
                parts.append(math)
                continue

            name = child.name.lower()
            if name == "code":
                parts.append(f"`{child.get_text()}`")
            elif name == "br":
                parts.append("\n")
            elif name == "a":
                label = _inline_text(child)
                href = child.get("href")
                if isinstance(href, str) and href.strip() and label:
                    parts.append(f"[{label}]({href.strip()})")
                else:
                    parts.append(label)
            else:
                parts.append(_inline_text(child))
    return " ".join("".join(parts).split())


def _code_block(node: Tag) -> str:
    """Convert a preformatted block to fenced markdown."""
    code = node.find("code")
    language = _language_from_code(code) if isinstance(code, Tag) else ""
    text = code.get_text("\n") if isinstance(code, Tag) else node.get_text("\n")
    return f"```{language}\n{text.strip()}\n```"


def _language_from_code(code: Tag) -> str:
    """Extract a code block language from semantic class names."""
    classes = code.get("class", [])
    if not isinstance(classes, list):
        return ""
    for class_name in classes:
        if isinstance(class_name, str) and class_name.startswith("language-"):
            return class_name.removeprefix("language-")
    return ""


def _list_to_markdown(node: Tag, ordered: bool, list_depth: int) -> str:
    """Convert a list while preserving hierarchy."""
    lines: list[str] = []
    index = 1
    for item in _direct_children(node, "li"):
        marker = f"{index}." if ordered else "-"
        prefix = "  " * list_depth + marker
        item_lines = _list_item_lines(item, list_depth)
        if item_lines:
            lines.append(f"{prefix} {item_lines[0]}")
            lines.extend(item_lines[1:])
        index += 1
    return "\n".join(lines)


def _list_item_lines(item: Tag, list_depth: int) -> list[str]:
    """Convert one list item into markdown lines."""
    parts: list[str] = []
    inline_parts: list[str] = []
    for child in item.children:
        if isinstance(child, Tag) and child.name.lower() in {"ul", "ol"}:
            if inline_parts:
                parts.append(" ".join("".join(inline_parts).split()))
                inline_parts = []
            parts.append(
                _list_to_markdown(
                    child,
                    ordered=child.name.lower() == "ol",
                    list_depth=list_depth + 1,
                )
            )
        elif isinstance(child, NavigableString):
            inline_parts.append(str(child))
        elif isinstance(child, Tag):
            inline_parts.append(_child_to_markdown(child, list_depth))
    if inline_parts:
        parts.insert(0, " ".join("".join(inline_parts).split()))
    return [line for part in parts for line in part.split("\n") if line.strip()]


def _table_to_markdown(node: Tag) -> str:
    """Convert a table to markdown."""
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
    """Build one markdown table row."""
    escaped_values = [escape(value, quote=False).replace("|", "\\|") for value in values]
    return f"| {' | '.join(escaped_values)} |"


def _extract_messages_from_embedded_data(soup: BeautifulSoup) -> Iterable[Message]:
    """Extract messages from ChatGPT app JSON when the DOM is virtualized."""
    for payload in _json_script_payloads(soup):
        for item in _walk_json(payload):
            if isinstance(item, dict) and "mapping" in item and isinstance(item["mapping"], dict):
                mapping_messages = _extract_messages_from_mapping(item["mapping"])
                if mapping_messages:
                    return mapping_messages

    candidates: list[tuple[float, int, Message]] = []
    seen: set[str] = set()
    order = 0

    for payload in _json_script_payloads(soup):
        for item in _walk_json(payload):
            if not isinstance(item, dict):
                continue

            message_data = item.get("message") if isinstance(item.get("message"), dict) else item
            if not isinstance(message_data, dict):
                continue

            role = _json_message_role(message_data)
            if role is None:
                continue

            plain_text = _json_message_text(message_data)
            if not plain_text:
                continue

            message_id = _json_message_id(message_data, fallback=f"embedded-{order + 1}")
            key = f"{message_id}:{role}:{plain_text[:240]}"
            if key in seen:
                continue
            seen.add(key)

            created_at = _json_message_time(message_data)
            order += 1
            candidates.append(
                (
                    created_at if created_at is not None else float(order),
                    order,
                    Message(
                        id=message_id,
                        role=role,
                        plain_text=plain_text,
                        content_blocks=(ContentBlock(type="markdown", text=plain_text),),
                    ),
                )
            )

    candidates.sort(key=lambda candidate: (candidate[0], candidate[1]))
    return [candidate[2] for candidate in candidates]


def _extract_messages_from_mapping(mapping: dict[object, object]) -> list[Message]:
    """Reconstruct a linear conversation from ChatGPT mapping tree in top-to-bottom order."""
    if not isinstance(mapping, dict):
        return []

    nodes_by_id: dict[str, dict[object, object]] = {}
    child_to_parent: dict[str, str] = {}
    parent_to_children: dict[str, list[str]] = {}

    for node_id, node in mapping.items():
        if isinstance(node_id, str) and isinstance(node, dict):
            nodes_by_id[node_id] = node
            parent_id = node.get("parent")
            if isinstance(parent_id, str):
                child_to_parent[node_id] = parent_id
            children = node.get("children")
            if isinstance(children, list):
                parent_to_children[node_id] = [c for c in children if isinstance(c, str)]

    roots = [
        node_id for node_id in nodes_by_id
        if node_id not in child_to_parent or child_to_parent[node_id] not in nodes_by_id
    ]

    ordered_nodes: list[dict[object, object]] = []
    visited: set[str] = set()

    for root_id in roots:
        curr: str | None = root_id
        while curr and curr in nodes_by_id and curr not in visited:
            visited.add(curr)
            node = nodes_by_id[curr]
            ordered_nodes.append(node)
            children = parent_to_children.get(curr, [])
            curr = children[0] if children else None

    messages: list[Message] = []
    seen: set[str] = set()
    for index, node in enumerate(ordered_nodes, start=1):
        message_data = node.get("message") if isinstance(node.get("message"), dict) else node
        if not isinstance(message_data, dict):
            continue

        role = _json_message_role(message_data)
        if role is None:
            continue

        plain_text = _json_message_text(message_data)
        if not plain_text:
            continue

        message_id = _json_message_id(message_data, fallback=f"embedded-{index}")
        key = f"{message_id}:{role}:{plain_text[:240]}"
        if key in seen:
            continue
        seen.add(key)

        messages.append(
            Message(
                id=message_id,
                role=role,
                plain_text=plain_text,
                content_blocks=(ContentBlock(type="markdown", text=plain_text),),
            )
        )

    return messages


def _json_script_payloads(soup: BeautifulSoup) -> Iterable[object]:
    """Yield parseable JSON payloads from script tags."""
    for script in soup.find_all("script"):
        if not isinstance(script, Tag):
            continue

        script_type = script.get("type")
        text = script.string or script.get_text()
        if not text:
            continue

        stripped = text.strip()
        if script_type != "application/json" and not stripped.startswith(("{", "[")):
            continue

        try:
            yield json.loads(stripped)
        except json.JSONDecodeError:
            continue


def _walk_json(value: object) -> Iterable[object]:
    """Walk JSON objects depth-first."""
    yield value
    if isinstance(value, dict):
        for child in value.values():
            yield from _walk_json(child)
    elif isinstance(value, list):
        for child in value:
            yield from _walk_json(child)


def _json_message_role(message_data: dict[object, object]) -> str | None:
    """Extract a supported role from a ChatGPT JSON message."""
    author = message_data.get("author")
    role = author.get("role") if isinstance(author, dict) else message_data.get("role")
    if not isinstance(role, str):
        return None
    normalized = role.strip().lower()
    if normalized in {"user", "assistant", "system"}:
        return normalized
    return None


def _json_message_text(message_data: dict[object, object]) -> str:
    """Extract markdown-like text from a ChatGPT JSON message."""
    content = message_data.get("content")
    if not isinstance(content, dict):
        return ""

    parts = content.get("parts")
    if isinstance(parts, list):
        text_parts = [_json_part_text(part) for part in parts]
        return _join_blocks(text_parts)

    text = content.get("text")
    if isinstance(text, str):
        return text.strip()

    return ""


def _json_part_text(part: object) -> str:
    """Extract text from one ChatGPT JSON content part."""
    if isinstance(part, str):
        return part.strip()
    if not isinstance(part, dict):
        return ""

    for key in ("text", "content", "transcript"):
        value = part.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()

    return ""


def _json_message_id(message_data: dict[object, object], fallback: str) -> str:
    """Extract a message id from embedded JSON."""
    for key in ("id", "message_id"):
        value = message_data.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return fallback


def _json_message_time(message_data: dict[object, object]) -> float | None:
    """Extract creation time for chronological sorting."""
    for key in ("create_time", "update_time"):
        value = message_data.get(key)
        if isinstance(value, int | float):
            return float(value)
    return None


def _direct_children(node: Tag, name: str) -> Iterable[Tag]:
    """Yield direct child tags with a given name."""
    for child in node.children:
        if isinstance(child, Tag) and child.name.lower() == name:
            yield child


def _join_blocks(parts: Iterable[str]) -> str:
    """Join markdown block parts."""
    cleaned = [part.strip() for part in parts if part and part.strip()]
    return "\n\n".join(cleaned)

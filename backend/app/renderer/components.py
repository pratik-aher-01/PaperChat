"""Reusable HTML components for rendered documents."""

from html import escape


def render_toc_prompt_item(index: int, label: str, anchor: str) -> str:
    """Render one numbered table-of-contents entry for a user prompt.

    Each entry corresponds to one user prompt in the conversation, in the
    order it was asked, and links straight to that prompt's section in the
    document body.
    """
    return (
        '<li class="toc-item">'
        f'<a href="#{escape(anchor, quote=True)}">'
        f'<span class="toc-index">{index}.</span>'
        f'<span class="toc-title">{escape(label)}</span>'
        '<span class="toc-leader"></span>'
        '<span class="toc-page" aria-hidden="true"></span>'
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
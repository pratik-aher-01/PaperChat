"""Tiny template engine for renderer-owned templates."""

from pathlib import Path

from exceptions import RendererException


class TemplateEngine:
    """Load and render simple placeholder templates."""

    def render(self, template_path: Path, context: dict[str, str]) -> str:
        """Render a template by replacing named placeholders."""
        try:
            template = template_path.read_text(encoding="utf-8")
        except OSError as exc:
            raise RendererException(f"Template could not be loaded: {template_path}") from exc

        for key, value in context.items():
            template = template.replace(f"{{{{ {key} }}}}", value)
        return template

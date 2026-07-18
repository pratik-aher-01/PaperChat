"""Renderer theme constants."""

from pathlib import Path

RENDERER_DIR = Path(__file__).resolve().parent
TEMPLATE_DIR = RENDERER_DIR / "templates"
ASSET_DIR = RENDERER_DIR / "assets"
DEFAULT_TEMPLATE = TEMPLATE_DIR / "default.html"
DEFAULT_STYLESHEET_URL = "/static/render/styles.css"
DEFAULT_STYLESHEET_PATH = ASSET_DIR / "styles.css"

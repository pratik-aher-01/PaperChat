"""FastAPI application factory for PaperChat."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.exporter import router as exporter_router
from app.api.importer import router as importer_router
from app.api.renderer import router as renderer_router
from app.api.routes import router as api_router
from app.renderer.themes import ASSET_DIR
from config import API_DESCRIPTION, API_TITLE
from logger import logger
from settings import settings


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Handle application startup and shutdown events."""
    logger.info("%s startup complete", app.title)
    yield
    logger.info("%s shutdown complete", app.title)


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title=API_TITLE,
        version=settings.app_version,
        description=API_DESCRIPTION,
        debug=settings.debug,
        lifespan=lifespan,
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=list(settings.cors_origins),
        allow_credentials=False,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["*"],
        expose_headers=["Content-Disposition"],
    )
    app.mount("/static/render", StaticFiles(directory=ASSET_DIR), name="render-static")
    app.include_router(api_router)
    app.include_router(importer_router)
    app.include_router(renderer_router)
    app.include_router(exporter_router)
    return app


app = create_app()

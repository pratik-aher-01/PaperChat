"""Base API routes for PaperChat."""

from typing import TypedDict

from fastapi import APIRouter

from settings import settings


class RootResponse(TypedDict):
    """Response payload for the root endpoint."""

    name: str
    version: str
    status: str


class HealthResponse(TypedDict):
    """Response payload for the health endpoint."""

    status: str


router = APIRouter()


@router.get("/", response_model=None)
def root() -> RootResponse:
    """Return basic API metadata."""
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "status": "running",
    }


@router.get("/health", response_model=None)
def health() -> HealthResponse:
    """Return service health status."""
    return {"status": "healthy"}

"""Logging configuration for PaperChat."""

import logging

from settings import settings

LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def create_logger(name: str = "paperchat") -> logging.Logger:
    """Create a reusable application logger."""
    app_logger = logging.getLogger(name)
    app_logger.setLevel(settings.log_level.upper())
    app_logger.propagate = False

    if not app_logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter(LOG_FORMAT, datefmt=DATE_FORMAT))
        app_logger.addHandler(handler)

    return app_logger


logger = create_logger()

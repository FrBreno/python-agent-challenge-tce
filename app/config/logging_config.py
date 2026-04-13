"""Logging setup for console output with dynamic log level."""

import logging
import logging.config

from app.config.settings import settings


def setup_logging() -> None:
    """Configure application logging with console handler only."""

    logging.config.dictConfig(
        {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "default": {
                    "format": "%(asctime)s | %(levelname)s | %(name)s | %(message)s",
                }
            },
            "handlers": {
                "console": {
                    "class": "logging.StreamHandler",
                    "formatter": "default",
                    "level": settings.log_level.upper(),
                },
            },
            "root": {
                "handlers": ["console"],
                "level": settings.log_level.upper(),
            },
        }
    )

    logging.getLogger(__name__).info(
        "Logging configured with level=%s",
        settings.log_level.upper(),
    )

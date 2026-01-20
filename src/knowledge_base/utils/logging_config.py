"""
Structured logging configuration
"""

import logging
import logging.config
import sys
from datetime import datetime
from typing import Any

import structlog

shared_processors = [
    structlog.contextvars.merge_contextvars,
    structlog.processors.add_log_level,
    structlog.processors.StackInfoRenderer(),
    structlog.dev.set_exc_info,
    structlog.processors.TimeStamper(fmt="iso"),
    structlog.processors.JSONRenderer(),
]


def configure_logging(log_level: str = "INFO") -> None:
    """Configure structured logging with JSON format."""
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, log_level.upper()),
    )

    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer(),
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    """Get a structured logger."""
    return structlog.get_logger(name)


def log_request(
    logger: structlog.stdlib.BoundLogger,
    request_id: str,
    method: str,
    path: str,
    status_code: int,
    duration_ms: float,
    **kwargs: Any,
) -> None:
    """Log an HTTP request."""
    logger.info(
        "http_request",
        request_id=request_id,
        method=method,
        path=path,
        status_code=status_code,
        duration_ms=duration_ms,
        **kwargs,
    )


def log_error(
    logger: structlog.stdlib.BoundLogger,
    request_id: str,
    error: Exception,
    **kwargs: Any,
) -> None:
    """Log an error with context."""
    logger.error(
        "error",
        request_id=request_id,
        error_type=type(error).__name__,
        error_message=str(error),
        **kwargs,
    )

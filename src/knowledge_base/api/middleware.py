"""
Global exception handlers for API routes
"""

import logging
import uuid

from fastapi import Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from psycopg import Error as PostgresError

from knowledge_base.utils.errors import (
    ConfigurationError,
    KnowledgeBaseError,
    LLMError,
    ValidationError,
)

logger = logging.getLogger(__name__)


def knowledge_base_exception_handler(
    request: Request, exc: KnowledgeBaseError
) -> JSONResponse:
    """Handle all custom KnowledgeBaseError exceptions."""
    request_id = str(uuid.uuid4())
    error_dict = exc.to_dict()
    error_dict["request_id"] = request_id

    logger.error(
        f"Request {request_id} failed: {exc.__class__.__name__}: {exc.message}",
        extra={"request_id": request_id, "details": exc.details},
    )

    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    if isinstance(exc, ValidationError):
        status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
    elif isinstance(exc, ConfigurationError):
        status_code = status.HTTP_500_INTERNAL_SERVER_ERROR

    return JSONResponse(
        status_code=status_code,
        content=error_dict,
    )


def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """Handle FastAPI validation errors."""
    request_id = str(uuid.uuid4())

    logger.warning(
        f"Request {request_id} validation failed: {exc.errors()}",
        extra={"request_id": request_id, "errors": exc.errors()},
    )

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": "ValidationError",
            "message": "Request validation failed",
            "details": exc.errors(),
            "request_id": request_id,
        },
    )


def database_exception_handler(request: Request, exc: PostgresError) -> JSONResponse:
    """Handle database errors."""
    request_id = str(uuid.uuid4())

    logger.error(
        f"Request {request_id} database error: {str(exc)}",
        extra={"request_id": request_id},
        exc_info=True,
    )

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "DatabaseError",
            "message": "Database operation failed",
            "details": {"error": str(exc)},
            "request_id": request_id,
        },
    )


def llm_exception_handler(request: Request, exc: LLMError) -> JSONResponse:
    """Handle LLM API errors."""
    request_id = str(uuid.uuid4())
    error_dict = exc.to_dict()
    error_dict["request_id"] = request_id

    logger.error(
        f"Request {request_id} LLM error: {exc.message}",
        extra={"request_id": request_id, "model": exc.details.get("model")},
    )

    return JSONResponse(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        content=error_dict,
    )


def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle unexpected errors."""
    request_id = str(uuid.uuid4())

    logger.error(
        f"Request {request_id} unexpected error: {str(exc)}",
        extra={"request_id": request_id},
        exc_info=True,
    )

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "InternalServerError",
            "message": "An unexpected error occurred",
            "details": {"error": str(exc)} if str(exc) else None,
            "request_id": request_id,
        },
    )

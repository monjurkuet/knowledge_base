"""
Custom exception hierarchy for the Knowledge Base system.
Provides meaningful error types and context for better error handling.
"""

from typing import Any


class KnowledgeBaseError(Exception):
    """Base exception for all knowledge base errors."""

    def __init__(self, message: str, details: dict[str, Any] | None = None):
        self.message = message
        self.details = details or {}
        super().__init__(message)

    @property
    def error_type(self) -> str:
        """Return the error type name"""
        return self.__class__.__name__

    def to_dict(self) -> dict[str, Any]:
        """Convert exception to dictionary for API responses."""
        return {
            "error": self.__class__.__name__,
            "message": self.message,
            "details": self.details,
        }


class DatabaseError(KnowledgeBaseError):
    """Database operation errors."""

    def __init__(
        self,
        message: str,
        query: str | None = None,
        details: dict[str, Any] | None = None,
    ):
        full_details = details or {}
        if query:
            full_details["query"] = query
        super().__init__(message, full_details)


class LLMError(KnowledgeBaseError):
    """Errors from LLM API calls."""

    def __init__(
        self,
        message: str,
        model: str | None = None,
        provider: str | None = None,
        details: dict[str, Any] | None = None,
    ):
        full_details = details or {}
        if model:
            full_details["model"] = model
        if provider:
            full_details["provider"] = provider
        super().__init__(message, full_details)


class IngestionError(KnowledgeBaseError):
    """Errors during document ingestion."""

    def __init__(
        self,
        message: str,
        file_path: str | None = None,
        stage: str | None = None,
        details: dict[str, Any] | None = None,
    ):
        full_details = details or {}
        if file_path:
            full_details["file_path"] = file_path
        if stage:
            full_details["stage"] = stage
        super().__init__(message, full_details)


class ResolutionError(KnowledgeBaseError):
    """Errors during entity resolution."""

    def __init__(
        self,
        message: str,
        entity_name: str | None = None,
        details: dict[str, Any] | None = None,
    ):
        full_details = details or {}
        if entity_name:
            full_details["entity_name"] = entity_name
        super().__init__(message, full_details)


class ValidationError(KnowledgeBaseError):
    """Input validation errors."""

    def __init__(
        self,
        message: str,
        field: str | None = None,
        value: Any = None,
        details: dict[str, Any] | None = None,
    ):
        full_details = details or {}
        if field:
            full_details["field"] = field
        if value is not None:
            full_details["value"] = str(value)
        super().__init__(message, full_details)


class ConfigurationError(KnowledgeBaseError):
    """Configuration-related errors."""

    def __init__(
        self,
        message: str,
        config_key: str | None = None,
        details: dict[str, Any] | None = None,
    ):
        full_details = details or {}
        if config_key:
            full_details["config_key"] = config_key
        super().__init__(message, full_details)


class CommunityDetectionError(KnowledgeBaseError):
    """Errors during community detection."""

    def __init__(
        self,
        message: str,
        graph_size: int | None = None,
        details: dict[str, Any] | None = None,
    ):
        full_details = details or {}
        if graph_size is not None:
            full_details["graph_size"] = graph_size
        super().__init__(message, full_details)


class SummarizationError(KnowledgeBaseError):
    """Errors during community summarization."""

    def __init__(
        self,
        message: str,
        community_id: str | None = None,
        level: int | None = None,
        details: dict[str, Any] | None = None,
    ):
        full_details = details or {}
        if community_id:
            full_details["community_id"] = community_id
        if level is not None:
            full_details["level"] = level
        super().__init__(message, full_details)


class DomainError(KnowledgeBaseError):
    """Domain-related errors."""

    def __init__(
        self,
        message: str,
        domain_id: str | None = None,
        domain_name: str | None = None,
        details: dict[str, Any] | None = None,
    ):
        full_details = details or {}
        if domain_id:
            full_details["domain_id"] = domain_id
        if domain_name:
            full_details["domain_name"] = domain_name
        super().__init__(message, full_details)

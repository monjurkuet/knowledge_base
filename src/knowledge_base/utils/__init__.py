"""
Shared utilities for the Knowledge Base system.
"""

from .db import BaseRepository, DatabaseConnection, QueryBuilder, execute_transaction
from .decorators import handle_errors, log_errors, retry, validate_args
from .errors import (
    CommunityDetectionError,
    ConfigurationError,
    DatabaseError,
    DomainError,
    IngestionError,
    KnowledgeBaseError,
    LLMError,
    ResolutionError,
    SummarizationError,
    ValidationError,
)
from .llm import (
    clean_llm_response,
    extract_json_from_llm_response,
    safe_json_loads,
    validate_json_structure,
)

__all__ = [
    # Database utilities
    "BaseRepository",
    "DatabaseConnection",
    "QueryBuilder",
    "execute_transaction",
    # LLM utilities
    "extract_json_from_llm_response",
    "clean_llm_response",
    "validate_json_structure",
    "safe_json_loads",
    # Exceptions
    "KnowledgeBaseError",
    "DatabaseError",
    "LLMError",
    "IngestionError",
    "ResolutionError",
    "ValidationError",
    "ConfigurationError",
    "CommunityDetectionError",
    "SummarizationError",
    "DomainError",
    # Decorators
    "log_errors",
    "handle_errors",
    "retry",
    "validate_args",
]

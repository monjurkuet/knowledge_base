"""
Domain management module for multi-domain knowledge base.
"""

from .models import (
    AnalysisConfig,
    DomainCreate,
    DomainResponse,
    DomainTemplate,
    DomainUpdate,
    EntityTypeTemplate,
    ExtractionConfig,
    RelationshipTypeTemplate,
    UIConfig,
)
from .service import DomainManager

__all__ = [
    # Models
    "DomainTemplate",
    "EntityTypeTemplate",
    "RelationshipTypeTemplate",
    "ExtractionConfig",
    "UIConfig",
    "AnalysisConfig",
    "DomainCreate",
    "DomainResponse",
    "DomainUpdate",
    # Service
    "DomainManager",
]

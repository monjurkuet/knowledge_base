"""
Domain models for multi-domain knowledge base.
Pydantic models for domain configuration and validation.
"""

from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class EntityTypeTemplate(BaseModel):
    """Template for domain-specific entity types."""

    name: str = Field(..., description="Internal name (snake_case)")
    display_name: str = Field(..., description="Human-readable name")
    description: str = Field(default="", description="Entity type description")
    icon: str = Field(default="circle", description="UI icon identifier")
    color: str = Field(default="#4285F4", description="UI color hex code")
    validation_rules: dict[str, Any] = Field(
        default_factory=dict, description="Validation rules"
    )
    extraction_prompt: str = Field(..., description="LLM prompt for extraction")
    example_patterns: list[str] = Field(
        default_factory=list, description="Example patterns"
    )
    synonyms: list[str] = Field(
        default_factory=list, description="Synonyms for this entity type"
    )


class RelationshipTypeTemplate(BaseModel):
    """Template for domain-specific relationship types."""

    name: str = Field(..., description="Internal name (snake_case)")
    display_name: str = Field(..., description="Human-readable name")
    description: str = Field(default="", description="Relationship type description")
    source_entity_types: list[str] = Field(
        ..., description="Allowed source entity types"
    )
    target_entity_types: list[str] = Field(
        ..., description="Allowed target entity types"
    )
    is_directional: bool = Field(
        default=True, description="Whether relationship has direction"
    )
    validation_rules: dict[str, Any] = Field(
        default_factory=dict, description="Validation rules"
    )
    extraction_prompt: str = Field(..., description="LLM prompt for extraction")
    example_patterns: list[str] = Field(
        default_factory=list, description="Example patterns"
    )
    synonyms: list[str] = Field(
        default_factory=list, description="Synonyms for this relationship type"
    )


class ExtractionConfig(BaseModel):
    """Configuration for LLM extraction in a domain."""

    llm_model: str = Field(default="gemini-2.5-flash", description="LLM model to use")
    temperature: float = Field(default=0.1, description="Temperature for generation")
    max_tokens: int = Field(default=8192, description="Max tokens for response")
    confidence_threshold: float = Field(default=0.7, description="Confidence threshold")
    system_prompt: str = Field(default="", description="Domain-specific system prompt")


class UIConfig(BaseModel):
    """UI configuration for a domain."""

    color_scheme: dict[str, str] = Field(
        default_factory=dict, description="UI color scheme"
    )
    layout: str = Field(default="default", description="Layout type")
    default_views: list[str] = Field(default_factory=list, description="Default views")


class AnalysisConfig(BaseModel):
    """Analysis configuration for a domain."""

    community_detection: dict[str, Any] = Field(
        default_factory=dict, description="Community detection settings"
    )
    summarization: dict[str, Any] = Field(
        default_factory=dict, description="Summarization settings"
    )
    trend_analysis: dict[str, Any] = Field(
        default_factory=dict, description="Trend analysis settings"
    )


class DomainTemplate(BaseModel):
    """Complete domain template configuration."""

    id: str = Field(..., description="Domain identifier")
    name: str = Field(..., description="Internal name")
    display_name: str = Field(..., description="Human-readable name")
    description: str = Field(default="", description="Domain description")
    entity_types: list[EntityTypeTemplate] = Field(
        default_factory=list, description="Entity type templates"
    )
    relationship_types: list[RelationshipTypeTemplate] = Field(
        default_factory=list, description="Relationship type templates"
    )
    extraction_config: ExtractionConfig = Field(
        default_factory=ExtractionConfig, description="Extraction configuration"
    )
    analysis_config: AnalysisConfig = Field(
        default_factory=AnalysisConfig, description="Analysis configuration"
    )
    ui_config: UIConfig = Field(
        default_factory=UIConfig, description="UI configuration"
    )


class DomainCreate(BaseModel):
    """Request model for creating a new domain."""

    name: str = Field(
        ...,
        min_length=3,
        max_length=100,
        pattern=r"^[a-z_]+$",
        description="Internal name (snake_case)",
    )
    display_name: str = Field(
        ..., min_length=3, max_length=200, description="Human-readable name"
    )
    description: str | None = Field(None, description="Domain description")
    template_config: dict[str, Any] = Field(
        default_factory=dict, description="Template configuration"
    )


class DomainResponse(BaseModel):
    """Response model for domain data."""

    id: UUID
    name: str
    display_name: str
    description: str | None
    is_active: bool
    node_count: int = 0
    edge_count: int = 0
    created_at: str
    updated_at: str

    model_config = {"from_attributes": True}


class DomainUpdate(BaseModel):
    """Request model for updating a domain."""

    display_name: str | None = Field(None, description="New display name")
    description: str | None = Field(None, description="New description")
    template_config: dict[str, Any] | None = Field(
        None, description="New template configuration"
    )
    is_active: bool | None = Field(None, description="New active status")

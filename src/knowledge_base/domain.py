"""
Domain management module for multi-domain knowledge base.
Handles domain CRUD operations, template loading, and validation.
"""

import json
import logging
from typing import Any
from uuid import UUID

from psycopg import AsyncConnection
from pydantic import BaseModel, Field

from knowledge_base.config import get_config

logger = logging.getLogger(__name__)
config = get_config()


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


class DomainManager:
    """Manages domain operations for the multi-domain knowledge base."""

    def __init__(self, db_conn_str: str | None = None):
        """Initialize domain manager with database connection."""
        self.config = get_config()
        self.db_conn_str = db_conn_str or self.config.database.connection_string

    async def get_connection(self) -> AsyncConnection:
        """Get async database connection."""
        return await AsyncConnection.connect(self.db_conn_str)

    async def create_domain(self, domain_data: DomainCreate) -> DomainResponse:
        """
        Create a new domain in the knowledge base.

        Args:
            domain_data: Domain creation data

        Returns:
            Created domain response
        """
        template_config = json.dumps(domain_data.template_config)

        async with await self.get_connection() as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    """
                    INSERT INTO domains (name, display_name, description, template_config)
                    VALUES (%s, %s, %s, %s)
                    RETURNING id, name, display_name, description, is_active, created_at, updated_at
                    """,
                    (
                        domain_data.name,
                        domain_data.display_name,
                        domain_data.description,
                        template_config,
                    ),
                )
                row = await cur.fetchone()
                await conn.commit()

        if row is None:
            raise ValueError(f"Failed to create domain: {domain_data.name}")

        return DomainResponse(
            id=row[0],
            name=row[1],
            display_name=row[2],
            description=row[3],
            is_active=row[4],
            created_at=str(row[5]),
            updated_at=str(row[6]),
        )

    async def get_domain(self, domain_id: UUID) -> DomainResponse | None:
        """
        Get a domain by ID.

        Args:
            domain_id: Domain UUID

        Returns:
            Domain response or None if not found
        """
        async with await self.get_connection() as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    """
                    SELECT id, name, display_name, description, is_active, created_at, updated_at
                    FROM domains WHERE id = %s
                    """,
                    (domain_id,),
                )
                row = await cur.fetchone()

        if row:
            return DomainResponse(
                id=row[0],
                name=row[1],
                display_name=row[2],
                description=row[3],
                is_active=row[4],
                created_at=str(row[5]),
                updated_at=str(row[6]),
            )
        return None

    async def get_domain_by_name(self, name: str) -> DomainResponse | None:
        """
        Get a domain by name.

        Args:
            name: Domain internal name

        Returns:
            Domain response or None if not found
        """
        async with await self.get_connection() as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    """
                    SELECT id, name, display_name, description, is_active, created_at, updated_at
                    FROM domains WHERE name = %s
                    """,
                    (name,),
                )
                row = await cur.fetchone()

        if row:
            return DomainResponse(
                id=row[0],
                name=row[1],
                display_name=row[2],
                description=row[3],
                is_active=row[4],
                created_at=str(row[5]),
                updated_at=str(row[6]),
            )
        return None

    async def list_domains(self, active_only: bool = True) -> list[DomainResponse]:
        """
        List all domains.

        Args:
            active_only: If True, only return active domains

        Returns:
            List of domain responses
        """
        async with await self.get_connection() as conn:
            async with conn.cursor() as cur:
                if active_only:
                    await cur.execute(
                        """
                        SELECT id, name, display_name, description, is_active, created_at, updated_at
                        FROM domains WHERE is_active = TRUE
                        ORDER BY name
                        """
                    )
                else:
                    await cur.execute(
                        """
                        SELECT id, name, display_name, description, is_active, created_at, updated_at
                        FROM domains ORDER BY name
                        """
                    )
                rows = await cur.fetchall()

        return [
            DomainResponse(
                id=row[0],
                name=row[1],
                display_name=row[2],
                description=row[3],
                is_active=row[4],
                created_at=str(row[5]),
                updated_at=str(row[6]),
            )
            for row in rows
        ]

    async def update_domain(
        self,
        domain_id: UUID,
        display_name: str | None = None,
        description: str | None = None,
        template_config: dict[str, Any] | None = None,
        is_active: bool | None = None,
    ) -> DomainResponse | None:
        """
        Update a domain.

        Args:
            domain_id: Domain UUID
            display_name: New display name (optional)
            description: New description (optional)
            template_config: New template config (optional)
            is_active: New active status (optional)

        Returns:
            Updated domain response or None if not found
        """
        updates = []
        params = []

        if display_name is not None:
            updates.append("display_name = %s")
            params.append(display_name)
        if description is not None:
            updates.append("description = %s")
            params.append(description)
        if template_config is not None:
            updates.append("template_config = %s")
            params.append(json.dumps(template_config))
        if is_active is not None:
            updates.append("is_active = %s")
            params.append(is_active)

        if not updates:
            return await self.get_domain(domain_id)

        params.append(domain_id)

        async with await self.get_connection() as conn:
            async with conn.cursor() as cur:
                query = f"""
                    UPDATE domains
                    SET {", ".join(updates)}
                    WHERE id = %s
                    RETURNING id, name, display_name, description, is_active, created_at, updated_at
                """
                await cur.execute(query, params)
                row = await cur.fetchone()
                await conn.commit()

        if row:
            return DomainResponse(
                id=row[0],
                name=row[1],
                display_name=row[2],
                description=row[3],
                is_active=row[4],
                created_at=str(row[5]),
                updated_at=str(row[6]),
            )
        return None

    async def delete_domain(self, domain_id: UUID) -> bool:
        """
        Soft delete a domain (set is_active = False).

        Args:
            domain_id: Domain UUID

        Returns:
            True if deleted, False if not found
        """
        async with await self.get_connection() as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    "UPDATE domains SET is_active = FALSE WHERE id = %s RETURNING id",
                    (domain_id,),
                )
                row = await cur.fetchone()
                await conn.commit()

        return row is not None

    async def add_entity_type(
        self,
        domain_id: UUID,
        entity_type: EntityTypeTemplate,
    ) -> UUID:
        """
        Add an entity type to a domain.

        Args:
            domain_id: Domain UUID
            entity_type: Entity type template

        Returns:
            Created entity type UUID
        """
        async with await self.get_connection() as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    """
                    INSERT INTO domain_entity_types
                    (domain_id, name, display_name, description, icon, color, validation_rules, extraction_prompt, synonyms)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING id
                    """,
                    (
                        domain_id,
                        entity_type.name,
                        entity_type.display_name,
                        entity_type.description,
                        entity_type.icon,
                        entity_type.color,
                        json.dumps(entity_type.validation_rules),
                        entity_type.extraction_prompt,
                        json.dumps(entity_type.synonyms),
                    ),
                )
                row = await cur.fetchone()
                await conn.commit()

        if row is None:
            raise ValueError(f"Failed to add entity type: {entity_type.name}")

        return row[0]

    async def add_relationship_type(
        self,
        domain_id: UUID,
        relationship_type: RelationshipTypeTemplate,
    ) -> UUID:
        """
        Add a relationship type to a domain.

        Args:
            domain_id: Domain UUID
            relationship_type: Relationship type template

        Returns:
            Created relationship type UUID
        """
        async with await self.get_connection() as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    """
                    INSERT INTO domain_relationship_types
                    (domain_id, name, display_name, description, source_entity_type, target_entity_type,
                     is_directional, validation_rules, extraction_prompt, synonyms)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING id
                    """,
                    (
                        domain_id,
                        relationship_type.name,
                        relationship_type.display_name,
                        relationship_type.description,
                        json.dumps(relationship_type.source_entity_types),
                        json.dumps(relationship_type.target_entity_types),
                        relationship_type.is_directional,
                        json.dumps(relationship_type.validation_rules),
                        relationship_type.extraction_prompt,
                        json.dumps(relationship_type.synonyms),
                    ),
                )
                row = await cur.fetchone()
                await conn.commit()

        if row is None:
            raise ValueError(
                f"Failed to add relationship type: {relationship_type.name}"
            )

        return row[0]

    async def get_entity_types(self, domain_id: UUID) -> list[dict[str, Any]]:
        """
        Get all entity types for a domain.

        Args:
            domain_id: Domain UUID

        Returns:
            List of entity type dictionaries
        """
        async with await self.get_connection() as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    """
                    SELECT id, name, display_name, description, icon, color, validation_rules, extraction_prompt, synonyms
                    FROM domain_entity_types WHERE domain_id = %s ORDER BY name
                    """,
                    (domain_id,),
                )
                rows = await cur.fetchall()

        return [
            {
                "id": row[0],
                "name": row[1],
                "display_name": row[2],
                "description": row[3],
                "icon": row[4],
                "color": row[5],
                "validation_rules": row[6],
                "extraction_prompt": row[7],
                "synonyms": row[8],
            }
            for row in rows
        ]

    async def get_relationship_types(self, domain_id: UUID) -> list[dict[str, Any]]:
        """
        Get all relationship types for a domain.

        Args:
            domain_id: Domain UUID

        Returns:
            List of relationship type dictionaries
        """
        async with await self.get_connection() as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    """
                    SELECT id, name, display_name, description, source_entity_type, target_entity_type,
                           is_directional, validation_rules, extraction_prompt, synonyms
                    FROM domain_relationship_types WHERE domain_id = %s ORDER BY name
                    """,
                    (domain_id,),
                )
                rows = await cur.fetchall()

        return [
            {
                "id": row[0],
                "name": row[1],
                "display_name": row[2],
                "description": row[3],
                "source_entity_type": row[4],
                "target_entity_type": row[5],
                "is_directional": row[6],
                "validation_rules": row[7],
                "extraction_prompt": row[8],
                "synonyms": row[9],
            }
            for row in rows
        ]

    async def apply_template(self, domain_id: UUID, template: DomainTemplate) -> None:
        """
        Apply a domain template to an existing domain.
        Creates all entity and relationship types from the template.

        Args:
            domain_id: Domain UUID
            template: Domain template to apply
        """
        for entity_type in template.entity_types:
            try:
                await self.add_entity_type(domain_id, entity_type)
                logger.info(f"Added entity type: {entity_type.name}")
            except Exception as e:
                logger.warning(f"Failed to add entity type {entity_type.name}: {e}")

        for relationship_type in template.relationship_types:
            try:
                await self.add_relationship_type(domain_id, relationship_type)
                logger.info(f"Added relationship type: {relationship_type.name}")
            except Exception as e:
                logger.warning(
                    f"Failed to add relationship type {relationship_type.name}: {e}"
                )

    async def sync_domain_schema(
        self, domain_id: UUID, template: DomainTemplate
    ) -> None:
        """
        Synchronize a domain's schema with a proposed template.
        Merges new types and updates existing ones.

        Args:
            domain_id: Domain UUID
            template: Proposed domain template
        """
        existing_entities = await self.get_entity_types(domain_id)
        existing_relationships = await self.get_relationship_types(domain_id)

        # Helper to find match
        def find_entity_match(name: str, synonyms: list[str]) -> dict[str, Any] | None:
            name_lower = name.lower()
            syn_lower = {s.lower() for s in synonyms}

            for existing in existing_entities:
                if existing["name"].lower() == name_lower:
                    return existing
                # Check synonyms
                existing_syns = {s.lower() for s in existing.get("synonyms", [])}
                if name_lower in existing_syns:
                    return existing
                if existing["name"].lower() in syn_lower:
                    return existing
                # Intersection of synonyms
                if not syn_lower.isdisjoint(existing_syns):
                    return existing
            return None

        # Sync Entities
        for et in template.entity_types:
            match = find_entity_match(et.name, et.synonyms)
            if match:
                logger.info(
                    f"Entity type '{et.name}' matches existing '{match['name']}'. Merging..."
                )
                # Merge logic: Add new synonyms
                existing_syns = set(match.get("synonyms", []))
                new_syns = set(et.synonyms)
                # Also add the proposed name if it was a synonym match
                if et.name != match["name"]:
                    new_syns.add(et.name)

                merged_syns = list(existing_syns.union(new_syns))

                if len(merged_syns) > len(existing_syns):
                    # Update DB
                    async with await self.get_connection() as conn:
                        async with conn.cursor() as cur:
                            await cur.execute(
                                "UPDATE domain_entity_types SET synonyms = %s WHERE id = %s",
                                (json.dumps(merged_syns), match["id"]),
                            )
                            await conn.commit()
            else:
                logger.info(f"Adding new entity type: {et.name}")
                await self.add_entity_type(domain_id, et)

        # Sync Relationships (Simplified: just check name for now)
        existing_rel_names = {r["name"] for r in existing_relationships}
        for rt in template.relationship_types:
            if rt.name not in existing_rel_names:
                logger.info(f"Adding new relationship type: {rt.name}")
                await self.add_relationship_type(domain_id, rt)

    @staticmethod
    def load_template_from_file(file_path: str) -> DomainTemplate:
        """
        Load a domain template from a JSON file.

        Args:
            file_path: Path to JSON template file

        Returns:
            Domain template
        """
        with open(file_path) as f:
            data = json.load(f)
        return DomainTemplate(**data)

    @staticmethod
    def load_template_from_dict(data: dict[str, Any]) -> DomainTemplate:
        """
        Load a domain template from a dictionary.

        Args:
            data: Template dictionary

        Returns:
            Domain template
        """
        return DomainTemplate(**data)

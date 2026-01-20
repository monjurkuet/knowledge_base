"""
Domain service for domain management business logic.
Uses repository pattern and custom exceptions.
"""

import json
import logging
from typing import Any
from uuid import UUID

from ..utils.errors import DatabaseError, DomainError
from .models import (
    DomainCreate,
    DomainResponse,
    DomainTemplate,
    EntityTypeTemplate,
    RelationshipTypeTemplate,
)
from .repository import DomainRepository

logger = logging.getLogger(__name__)


class DomainManager:
    """Manages domain operations for the multi-domain knowledge base."""

    def __init__(self, db_conn_str: str):
        """Initialize domain manager with database connection."""
        self.db_conn_str = db_conn_str
        self.repository = DomainRepository(db_conn_str)

    async def create_domain(self, domain_data: DomainCreate) -> DomainResponse:
        """
        Create a new domain in the knowledge base.

        Args:
            domain_data: Domain creation data

        Returns:
            Created domain response

        Raises:
            DomainError: If domain creation fails
        """
        try:
            template_config_json = (
                json.dumps(domain_data.template_config)
                if domain_data.template_config
                else None
            )

            result = await self.repository.create(
                name=domain_data.name,
                display_name=domain_data.display_name,
                description=domain_data.description or "",
                template_config=template_config_json,
            )

            return DomainResponse(
                id=UUID(result["id"]),
                name=result["name"],
                display_name=result["display_name"],
                description=result["description"],
                is_active=result["is_active"],
                created_at=result["created_at"],
                updated_at=result["updated_at"],
            )
        except DatabaseError as e:
            raise DomainError(
                f"Failed to create domain: {e.message}",
                domain_name=domain_data.name,
                details=e.details,
            ) from e

    async def get_domain(self, domain_id: UUID) -> DomainResponse | None:
        """
        Get a domain by ID.

        Args:
            domain_id: Domain UUID

        Returns:
            Domain response or None if not found
        """
        result = await self.repository.find_by_id(str(domain_id))
        if not result:
            return None

        return DomainResponse(
            id=UUID(result["id"]),
            name=result["name"],
            display_name=result["display_name"],
            description=result["description"],
            is_active=result["is_active"],
            created_at=result["created_at"],
            updated_at=result["updated_at"],
        )

    async def list_domains(self) -> list[DomainResponse]:
        """
        List all active domains.

        Returns:
            List of domain responses
        """
        results = await self.repository.find_all(active_only=True)

        return [
            DomainResponse(
                id=UUID(result["id"]),
                name=result["name"],
                display_name=result["display_name"],
                description=result["description"],
                is_active=result["is_active"],
                created_at=result["created_at"],
                updated_at=result["updated_at"],
            )
            for result in results
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

        Raises:
            DomainError: If update fails
        """
        try:
            template_config_json = (
                json.dumps(template_config) if template_config is not None else None
            )

            result = await self.repository.update(
                domain_id=str(domain_id),
                display_name=display_name,
                description=description,
                template_config=template_config_json,
                is_active=is_active,
            )

            if not result:
                return None

            return DomainResponse(
                id=UUID(result["id"]),
                name=result["name"],
                display_name=result["display_name"],
                description=result["description"],
                is_active=result["is_active"],
                created_at=result["created_at"],
                updated_at=result["updated_at"],
            )
        except DatabaseError as e:
            raise DomainError(
                f"Failed to update domain: {e.message}",
                domain_id=str(domain_id),
                details=e.details,
            ) from e

    async def delete_domain(self, domain_id: UUID) -> bool:
        """
        Delete a domain.

        Args:
            domain_id: Domain UUID

        Returns:
            True if deleted, False otherwise

        Raises:
            DomainError: If deletion fails
        """
        try:
            await self.repository.delete(str(domain_id))
            return True
        except DatabaseError as e:
            raise DomainError(
                f"Failed to delete domain: {e.message}",
                domain_id=str(domain_id),
                details=e.details,
            ) from e

    async def add_entity_type(
        self, domain_id: UUID, entity_type: EntityTypeTemplate
    ) -> UUID:
        """
        Add an entity type to a domain.

        Args:
            domain_id: Domain UUID
            entity_type: Entity type template

        Returns:
            Created entity type UUID

        Raises:
            DomainError: If creation fails
        """
        try:
            validation_rules_json = (
                json.dumps(entity_type.validation_rules)
                if entity_type.validation_rules
                else None
            )
            synonyms_json = (
                json.dumps(entity_type.synonyms) if entity_type.synonyms else None
            )

            result_id = await self.repository.add_entity_type(
                domain_id=str(domain_id),
                name=entity_type.name,
                display_name=entity_type.display_name,
                description=entity_type.description,
                icon=entity_type.icon,
                color=entity_type.color,
                validation_rules=validation_rules_json,
                extraction_prompt=entity_type.extraction_prompt,
                synonyms=synonyms_json,
            )
            return UUID(result_id)
        except DatabaseError as e:
            raise DomainError(
                f"Failed to add entity type: {e.message}",
                domain_id=str(domain_id),
                details=e.details,
            ) from e

    async def add_relationship_type(
        self, domain_id: UUID, relationship_type: RelationshipTypeTemplate
    ) -> UUID:
        """
        Add a relationship type to a domain.

        Args:
            domain_id: Domain UUID
            relationship_type: Relationship type template

        Returns:
            Created relationship type UUID

        Raises:
            DomainError: If creation fails
        """
        try:
            validation_rules_json = (
                json.dumps(relationship_type.validation_rules)
                if relationship_type.validation_rules
                else None
            )
            synonyms_json = (
                json.dumps(relationship_type.synonyms)
                if relationship_type.synonyms
                else None
            )

            result_id = await self.repository.add_relationship_type(
                domain_id=str(domain_id),
                name=relationship_type.name,
                display_name=relationship_type.display_name,
                description=relationship_type.description,
                validation_rules=validation_rules_json,
                extraction_prompt=relationship_type.extraction_prompt,
                synonyms=synonyms_json,
            )
            return UUID(result_id)
        except DatabaseError as e:
            raise DomainError(
                f"Failed to add relationship type: {e.message}",
                domain_id=str(domain_id),
                details=e.details,
            ) from e

    async def get_entity_types(self, domain_id: UUID) -> list[dict[str, Any]]:
        """
        Get all entity types for a domain.

        Args:
            domain_id: Domain UUID

        Returns:
            List of entity type dictionaries
        """
        return await self.repository.get_entity_types(str(domain_id))

    async def get_relationship_types(self, domain_id: UUID) -> list[dict[str, Any]]:
        """
        Get all relationship types for a domain.

        Args:
            domain_id: Domain UUID

        Returns:
            List of relationship type dictionaries
        """
        return await self.repository.get_relationship_types(str(domain_id))

    async def get_domain_by_name(self, name: str) -> DomainResponse | None:
        """
        Get a domain by name.

        Args:
            name: Domain internal name

        Returns:
            Domain response or None if not found
        """
        result = await self.repository.find_by_name(name)
        if not result:
            return None

        return DomainResponse(
            id=UUID(result["id"]),
            name=result["name"],
            display_name=result["display_name"],
            description=result["description"],
            is_active=result["is_active"],
            created_at=result["created_at"],
            updated_at=result["updated_at"],
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

        Raises:
            DomainError: If sync fails
        """
        try:
            existing_entities = await self.get_entity_types(domain_id)
            existing_relationships = await self.get_relationship_types(domain_id)

            def find_entity_match(
                name: str, synonyms: list[str]
            ) -> dict[str, Any] | None:
                name_lower = name.lower()
                syn_lower = {s.lower() for s in synonyms}

                for existing in existing_entities:
                    if existing["name"].lower() == name_lower:
                        return existing
                    existing_syns = {s.lower() for s in existing.get("synonyms", [])}
                    if name_lower in existing_syns:
                        return existing
                    if existing["name"].lower() in syn_lower:
                        return existing
                    if not syn_lower.isdisjoint(existing_syns):
                        return existing
                return None

            for et in template.entity_types:
                match = find_entity_match(et.name, et.synonyms)
                if match:
                    logger.info(
                        f"Entity type '{et.name}' matches existing '{match['name']}'. Merging..."
                    )
                    existing_syns = set(match.get("synonyms", []))
                    new_syns = set(et.synonyms)
                    if et.name != match["name"]:
                        new_syns.add(et.name)

                    merged_syns = list(existing_syns.union(new_syns))

                    if len(merged_syns) > len(existing_syns):
                        await self.repository.update_entity_type_synonyms(
                            match["id"], json.dumps(merged_syns)
                        )
                else:
                    logger.info(f"Adding new entity type: {et.name}")
                    await self.add_entity_type(domain_id, et)

            existing_rel_names = {r["name"] for r in existing_relationships}
            for rt in template.relationship_types:
                if rt.name not in existing_rel_names:
                    logger.info(f"Adding new relationship type: {rt.name}")
                    await self.add_relationship_type(domain_id, rt)
        except DatabaseError as e:
            raise DomainError(
                f"Failed to sync domain schema: {e.message}",
                domain_id=str(domain_id),
                details=e.details,
            ) from e

    async def apply_template(self, domain_id: UUID, template: DomainTemplate) -> None:
        """
        Apply a domain template to an existing domain.
        Creates all entity and relationship types from the template.

        Args:
            domain_id: Domain UUID
            template: Domain template to apply

        Raises:
            DomainError: If template application fails
        """
        try:
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
        except DatabaseError as e:
            raise DomainError(
                f"Failed to apply domain template: {e.message}",
                domain_id=str(domain_id),
                details=e.details,
            ) from e

    @staticmethod
    def load_template_from_file(file_path: str) -> DomainTemplate:
        """
        Load a domain template from a JSON file.

        Args:
            file_path: Path to JSON file

        Returns:
            DomainTemplate object

        Raises:
            DomainError: If file loading fails
        """
        try:
            with open(file_path) as f:
                data = json.load(f)
            return DomainTemplate(**data)
        except (FileNotFoundError, json.JSONDecodeError, ValueError) as e:
            raise DomainError(
                f"Failed to load domain template from {file_path}: {str(e)}",
                details={"file_path": file_path},
            ) from e

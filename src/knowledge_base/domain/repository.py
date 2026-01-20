"""
Domain repository for database operations.
Uses the repository pattern to abstract database access.
"""

import logging
from typing import Any

from ..repositories.base import BaseRepository
from ..utils.errors import DatabaseError

logger = logging.getLogger(__name__)


class DomainRepository(BaseRepository):
    """Repository for domain database operations."""

    async def find_by_id(self, domain_id: str) -> dict[str, Any] | None:
        """Find a domain by ID."""
        query = """
            SELECT id, name, display_name, description, is_active, template_config, created_at, updated_at
            FROM domains
            WHERE id = %s
        """
        results = await self._execute_query(query, (domain_id,))
        if results:
            row = results[0]
            return {
                "id": str(row[0]),
                "name": row[1],
                "display_name": row[2],
                "description": row[3],
                "is_active": row[4],
                "template_config": row[5],
                "created_at": str(row[6]),
                "updated_at": str(row[7]),
            }
        return None

    async def find_by_name(self, name: str) -> dict[str, Any] | None:
        """Find a domain by name."""
        query = """
            SELECT id, name, display_name, description, is_active, template_config, created_at, updated_at
            FROM domains
            WHERE name = %s
        """
        results = await self._execute_query(query, (name,))
        if results:
            row = results[0]
            return {
                "id": str(row[0]),
                "name": row[1],
                "display_name": row[2],
                "description": row[3],
                "is_active": row[4],
                "template_config": row[5],
                "created_at": str(row[6]),
                "updated_at": str(row[7]),
            }
        return None

    async def find_all(self, active_only: bool = True) -> list[dict[str, Any]]:
        """Find all domains."""
        if active_only:
            query = """
                SELECT id, name, display_name, description, is_active, created_at, updated_at
                FROM domains
                WHERE is_active = true
                ORDER BY display_name
            """
        else:
            query = """
                SELECT id, name, display_name, description, is_active, created_at, updated_at
                FROM domains
                ORDER BY display_name
            """

        results = await self._execute_query(query)
        return [
            {
                "id": str(row[0]),
                "name": row[1],
                "display_name": row[2],
                "description": row[3],
                "is_active": row[4],
                "created_at": str(row[5]),
                "updated_at": str(row[6]),
            }
            for row in results
        ]

    async def create(
        self,
        name: str,
        display_name: str,
        description: str = "",
        template_config: str | None = None,
    ) -> dict[str, Any]:
        """Create a new domain."""
        query = """
            INSERT INTO domains (name, display_name, description, template_config, is_active)
            VALUES (%s, %s, %s, %s, true)
            RETURNING id, name, display_name, description, is_active, created_at, updated_at
        """
        results = await self._execute_query(
            query, (name, display_name, description, template_config), commit=True
        )
        if results:
            row = results[0]
            return {
                "id": str(row[0]),
                "name": row[1],
                "display_name": row[2],
                "description": row[3],
                "is_active": row[4],
                "created_at": str(row[5]),
                "updated_at": str(row[6]),
            }
        raise DatabaseError("Failed to create domain")

    async def update(
        self,
        domain_id: str,
        display_name: str | None = None,
        description: str | None = None,
        template_config: str | None = None,
        is_active: bool | None = None,
    ) -> dict[str, Any] | None:
        """Update a domain."""
        updates = []
        params: list[str | bool] = []

        if display_name is not None:
            updates.append("display_name = %s")
            params.append(display_name)

        if description is not None:
            updates.append("description = %s")
            params.append(description)

        if template_config is not None:
            updates.append("template_config = %s")
            params.append(template_config)

        if is_active is not None:
            updates.append("is_active = %s")
            params.append(is_active)

        if not updates:
            return await self.find_by_id(domain_id)

        params.append(str(domain_id))

        query = f"""
            UPDATE domains
            SET {", ".join(updates)}, updated_at = NOW()
            WHERE id = %s
            RETURNING id, name, display_name, description, is_active, created_at, updated_at
        """

        results = await self._execute_query(query, tuple(params), commit=True)
        if results:
            row = results[0]
            return {
                "id": str(row[0]),
                "name": row[1],
                "display_name": row[2],
                "description": row[3],
                "is_active": row[4],
                "created_at": str(row[5]),
                "updated_at": str(row[6]),
            }
        return None

    async def delete(self, domain_id: str) -> bool:
        """Delete a domain."""
        query = "DELETE FROM domains WHERE id = %s"
        await self._execute_query(query, (domain_id,), fetch=False, commit=True)
        return True

    async def get_entity_types(self, domain_id: str) -> list[dict[str, Any]]:
        """Get all entity types for a domain."""
        query = """
            SELECT id, name, display_name, description, icon, color, validation_rules, extraction_prompt, synonyms
            FROM domain_entity_types
            WHERE domain_id = %s
            ORDER BY name
        """
        results = await self._execute_query(query, (domain_id,))
        return [
            {
                "id": str(row[0]),
                "name": row[1],
                "display_name": row[2],
                "description": row[3],
                "icon": row[4],
                "color": row[5],
                "validation_rules": row[6],
                "extraction_prompt": row[7],
                "synonyms": row[8],
            }
            for row in results
        ]

    async def add_entity_type(
        self,
        domain_id: str,
        name: str,
        display_name: str,
        description: str = "",
        icon: str = "",
        color: str = "#000000",
        validation_rules: str | None = None,
        extraction_prompt: str = "",
        synonyms: str | None = None,
    ) -> str:
        """Add an entity type to a domain."""
        query = """
            INSERT INTO domain_entity_types
            (domain_id, name, display_name, description, icon, color, validation_rules, extraction_prompt, synonyms)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (domain_id, name) DO UPDATE
            SET display_name = EXCLUDED.display_name,
                description = EXCLUDED.description,
                icon = EXCLUDED.icon,
                color = EXCLUDED.color,
                validation_rules = EXCLUDED.validation_rules,
                extraction_prompt = EXCLUDED.extraction_prompt,
                synonyms = EXCLUDED.synonyms
            RETURNING id
        """
        results = await self._execute_query(
            query,
            (
                domain_id,
                name,
                display_name,
                description,
                icon,
                color,
                validation_rules,
                extraction_prompt,
                synonyms,
            ),
            commit=True,
        )
        if results:
            return str(results[0][0])
        raise DatabaseError(f"Failed to add entity type: {name}")

    async def get_relationship_types(self, domain_id: str) -> list[dict[str, Any]]:
        """Get all relationship types for a domain."""
        query = """
            SELECT id, name, display_name, description, source_entity_type, target_entity_type, is_directional, validation_rules, extraction_prompt, synonyms
            FROM domain_relationship_types
            WHERE domain_id = %s
            ORDER BY name
        """
        results = await self._execute_query(query, (domain_id,))
        return [
            {
                "id": str(row[0]),
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
            for row in results
        ]

    async def add_relationship_type(
        self,
        domain_id: str,
        name: str,
        display_name: str,
        description: str = "",
        validation_rules: str | None = None,
        extraction_prompt: str = "",
        synonyms: str | None = None,
    ) -> str:
        """Add a relationship type to a domain."""
        query = """
            INSERT INTO domain_relationship_types
            (domain_id, name, display_name, description, validation_rules, extraction_prompt, synonyms)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (domain_id, name) DO UPDATE
            SET display_name = EXCLUDED.display_name,
                description = EXCLUDED.description,
                validation_rules = EXCLUDED.validation_rules,
                extraction_prompt = EXCLUDED.extraction_prompt,
                synonyms = EXCLUDED.synonyms
            RETURNING id
        """
        results = await self._execute_query(
            query,
            (
                domain_id,
                name,
                display_name,
                description,
                validation_rules,
                extraction_prompt,
                synonyms,
            ),
            commit=True,
        )
        if results:
            return str(results[0][0])
        raise DatabaseError(f"Failed to add relationship type: {name}")

    async def update_entity_type_synonyms(
        self, entity_type_id: str, synonyms_json: str
    ) -> None:
        """Update synonyms for an entity type."""
        query = """
            UPDATE domain_entity_types
            SET synonyms = %s
            WHERE id = %s
        """
        await self._execute_query(
            query, (synonyms_json, entity_type_id), fetch=False, commit=True
        )

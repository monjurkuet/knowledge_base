"""
Repository for domain operations.
"""

import json
import logging
from typing import Any

from .base import BaseRepository

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
                "template_config": json.loads(row[5]) if row[5] else None,
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
                "template_config": json.loads(row[5]) if row[5] else None,
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
        template_config: dict[str, Any] | None = None,
    ) -> str:
        """Create a new domain."""
        query = """
            INSERT INTO domains (name, display_name, description, template_config, is_active)
            VALUES (%s, %s, %s, %s, true)
            RETURNING id
        """
        config_json = json.dumps(template_config) if template_config else None
        results = await self._execute_query(
            query, (name, display_name, description, config_json), commit=True
        )
        return str(results[0][0]) if results else ""

    async def update(
        self,
        domain_id: str,
        display_name: str | None = None,
        description: str | None = None,
        template_config: dict[str, Any] | None = None,
        is_active: bool | None = None,
    ) -> bool:
        """Update a domain."""
        updates = []
        params: list[Any] = []

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
            return False

        params.append(domain_id)
        query = (
            f"UPDATE domains SET {', '.join(updates)}, updated_at = NOW() WHERE id = %s"
        )

        await self._execute_query(query, tuple(params), fetch=False, commit=True)
        return True

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
                "validation_rules": json.loads(row[6]) if row[6] else None,
                "extraction_prompt": row[7],
                "synonyms": json.loads(row[8]) if row[8] else None,
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
        validation_rules: dict[str, Any] | None = None,
        extraction_prompt: str = "",
        synonyms: list[str] | None = None,
    ) -> str:
        """Add an entity type to a domain."""
        query = """
            INSERT INTO domain_entity_types
            (domain_id, name, display_name, description, icon, color, validation_rules, extraction_prompt, synonyms)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
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
                json.dumps(validation_rules) if validation_rules else None,
                extraction_prompt,
                json.dumps(synonyms) if synonyms else None,
            ),
            commit=True,
        )
        return str(results[0][0]) if results else ""

    async def get_relationship_types(self, domain_id: str) -> list[dict[str, Any]]:
        """Get all relationship types for a domain."""
        query = """
            SELECT id, name, display_name, description, icon, color, validation_rules, extraction_prompt, synonyms
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
                "icon": row[4],
                "color": row[5],
                "validation_rules": json.loads(row[6]) if row[6] else None,
                "extraction_prompt": row[7],
                "synonyms": json.loads(row[8]) if row[8] else None,
            }
            for row in results
        ]

    async def add_relationship_type(
        self,
        domain_id: str,
        name: str,
        display_name: str,
        description: str = "",
        icon: str = "",
        color: str = "#000000",
        validation_rules: dict[str, Any] | None = None,
        extraction_prompt: str = "",
        synonyms: list[str] | None = None,
    ) -> str:
        """Add a relationship type to a domain."""
        query = """
            INSERT INTO domain_relationship_types
            (domain_id, name, display_name, description, icon, color, validation_rules, extraction_prompt, synonyms)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
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
                json.dumps(validation_rules) if validation_rules else None,
                extraction_prompt,
                json.dumps(synonyms) if synonyms else None,
            ),
            commit=True,
        )
        return str(results[0][0]) if results else ""

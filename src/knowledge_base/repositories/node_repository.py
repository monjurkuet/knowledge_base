"""
Repository for node (entity) operations.
"""

import logging
from typing import Any

from .base import BaseRepository

logger = logging.getLogger(__name__)


class NodeRepository(BaseRepository):
    """Repository for node (entity) database operations."""

    async def find_by_id(self, node_id: str) -> dict[str, Any] | None:
        """Find a node by ID."""
        query = "SELECT id, name, type, description, embedding, domain_id FROM nodes WHERE id = %s"
        results = await self._execute_query(query, (node_id,))
        if results:
            row = results[0]
            return {
                "id": str(row[0]),
                "name": row[1],
                "type": row[2],
                "description": row[3],
                "embedding": list(row[4]) if row[4] else None,
                "domain_id": str(row[5]) if row[5] else None,
            }
        return None

    async def find_by_name(
        self, name: str, domain_id: str | None = None
    ) -> list[dict[str, Any]]:
        """Find nodes by name."""
        if domain_id:
            query = "SELECT id, name, type, description FROM nodes WHERE name = %s AND domain_id = %s"
            params = (name, domain_id)
        else:
            query = "SELECT id, name, type, description FROM nodes WHERE name = %s"
            params = (name,)

        results = await self._execute_query(query, params)
        return [
            {
                "id": str(row[0]),
                "name": row[1],
                "type": row[2],
                "description": row[3],
            }
            for row in results
        ]

    async def find_similar(
        self, embedding: list[float], threshold: float = 0.70, limit: int = 5
    ) -> list[dict[str, Any]]:
        """Find nodes with similar embeddings using vector search."""
        query = """
            SELECT id, name, type, description, 1 - (embedding <=> %s::vector) as similarity
            FROM nodes
            WHERE 1 - (embedding <=> %s::vector) > %s
            ORDER BY similarity DESC
            LIMIT %s
        """
        results = await self._execute_query(
            query, (embedding, embedding, threshold, limit)
        )
        return [
            {
                "id": str(row[0]),
                "name": row[1],
                "type": row[2],
                "description": row[3],
                "similarity": float(row[4]),
            }
            for row in results
        ]

    async def create(
        self,
        entity: dict[str, Any],
        embedding: list[float],
        domain_id: str | None = None,
    ) -> str:
        """Create a new node."""
        query = """
            INSERT INTO nodes (name, type, description, embedding, domain_id)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING id
        """
        results = await self._execute_query(
            query,
            (
                entity["name"],
                entity["type"],
                entity.get("description", ""),
                embedding,
                domain_id,
            ),
            commit=True,
        )
        return str(results[0][0]) if results else ""

    async def update(self, node_id: str, updates: dict[str, Any]) -> bool:
        """Update a node."""
        if not updates:
            return False

        set_clauses = []
        params: list[Any] = []

        for key, value in updates.items():
            set_clauses.append(f"{key} = %s")
            params.append(value)

        params.append(node_id)
        query = f"UPDATE nodes SET {', '.join(set_clauses)} WHERE id = %s"

        await self._execute_query(query, tuple(params), fetch=False, commit=True)
        return True

    async def delete(self, node_id: str) -> bool:
        """Delete a node."""
        query = "DELETE FROM nodes WHERE id = %s"
        await self._execute_query(query, (node_id,), fetch=False, commit=True)
        return True

    async def find_by_type(
        self, node_type: str, limit: int = 100, offset: int = 0
    ) -> list[dict[str, Any]]:
        """Find nodes by type with pagination."""
        query = """
            SELECT id, name, type, description
            FROM nodes
            WHERE type = %s
            ORDER BY name
            LIMIT %s OFFSET %s
        """
        results = await self._execute_query(query, (node_type, limit, offset))
        return [
            {
                "id": str(row[0]),
                "name": row[1],
                "type": row[2],
                "description": row[3],
            }
            for row in results
        ]

    async def search(self, query_text: str, limit: int = 10) -> list[dict[str, Any]]:
        """Search nodes by name or description."""
        query = """
            SELECT id, name, type, description
            FROM nodes
            WHERE name ILIKE %s OR description ILIKE %s
            LIMIT %s
        """
        pattern = f"%{query_text}%"
        results = await self._execute_query(query, (pattern, pattern, limit))
        return [
            {
                "id": str(row[0]),
                "name": row[1],
                "type": row[2],
                "description": row[3],
            }
            for row in results
        ]

    async def count_by_type(self, node_type: str | None = None) -> int:
        """Count nodes, optionally filtered by type."""
        if node_type:
            query = "SELECT COUNT(*) FROM nodes WHERE type = %s"
            results = await self._execute_query(query, (node_type,))
        else:
            query = "SELECT COUNT(*) FROM nodes"
            results = await self._execute_query(query)

        return results[0][0] if results else 0

    async def get_all_types(self) -> list[str]:
        """Get all unique node types."""
        query = "SELECT DISTINCT type FROM nodes ORDER BY type"
        results = await self._execute_query(query)
        return [row[0] for row in results] if results else []

    async def find_by_domain(self, domain_id: str) -> list[dict[str, Any]]:
        """Find all nodes in a domain."""
        query = "SELECT id, name, type, description FROM nodes WHERE domain_id = %s ORDER BY name"
        results = await self._execute_query(query, (domain_id,))
        return [
            {
                "id": str(row[0]),
                "name": row[1],
                "type": row[2],
                "description": row[3],
            }
            for row in results
        ]

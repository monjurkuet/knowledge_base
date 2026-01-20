"""
Repository for edge (relationship) operations.
"""

import logging
from typing import Any

from .base import BaseRepository

logger = logging.getLogger(__name__)


class EdgeRepository(BaseRepository):
    """Repository for edge (relationship) database operations."""

    async def find_by_id(self, edge_id: str) -> dict[str, Any] | None:
        """Find an edge by ID."""
        query = "SELECT id, source_id, target_id, type, description, weight FROM edges WHERE id = %s"
        results = await self._execute_query(query, (edge_id,))
        if results:
            row = results[0]
            return {
                "id": str(row[0]),
                "source_id": str(row[1]),
                "target_id": str(row[2]),
                "type": row[3],
                "description": row[4],
                "weight": float(row[5]),
            }
        return None

    async def find_by_source(self, source_id: str) -> list[dict[str, Any]]:
        """Find all edges from a source node."""
        query = """
            SELECT id, source_id, target_id, type, description, weight
            FROM edges
            WHERE source_id = %s
            ORDER BY type, target_id
        """
        results = await self._execute_query(query, (source_id,))
        return [
            {
                "id": str(row[0]),
                "source_id": str(row[1]),
                "target_id": str(row[2]),
                "type": row[3],
                "description": row[4],
                "weight": float(row[5]),
            }
            for row in results
        ]

    async def find_by_target(self, target_id: str) -> list[dict[str, Any]]:
        """Find all edges to a target node."""
        query = """
            SELECT id, source_id, target_id, type, description, weight
            FROM edges
            WHERE target_id = %s
            ORDER BY type, source_id
        """
        results = await self._execute_query(query, (target_id,))
        return [
            {
                "id": str(row[0]),
                "source_id": str(row[1]),
                "target_id": str(row[2]),
                "type": row[3],
                "description": row[4],
                "weight": float(row[5]),
            }
            for row in results
        ]

    async def create(
        self,
        source_id: str,
        target_id: str,
        edge_type: str,
        description: str = "",
        weight: float = 1.0,
    ) -> str:
        """Create a new edge."""
        query = """
            INSERT INTO edges (source_id, target_id, type, description, weight)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING id
        """
        results = await self._execute_query(
            query, (source_id, target_id, edge_type, description, weight), commit=True
        )
        return str(results[0][0]) if results else ""

    async def find_all(self, limit: int = 100, offset: int = 0) -> list[dict[str, Any]]:
        """Find all edges with pagination."""
        query = """
            SELECT id, source_id, target_id, type, description, weight
            FROM edges
            ORDER BY source_id, target_id
            LIMIT %s OFFSET %s
        """
        results = await self._execute_query(query, (limit, offset))
        return [
            {
                "id": str(row[0]),
                "source_id": str(row[1]),
                "target_id": str(row[2]),
                "type": row[3],
                "description": row[4],
                "weight": float(row[5]),
            }
            for row in results
        ]

    async def find_by_type(self, edge_type: str) -> list[dict[str, Any]]:
        """Find all edges of a specific type."""
        query = """
            SELECT id, source_id, target_id, type, description, weight
            FROM edges
            WHERE type = %s
            ORDER BY source_id, target_id
        """
        results = await self._execute_query(query, (edge_type,))
        return [
            {
                "id": str(row[0]),
                "source_id": str(row[1]),
                "target_id": str(row[2]),
                "type": row[3],
                "description": row[4],
                "weight": float(row[5]),
            }
            for row in results
        ]

    async def count(self) -> int:
        """Count all edges."""
        query = "SELECT COUNT(*) FROM edges"
        results = await self._execute_query(query)
        return results[0][0] if results else 0

    async def delete(self, edge_id: str) -> bool:
        """Delete an edge."""
        query = "DELETE FROM edges WHERE id = %s"
        await self._execute_query(query, (edge_id,), fetch=False, commit=True)
        return True

    async def find_between(
        self, source_id: str, target_id: str
    ) -> list[dict[str, Any]]:
        """Find all edges between two nodes."""
        query = """
            SELECT id, source_id, target_id, type, description, weight
            FROM edges
            WHERE source_id = %s AND target_id = %s
        """
        results = await self._execute_query(query, (source_id, target_id))
        return [
            {
                "id": str(row[0]),
                "source_id": str(row[1]),
                "target_id": str(row[2]),
                "type": row[3],
                "description": row[4],
                "weight": float(row[5]),
            }
            for row in results
        ]

    async def get_all_types(self) -> list[str]:
        """Get all unique edge types."""
        query = "SELECT DISTINCT type FROM edges ORDER BY type"
        results = await self._execute_query(query)
        return [row[0] for row in results] if results else []

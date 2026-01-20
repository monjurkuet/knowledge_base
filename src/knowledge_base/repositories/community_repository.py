"""
Repository for community operations.
"""

import logging
from typing import Any

from .base import BaseRepository

logger = logging.getLogger(__name__)


class CommunityRepository(BaseRepository):
    """Repository for community database operations."""

    async def find_by_id(self, community_id: str) -> dict[str, Any] | None:
        """Find a community by ID."""
        query = """
            SELECT id, title, level, summary, full_content, embedding, created_at, updated_at
            FROM communities
            WHERE id = %s
        """
        results = await self._execute_query(query, (community_id,))
        if results:
            row = results[0]
            return {
                "id": str(row[0]),
                "title": row[1],
                "level": row[2],
                "summary": row[3],
                "full_content": row[4],
                "embedding": list(row[5]) if row[5] else None,
                "created_at": str(row[6]),
                "updated_at": str(row[7]),
            }
        return None

    async def find_by_level(self, level: int) -> list[dict[str, Any]]:
        """Find all communities at a specific level."""
        query = """
            SELECT id, title, level, summary
            FROM communities
            WHERE level = %s
            ORDER BY title
        """
        results = await self._execute_query(query, (level,))
        return [
            {
                "id": str(row[0]),
                "title": row[1],
                "level": row[2],
                "summary": row[3],
            }
            for row in results
        ]

    async def find_all(self) -> list[dict[str, Any]]:
        """Find all communities."""
        query = """
            SELECT id, title, level, summary
            FROM communities
            ORDER BY level DESC, title ASC
        """
        results = await self._execute_query(query)
        return [
            {
                "id": str(row[0]),
                "title": row[1],
                "level": row[2],
                "summary": row[3],
            }
            for row in results
        ]

    async def create(
        self, title: str, level: int, summary: str = "Pending Summarization"
    ) -> str:
        """Create a new community."""
        query = """
            INSERT INTO communities (title, level, summary)
            VALUES (%s, %s, %s)
            RETURNING id
        """
        results = await self._execute_query(query, (title, level, summary), commit=True)
        return str(results[0][0]) if results else ""

    async def update(
        self,
        community_id: str,
        title: str | None = None,
        summary: str | None = None,
        full_content: str | None = None,
        embedding: list[float] | None = None,
    ) -> bool:
        """Update a community."""
        updates = []
        params: list[Any] = []

        if title is not None:
            updates.append("title = %s")
            params.append(title)

        if summary is not None:
            updates.append("summary = %s")
            params.append(summary)

        if full_content is not None:
            updates.append("full_content = %s")
            params.append(full_content)

        if embedding is not None:
            updates.append("embedding = %s")
            params.append(embedding)

        if not updates:
            return False

        params.append(community_id)
        query = f"UPDATE communities SET {', '.join(updates)}, updated_at = NOW() WHERE id = %s"

        await self._execute_query(query, tuple(params), fetch=False, commit=True)
        return True

    async def get_max_level(self) -> int:
        """Get the maximum community level."""
        query = "SELECT MAX(level) FROM communities"
        results = await self._execute_query(query)
        return results[0][0] if results and results[0][0] is not None else 0

    async def get_members(self, community_id: str) -> list[dict[str, Any]]:
        """Get all nodes in a community."""
        query = """
            SELECT n.id, n.name, n.type, n.description
            FROM community_membership cm
            JOIN nodes n ON cm.node_id = n.id
            WHERE cm.community_id = %s
            ORDER BY n.name
        """
        results = await self._execute_query(query, (community_id,))
        return [
            {
                "id": str(row[0]),
                "name": row[1],
                "type": row[2],
                "description": row[3],
            }
            for row in results
        ]

    async def get_member_count(self, community_id: str) -> int:
        """Count members in a community."""
        query = "SELECT COUNT(*) FROM community_membership WHERE community_id = %s"
        results = await self._execute_query(query, (community_id,))
        return results[0][0] if results else 0

    async def add_member(self, community_id: str, node_id: str) -> bool:
        """Add a node to a community."""
        query = """
            INSERT INTO community_membership (community_id, node_id)
            VALUES (%s, %s)
            ON CONFLICT DO NOTHING
        """
        await self._execute_query(
            query, (community_id, node_id), fetch=False, commit=True
        )
        return True

    async def add_members_bulk(self, community_id: str, node_ids: list[str]) -> bool:
        """Add multiple nodes to a community."""
        if not node_ids:
            return True

        values = ", ".join(["(%s, %s)" for _ in node_ids])
        params: list[Any] = []
        for node_id in node_ids:
            params.extend([community_id, node_id])

        query = f"""
            INSERT INTO community_membership (community_id, node_id)
            VALUES {values}
            ON CONFLICT DO NOTHING
        """
        await self._execute_query(query, tuple(params), fetch=False, commit=True)
        return True

    async def get_children(self, community_id: str) -> list[dict[str, Any]]:
        """Get child communities."""
        query = """
            SELECT c.id, c.title, c.level, c.summary
            FROM community_hierarchy ch
            JOIN communities c ON ch.child_id = c.id
            WHERE ch.parent_id = %s
            ORDER BY c.title
        """
        results = await self._execute_query(query, (community_id,))
        return [
            {
                "id": str(row[0]),
                "title": row[1],
                "level": row[2],
                "summary": row[3],
            }
            for row in results
        ]

    async def add_hierarchy(self, parent_id: str, child_id: str) -> bool:
        """Add a parent-child relationship."""
        query = """
            INSERT INTO community_hierarchy (parent_id, child_id)
            VALUES (%s, %s)
            ON CONFLICT DO NOTHING
        """
        await self._execute_query(
            query, (parent_id, child_id), fetch=False, commit=True
        )
        return True

    async def count(self) -> int:
        """Count all communities."""
        query = "SELECT COUNT(*) FROM communities"
        results = await self._execute_query(query)
        return results[0][0] if results else 0

    async def find_similar(
        self, embedding: list[float], threshold: float = 0.70, limit: int = 5
    ) -> list[dict[str, Any]]:
        """Find communities with similar embeddings."""
        query = """
            SELECT id, title, level, summary, 1 - (embedding <=> %s::vector) as similarity
            FROM communities
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
                "title": row[1],
                "level": row[2],
                "summary": row[3],
                "similarity": float(row[4]),
            }
            for row in results
        ]

    async def clear_all(self) -> bool:
        """Clear all communities and related data."""
        queries = [
            ("DELETE FROM community_hierarchy", None),
            ("DELETE FROM community_membership", None),
            ("DELETE FROM communities", None),
        ]

        for query, params in queries:
            await self._execute_query(query, params, fetch=False, commit=True)

        return True

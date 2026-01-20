"""
Repository for statistics and analytics operations.
"""

import logging
from typing import Any

from .base import BaseRepository

logger = logging.getLogger(__name__)


class StatsRepository(BaseRepository):
    """Repository for statistics and analytics database operations."""

    async def get_counts(self) -> dict[str, int]:
        """Get counts of all major entities."""
        queries = [
            ("SELECT COUNT(*) FROM nodes", None),
            ("SELECT COUNT(*) FROM edges", None),
            ("SELECT COUNT(*) FROM communities", None),
            ("SELECT COUNT(*) FROM events", None),
            ("SELECT COUNT(*) FROM domains", None),
        ]

        results = []
        for query, params in queries:
            result = await self._execute_query(query, params)
            results.append(result[0][0] if result else 0)

        return {
            "nodes_count": results[0],
            "edges_count": results[1],
            "communities_count": results[2],
            "events_count": results[3],
            "domains_count": results[4],
        }

    async def get_node_type_distribution(self) -> list[dict[str, Any]]:
        """Get distribution of nodes by type."""
        query = """
            SELECT type, COUNT(*) as count
            FROM nodes
            GROUP BY type
            ORDER BY count DESC
        """
        results = await self._execute_query(query)
        return [{"type": row[0], "count": row[1]} for row in results] if results else []

    async def get_edge_type_distribution(self) -> list[dict[str, Any]]:
        """Get distribution of edges by type."""
        query = """
            SELECT type, COUNT(*) as count
            FROM edges
            GROUP BY type
            ORDER BY count DESC
        """
        results = await self._execute_query(query)
        return [{"type": row[0], "count": row[1]} for row in results] if results else []

    async def get_community_level_distribution(self) -> list[dict[str, Any]]:
        """Get distribution of communities by level."""
        query = """
            SELECT level, COUNT(*) as count
            FROM communities
            GROUP BY level
            ORDER BY level DESC
        """
        results = await self._execute_query(query)
        return (
            [{"level": row[0], "count": row[1]} for row in results] if results else []
        )

    async def get_top_nodes(self, limit: int = 10) -> list[dict[str, Any]]:
        """Get top nodes by connection count."""
        query = """
            SELECT n.id, n.name, n.type,
                   (SELECT COUNT(*) FROM edges e WHERE e.source_id = n.id OR e.target_id = n.id) as connections
            FROM nodes n
            ORDER BY connections DESC
            LIMIT %s
        """
        results = await self._execute_query(query, (limit,))
        return [
            {
                "id": str(row[0]),
                "name": row[1],
                "type": row[2],
                "connections": row[3],
            }
            for row in results
        ]

    async def get_domain_statistics(self, domain_id: str) -> dict[str, Any]:
        """Get statistics for a specific domain."""
        queries = [
            ("SELECT COUNT(*) FROM nodes WHERE domain_id = %s", (domain_id,)),
            (
                "SELECT COUNT(DISTINCT type) FROM nodes WHERE domain_id = %s",
                (domain_id,),
            ),
            (
                "SELECT COUNT(*) FROM edges e JOIN nodes n ON e.source_id = n.id WHERE n.domain_id = %s",
                (domain_id,),
            ),
        ]

        results = []
        for query, params in queries:
            result = await self._execute_query(query, params)
            results.append(result[0][0] if result else 0)

        return {
            "node_count": results[0],
            "unique_types": results[1],
            "edge_count": results[2],
        }

    async def get_graph_summary(self) -> dict[str, Any]:
        """Get overall graph summary statistics."""
        query = """
            SELECT
                (SELECT COUNT(*) FROM nodes) as total_nodes,
                (SELECT COUNT(*) FROM edges) as total_edges,
                (SELECT COUNT(*) FROM communities) as total_communities,
                (SELECT MAX(level) FROM communities) as max_community_level,
                (SELECT AVG(node_count) FROM (
                    SELECT COUNT(*) as node_count
                    FROM community_membership
                    GROUP BY community_id
                ) sub) as avg_community_size
        """
        result = await self._execute_query(query)
        if result and result[0]:
            row = result[0]
            return {
                "total_nodes": row[0],
                "total_edges": row[1],
                "total_communities": row[2],
                "max_community_level": row[3],
                "avg_community_size": float(row[4]) if row[4] else 0.0,
            }
        return {}

    async def get_recent_activity(self, limit: int = 10) -> list[dict[str, Any]]:
        """Get recent activity (based on updated_at timestamps)."""
        queries = [
            """
            SELECT 'node' as type, name as title, updated_at
            FROM nodes
            ORDER BY updated_at DESC
            LIMIT %s
            """,
            """
            SELECT 'community' as type, title, updated_at
            FROM communities
            ORDER BY updated_at DESC
            LIMIT %s
            """,
        ]

        all_activities = []
        for query in queries:
            results = await self._execute_query(query, (limit,))
            for row in results:
                all_activities.append(
                    {
                        "type": row[0],
                        "title": row[1],
                        "updated_at": str(row[2]),
                    }
                )

        all_activities.sort(key=lambda x: x["updated_at"], reverse=True)
        return all_activities[:limit]

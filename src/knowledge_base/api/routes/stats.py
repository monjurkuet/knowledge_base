"""
Database statistics routes
"""

import logging

import psycopg
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from knowledge_base.config import get_config

logger = logging.getLogger(__name__)
router = APIRouter()
config = get_config()


class StatsResponse(BaseModel):
    nodes_count: int
    edges_count: int
    communities_count: int
    events_count: int


@router.get("", response_model=StatsResponse)
async def get_stats() -> StatsResponse:
    """Get database statistics"""
    try:
        async with (
            await psycopg.AsyncConnection.connect(
                config.database.connection_string
            ) as conn,
            conn.cursor() as cur,
        ):
            await cur.execute("SELECT COUNT(*) FROM nodes")
            nodes_result = await cur.fetchone()
            nodes_count = nodes_result[0] if nodes_result else 0

            await cur.execute("SELECT COUNT(*) FROM edges")
            edges_result = await cur.fetchone()
            edges_count = edges_result[0] if edges_result else 0

            await cur.execute("SELECT COUNT(*) FROM communities")
            communities_result = await cur.fetchone()
            communities_count = communities_result[0] if communities_result else 0

            await cur.execute("SELECT COUNT(*) FROM events")
            events_result = await cur.fetchone()
            events_count = events_result[0] if events_result else 0

        return StatsResponse(
            nodes_count=nodes_count,
            edges_count=edges_count,
            communities_count=communities_count,
            events_count=events_count,
        )

    except Exception as e:
        logger.error(f"Failed to get stats: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get stats: {str(e)}")

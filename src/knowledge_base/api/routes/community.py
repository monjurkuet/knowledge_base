"""
Community detection and summarization routes
"""

import logging

import psycopg
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from knowledge_base.config import get_config

from ..dependencies import CommunityDetectorDep, SummarizerDep

logger = logging.getLogger(__name__)
router = APIRouter()
config = get_config()


class CommunityResponse(BaseModel):
    id: str
    title: str
    summary: str
    node_count: int


@router.get("", response_model=list[CommunityResponse])
async def get_communities() -> list[CommunityResponse]:
    """Get community information"""
    try:
        async with await psycopg.AsyncConnection.connect(
            config.database.connection_string
        ) as conn:
            async with conn.cursor() as cur:
                await cur.execute("""
                        SELECT c.id, c.title, c.summary, COUNT(cm.node_id) as node_count
                        FROM communities c
                        LEFT JOIN community_membership cm ON c.id = cm.community_id
                        GROUP BY c.id, c.title, c.summary
                        ORDER BY c.id
                    """)

                rows = await cur.fetchall()
                communities = [
                    CommunityResponse(
                        id=str(row[0]),
                        title=row[1] or f"Community {row[0]}",
                        summary=row[2] or "",
                        node_count=row[3],
                    )
                    for row in rows
                ]

        return communities
    except Exception as e:
        logger.error(f"Failed to get communities: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to get communities: {str(e)}"
        )


@router.post("/detect")
async def detect_communities(
    channel_id: str | None = None,
    community_detector: CommunityDetectorDep = None,
) -> dict[str, str]:
    """Run community detection on the current graph"""
    try:
        G = await community_detector.load_graph()
        if G.number_of_nodes() > 0:
            memberships = community_detector.detect_communities(G)
            await community_detector.save_communities(memberships)
            return {
                "status": "success",
                "message": f"Detected communities for {G.number_of_nodes()} nodes",
            }
        else:
            return {"status": "no_data", "message": "No nodes found in database"}

    except Exception as e:
        logger.error(f"Community detection failed: {e}")
        raise HTTPException(
            status_code=500, detail=f"Community detection failed: {str(e)}"
        )


@router.post("/summarize")
async def run_summarization(
    channel_id: str | None = None,
    summarizer: SummarizerDep = None,
) -> dict[str, str]:
    """Run recursive summarization on communities"""
    try:
        await summarizer.summarize_all()
        return {"status": "success", "message": "Summarization completed"}

    except Exception as e:
        logger.error(f"Summarization failed: {e}")
        raise HTTPException(status_code=500, detail=f"Summarization failed: {str(e)}")

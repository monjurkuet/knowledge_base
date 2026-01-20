"""
Search and graph query routes
"""

import logging
from typing import Any

import psycopg
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from knowledge_base.config import get_config

logger = logging.getLogger(__name__)
router = APIRouter()
config = get_config()


class SearchRequest(BaseModel):
    query: str
    limit: int | None = 10


class NodeResponse(BaseModel):
    id: str
    name: str
    type: str
    description: str


class EdgeResponse(BaseModel):
    source_id: str
    target_id: str
    type: str
    description: str
    weight: float


class PaginatedNodesResponse(BaseModel):
    nodes: list[NodeResponse]
    total: int
    limit: int
    offset: int


class PaginatedEdgesResponse(BaseModel):
    edges: list[EdgeResponse]
    total: int
    limit: int
    offset: int


@router.post("/search")
async def search_nodes(request: SearchRequest) -> dict[str, Any]:
    """Search nodes using vector similarity"""
    try:
        async with await psycopg.AsyncConnection.connect(
            config.database.connection_string
        ) as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    "SELECT id, name, type, description FROM nodes WHERE name ILIKE %s OR description ILIKE %s LIMIT %s",
                    (f"%{request.query}%", f"%{request.query}%", request.limit),
                )

                rows = await cur.fetchall()
                results = [
                    {
                        "id": row[0],
                        "name": row[1],
                        "type": row[2],
                        "description": row[3],
                    }
                    for row in rows
                ]

        return {"results": results, "count": len(results)}

    except Exception as e:
        logger.error(f"Search failed: {e}")
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


@router.get("/nodes", response_model=PaginatedNodesResponse)
async def get_nodes(
    offset: int = 0,
    limit: int = Query(100, description="Maximum number of nodes to return"),
    node_type: str | None = Query(None, description="Filter by node type"),
) -> PaginatedNodesResponse:
    """Get nodes from the knowledge graph"""
    try:
        async with await psycopg.AsyncConnection.connect(
            config.database.connection_string
        ) as conn:
            async with conn.cursor() as cur:
                query = "SELECT id, name, type, description FROM nodes"
                count_query = "SELECT COUNT(*) FROM nodes"
                params: list[Any] = []

                if node_type:
                    query += " WHERE type = %s"
                    count_query += " WHERE type = %s"
                    params.append(node_type)

                await cur.execute(count_query, tuple(params) if node_type else None)
                total_result = await cur.fetchone()
                total = total_result[0] if total_result else 0

                query += " ORDER BY name LIMIT %s OFFSET %s"
                params.extend([limit, offset])
                await cur.execute(query, tuple(params))

                rows = await cur.fetchall()
                nodes = [
                    NodeResponse(
                        id=str(row[0]), name=row[1], type=row[2], description=row[3]
                    )
                    for row in rows
                ]

        return PaginatedNodesResponse(
            nodes=nodes, total=total, limit=limit, offset=offset
        )
    except Exception as e:
        logger.error(f"Failed to get nodes: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get nodes: {str(e)}")


@router.get("/edges", response_model=PaginatedEdgesResponse)
async def get_edges(
    offset: int = 0,
    limit: int = Query(100, description="Maximum number of edges to return"),
) -> PaginatedEdgesResponse:
    """Get edges from the knowledge graph"""
    try:
        async with await psycopg.AsyncConnection.connect(
            config.database.connection_string
        ) as conn:
            async with conn.cursor() as cur:
                query = "SELECT source_id, target_id, type, description, weight FROM edges ORDER BY source_id LIMIT %s OFFSET %s"
                await cur.execute(query, (limit, offset))
                rows = await cur.fetchall()
                edges = [
                    EdgeResponse(
                        source_id=str(row[0]),
                        target_id=str(row[1]),
                        type=row[2],
                        description=row[3],
                        weight=row[4],
                    )
                    for row in rows
                ]

                await cur.execute("SELECT COUNT(*) FROM edges")
                total_result = await cur.fetchone()
                total = total_result[0] if total_result else 0

        return PaginatedEdgesResponse(
            edges=edges, total=total, limit=limit, offset=offset
        )
    except Exception as e:
        logger.error(f"Failed to get edges: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get edges: {str(e)}")


@router.get("/graph")
async def get_graph_data(
    limit: int = Query(500, description="Maximum nodes/edges to return"),
) -> dict[str, Any]:
    """Get graph data for visualization"""
    try:
        async with await psycopg.AsyncConnection.connect(
            config.database.connection_string
        ) as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    "SELECT id, name, type, description FROM nodes LIMIT %s", (limit,)
                )
                node_rows = await cur.fetchall()

                await cur.execute(
                    "SELECT source_id, target_id, type, description, weight FROM edges LIMIT %s",
                    (limit,),
                )
                edge_rows = await cur.fetchall()

        nodes = [
            {"id": row[0], "name": row[1], "type": row[2], "description": row[3]}
            for row in node_rows
        ]

        edges = [
            {
                "source": row[0],
                "target": row[1],
                "type": row[2],
                "description": row[3],
                "weight": row[4],
            }
            for row in edge_rows
        ]

        return {"nodes": nodes, "edges": edges}

    except Exception as e:
        logger.error(f"Failed to get graph data: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to get graph data: {str(e)}"
        )

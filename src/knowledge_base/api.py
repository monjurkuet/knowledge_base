"""
Knowledge Base API - FastAPI endpoints for the GraphRAG system
"""

import logging
import os
from typing import Any
import psycopg
from dotenv import load_dotenv
from fastapi import FastAPI, File, HTTPException, Query, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from knowledge_base.community import CommunityDetector
from knowledge_base.config import get_config
from knowledge_base.pipeline import KnowledgePipeline
from knowledge_base.resolver import EntityResolver
from knowledge_base.summarizer import CommunitySummarizer

load_dotenv()

config = get_config()

# Configure logging
logging.basicConfig(
    level=getattr(logging, config.logging.level), format=config.logging.format
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Knowledge Base API",
    description="GraphRAG system for extracting and querying knowledge from text",
    version="1.0.0",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.api.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


_pipeline = None
_resolver = None
_community_detector = None
_summarizer = None


def get_pipeline():
    global _pipeline
    if _pipeline is None:
        _pipeline = KnowledgePipeline()
    return _pipeline


def get_resolver():
    global _resolver
    if _resolver is None:
        _resolver = EntityResolver(
            db_conn_str=config.database.connection_string,
            model_name=config.llm.model_name,
        )
    return _resolver


def get_community_detector():
    global _community_detector
    if _community_detector is None:
        _community_detector = CommunityDetector(
            db_conn_str=config.database.connection_string
        )
    return _community_detector


def get_summarizer():
    global _summarizer
    if _summarizer is None:
        _summarizer = CommunitySummarizer(
            config.database.connection_string, model_name=config.llm.model_name
        )
    return _summarizer


# Pydantic models for API requests/responses
class IngestTextRequest(BaseModel):
    text: str
    filename: str | None = "uploaded_text.txt"


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


class CommunityResponse(BaseModel):
    id: str
    title: str
    summary: str
    node_count: int


class StatsResponse(BaseModel):
    nodes_count: int
    edges_count: int
    communities_count: int
    events_count: int


# API Endpoints


@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "Knowledge Base API", "version": "1.0.0"}


@app.post("/api/ingest/text")
async def ingest_text(request: IngestTextRequest):
    """Ingest text content directly"""
    try:
        # Create a temporary file
        temp_file = f"/tmp/{request.filename}"
        with open(temp_file, "w", encoding="utf-8") as f:
            f.write(request.text)

        # Run the pipeline
        await get_pipeline().run(temp_file)

        # Clean up
        os.remove(temp_file)

        return {
            "status": "success",
            "message": f"Successfully ingested {len(request.text)} characters",
        }

    except Exception as e:
        logger.error(f"Ingestion failed: {e}")
        raise HTTPException(status_code=500, detail=f"Ingestion failed: {str(e)}")


@app.post("/api/ingest/file")
async def ingest_file(file: UploadFile = File(...)):
    """Upload and ingest a text file"""
    try:
        # Read file content
        content = await file.read()
        text = content.decode("utf-8")

        # Create temporary file
        temp_file = f"/tmp/{file.filename}"
        with open(temp_file, "w", encoding="utf-8") as f:
            f.write(text)

        # Run the pipeline
        await get_pipeline().run(temp_file)

        # Clean up
        os.remove(temp_file)

        return {
            "status": "success",
            "message": f"Successfully ingested file {file.filename}",
        }

    except Exception as e:
        logger.error(f"File ingestion failed: {e}")
        raise HTTPException(status_code=500, detail=f"File ingestion failed: {str(e)}")


@app.get("/api/stats", response_model=StatsResponse)
async def get_stats():
    """Get database statistics"""
    try:
        async with (
            await psycopg.AsyncConnection.connect(
                config.database.connection_string
            ) as conn,
            conn.cursor() as cur,
        ):
            # Get counts
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


class PaginatedCommunitiesResponse(BaseModel):
    communities: list[CommunityResponse]
    total: int
    limit: int
    offset: int


@app.get("/api/nodes", response_model=PaginatedNodesResponse)
async def get_nodes(
    offset: int = 0,
    limit: int = Query(100, description="Maximum number of nodes to return"),
    node_type: str | None = Query(None, description="Filter by node type"),
):
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

                # Get total count
                await cur.execute(count_query, tuple(params) if node_type else None)
                total_result = await cur.fetchone()
                total = total_result[0] if total_result else 0

                # Get paginated results
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


@app.get("/api/edges", response_model=PaginatedEdgesResponse)
async def get_edges(
    offset: int = 0,
    limit: int = Query(100, description="Maximum number of edges to return"),
):
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


@app.get("/api/communities", response_model=list[CommunityResponse])
async def get_communities():
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


@app.post("/api/search")
async def search_nodes(request: SearchRequest):
    """Search nodes using vector similarity"""
    try:
        # This is a simplified search - in production you'd use vector search
        async with await psycopg.AsyncConnection.connect(
            config.database.connection_string
        ) as conn:
            async with conn.cursor() as cur:
                # Simple text search for now
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


@app.get("/api/graph")
async def get_graph_data(
    limit: int = Query(500, description="Maximum nodes/edges to return"),
):
    """Get graph data for visualization"""
    try:
        async with await psycopg.AsyncConnection.connect(
            config.database.connection_string
        ) as conn:
            async with conn.cursor() as cur:
                # Get nodes
                await cur.execute(
                    "SELECT id, name, type, description FROM nodes LIMIT %s", (limit,)
                )
                node_rows = await cur.fetchall()

                # Get edges
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


@app.post("/api/community/detect")
async def detect_communities():
    """Run community detection on the current graph"""
    try:
        G = await get_community_detector().load_graph()
        if G.number_of_nodes() > 0:
            memberships = get_community_detector().detect_communities(G)
            await get_community_detector().save_communities(memberships)
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


@app.post("/api/summarize")
async def run_summarization():
    """Run recursive summarization on communities"""
    try:
        await get_summarizer().summarize_all()
        return {"status": "success", "message": "Summarization completed"}

    except Exception as e:
        logger.error(f"Summarization failed: {e}")
        raise HTTPException(status_code=500, detail=f"Summarization failed: {str(e)}")

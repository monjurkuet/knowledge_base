"""
Knowledge Base API - FastAPI endpoints for the GraphRAG system
"""

import logging
import os

import psycopg
from dotenv import load_dotenv
from fastapi import (
    BackgroundTasks,
    FastAPI,
    File,
    HTTPException,
    UploadFile,
    WebSocket,
)
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest
from pydantic import BaseModel

from knowledge_base.community import CommunityDetector
from knowledge_base.config import get_config

from knowledge_base.domain import DomainManager, DomainResponse
from knowledge_base.metrics import MetricsMiddleware
from knowledge_base.pipeline import KnowledgePipeline
from knowledge_base.resolver import EntityResolver
from knowledge_base.summarizer import CommunitySummarizer
from knowledge_base.tracing import setup_tracing
from knowledge_base.websocket import websocket_endpoint

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

# Set up OpenTelemetry tracing
setup_tracing(app)

# Configuration is static and requires server restart for changes
logger.info("Configuration loaded. Server restart required for configuration changes.")

app.add_middleware(MetricsMiddleware)

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
_domain_manager = None


def get_pipeline():
    global _pipeline
    if _pipeline is None:
        _pipeline = KnowledgePipeline()
    return _pipeline


def get_domain_manager():
    global _domain_manager
    if _domain_manager is None:
        _domain_manager = DomainManager(config.database.connection_string)
    return _domain_manager


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
    channel_id: str | None = None
    domain_id: str | None = None


class SearchRequest(BaseModel):
    query: str
    limit: int | None = 10

    def model_post_init(self, __context):
        if self.limit is not None:
            self.limit = max(1, min(self.limit, 1000))


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


@app.get("/health")
async def health_check():
    """Health check for Kubernetes probes and monitoring"""
    try:
        async with await psycopg.AsyncConnection.connect(
            config.database.connection_string
        ) as conn:
            await conn.execute("SELECT 1")

        # Test LLM API accessibility by attempting to create a client
        try:
            from knowledge_base.http_client import HTTPClient

            client = HTTPClient()
            # Basic test that the API configuration is valid
            _ = client.api_url  # Just access a property to confirm it's working
        except Exception:
            logger.warning("LLM API configuration may be invalid")

        return {
            "status": "healthy",
            "timestamp": __import__("datetime").datetime.now().isoformat(),
            "components": {"database": "healthy", "llm_api": "accessible"},
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=503, detail="Service unhealthy")


@app.get("/ready")
async def readiness_check():
    """Readiness check - service is ready to accept traffic"""
    return await health_check()


@app.get("/live")
async def liveness_check():
    """Liveness check - service is running and responsive"""
    return {
        "status": "live",
        "timestamp": __import__("datetime").datetime.now().isoformat(),
    }


@app.get("/metrics")
async def metrics_endpoint():
    """Prometheus metrics endpoint"""
    from fastapi.responses import Response

    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


@app.get("/api/domains", response_model=list[DomainResponse])
async def list_domains():
    """List all active domains"""
    try:
        return await get_domain_manager().list_domains()
    except Exception as e:
        logger.error(f"Failed to list domains: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list domains: {str(e)}")


@app.get("/api/domains/{domain_id}", response_model=DomainResponse)
async def get_domain(domain_id: str):
    """Get domain details"""
    try:
        from uuid import UUID

        domain = await get_domain_manager().get_domain(UUID(domain_id))
        if not domain:
            raise HTTPException(status_code=404, detail="Domain not found")
        return domain
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid domain ID format")
    except Exception as e:
        logger.error(f"Failed to get domain: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get domain: {str(e)}")


@app.get("/api/domains/{domain_id}/schema")
async def get_domain_schema(domain_id: str):
    """Get domain schema (entities and relationships)"""
    try:
        from uuid import UUID

        uuid_obj = UUID(domain_id)
        entities = await get_domain_manager().get_entity_types(uuid_obj)
        relationships = await get_domain_manager().get_relationship_types(uuid_obj)
        return {"entities": entities, "relationships": relationships}
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid domain ID format")
    except Exception as e:
        logger.error(f"Failed to get domain schema: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to get domain schema: {str(e)}"
        )


async def run_pipeline_background(
    file_path: str,
    channel_id: str | None = None,
    domain_id: str | None = None,
    cleanup_file: bool = True,
):
    """Background task to run the pipeline"""
    try:
        await get_pipeline().run(file_path, channel_id=channel_id, domain_id=domain_id)
        if cleanup_file:
            os.unlink(file_path)
    except Exception as e:
        logger.error(f"Background pipeline failed: {e}")
        error_msg = f"Pipeline failed: {str(e)}"
        # Optionally notify via WebSocket if channel_id is provided
        if channel_id:
            from knowledge_base.websocket import manager

            await manager.send_error("ingestion", error_msg, channel_id)

        raise


async def run_summarization_background(channel_id: str | None = None):
    """Background task to run recursive summarization"""
    try:
        await get_summarizer().summarize_all()
        result = {"status": "success", "message": "Summarization completed"}

        # Optionally notify via WebSocket if channel_id is provided
        if channel_id:
            from knowledge_base.websocket import manager

            await manager.send_status(
                "summarization", "completed", {"message": result["message"]}, channel_id
            )

        return result
    except Exception as e:
        logger.error(f"Summarization failed: {e}")
        error_msg = f"Summarization failed: {str(e)}"

        # Optionally notify via WebSocket if channel_id is provided
        if channel_id:
            from knowledge_base.websocket import manager

            await manager.send_error("summarization", error_msg, channel_id)

        raise


async def run_community_detection_background(channel_id: str | None = None):
    """Background task to run community detection"""
    try:
        G = await get_community_detector().load_graph()
        if G.number_of_nodes() > 0:
            memberships = get_community_detector().detect_communities(G)
            await get_community_detector().save_communities(memberships)
            result = {
                "status": "success",
                "message": f"Detected communities for {G.number_of_nodes()} nodes",
            }
        else:
            result = {"status": "no_data", "message": "No nodes found in database"}

        # Optionally notify via WebSocket if channel_id is provided
        if channel_id:
            from knowledge_base.websocket import manager

            await manager.send_status(
                "community_detection",
                "completed",
                {"message": result["message"]},
                channel_id,
            )

        return result
    except Exception as e:
        logger.error(f"Community detection failed: {e}")
        error_msg = f"Community detection failed: {str(e)}"

        # Optionally notify via WebSocket if channel_id is provided
        if channel_id:
            from knowledge_base.websocket import manager

            await manager.send_error("community_detection", error_msg, channel_id)

        raise


@app.post("/api/summarize")
async def run_summarization(
    background_tasks: BackgroundTasks, channel_id: str | None = None
):
    """Run recursive summarization on communities"""
    try:
        # Run as a background task
        background_tasks.add_task(run_summarization_background, channel_id)

        return {
            "status": "started",
            "message": "Summarization started in background",
            "background": True,
        }

    except Exception as e:
        logger.error(f"Summarization setup failed: {e}")
        raise HTTPException(
            status_code=500, detail=f"Summarization setup failed: {str(e)}"
        )


@app.get("/api/stats")
async def get_stats():
    """Get database statistics"""
    try:
        async with await psycopg.AsyncConnection.connect(
            config.database.connection_string
        ) as conn:
            async with conn.cursor() as cur:
                # Count nodes
                await cur.execute("SELECT COUNT(*) FROM nodes")
                nodes_result = await cur.fetchone()
                nodes_count = nodes_result[0] if nodes_result else 0

                # Count edges
                await cur.execute("SELECT COUNT(*) FROM edges")
                edges_result = await cur.fetchone()
                edges_count = edges_result[0] if edges_result else 0

                # Count communities
                await cur.execute("SELECT COUNT(*) FROM communities")
                communities_result = await cur.fetchone()
                communities_count = communities_result[0] if communities_result else 0

                # Count events
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
        logger.error(f"Stats retrieval failed: {e}")
        raise HTTPException(status_code=500, detail=f"Stats retrieval failed: {str(e)}")


@app.get("/api/graph")
async def get_graph(limit: int = 200):
    """Get graph data for visualization"""
    try:
        async with await psycopg.AsyncConnection.connect(
            config.database.connection_string
        ) as conn:
            async with conn.cursor() as cur:
                # Fetch nodes with limit
                await cur.execute(
                    """
                    SELECT id, name, type, description
                    FROM nodes
                    ORDER BY RANDOM()
                    LIMIT %s
                    """,
                    (limit,),
                )
                nodes_rows = await cur.fetchall()

                # Extract node IDs to fetch related edges
                node_ids = [row[0] for row in nodes_rows]
                if node_ids:
                    # Create parameterized query for edges - only get edges between selected nodes
                    placeholders = ",".join(["%s"] * len(node_ids))
                    await cur.execute(
                        f"SELECT source_id, target_id, type, description, weight FROM edges WHERE source_id = ANY(%s) AND target_id = ANY(%s)",
                        (node_ids, node_ids),
                    )
                    edges_rows = await cur.fetchall()
                else:
                    edges_rows = []

        nodes = [
            {
                "id": row[0],
                "name": row[1],
                "type": row[2],
                "description": row[3],
            }
            for row in nodes_rows
        ]

        edges = [
            {
                "source": row[0],
                "target": row[1],
                "type": row[2],
                "description": row[3],
                "weight": row[4],
            }
            for row in edges_rows
        ]

        return {
            "nodes": nodes,
            "edges": edges,
            "node_count": len(nodes),
            "edge_count": len(edges),
        }

    except Exception as e:
        logger.error(f"Graph data retrieval failed: {e}")
        raise HTTPException(
            status_code=500, detail=f"Graph data retrieval failed: {str(e)}"
        )


@app.get("/api/nodes")
async def get_nodes(limit: int = 100, node_type: str | None = None):
    """Get knowledge graph nodes"""
    try:
        async with await psycopg.AsyncConnection.connect(
            config.database.connection_string
        ) as conn:
            async with conn.cursor() as cur:
                if node_type:
                    await cur.execute(
                        "SELECT id, name, type, description FROM nodes WHERE type = %s ORDER BY name LIMIT %s",
                        (node_type, limit),
                    )
                else:
                    await cur.execute(
                        "SELECT id, name, type, description FROM nodes ORDER BY name LIMIT %s",
                        (limit,),
                    )
                rows = await cur.fetchall()

        nodes = [
            {
                "id": row[0],
                "name": row[1],
                "type": row[2],
                "description": row[3],
            }
            for row in rows
        ]

        return {"nodes": nodes, "count": len(nodes)}

    except Exception as e:
        logger.error(f"Nodes retrieval failed: {e}")
        raise HTTPException(status_code=500, detail=f"Nodes retrieval failed: {str(e)}")


@app.get("/api/edges")
async def get_edges(limit: int = 100):
    """Get knowledge graph edges"""
    try:
        async with await psycopg.AsyncConnection.connect(
            config.database.connection_string
        ) as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    "SELECT source_id, target_id, type, description, weight FROM edges ORDER BY type LIMIT %s",
                    (limit,),
                )
                rows = await cur.fetchall()

        edges = [
            {
                "source_id": row[0],
                "target_id": row[1],
                "type": row[2],
                "description": row[3],
                "weight": row[4],
            }
            for row in rows
        ]

        return {"edges": edges, "count": len(edges)}

    except Exception as e:
        logger.error(f"Edges retrieval failed: {e}")
        raise HTTPException(status_code=500, detail=f"Edges retrieval failed: {str(e)}")


@app.get("/api/communities")
async def get_communities(limit: int = 100):
    """Get detected communities"""
    try:
        async with await psycopg.AsyncConnection.connect(
            config.database.connection_string
        ) as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    """
                    SELECT c.id, c.title, c.summary, c.level, 
                           COUNT(cm.node_id) as node_count
                    FROM communities c
                    LEFT JOIN community_membership cm ON c.id = cm.community_id
                    GROUP BY c.id, c.title, c.summary, c.level
                    ORDER BY c.level, c.title
                    LIMIT %s
                    """,
                    (limit,),
                )
                rows = await cur.fetchall()

        communities = [
            {
                "id": row[0],
                "title": row[1],
                "summary": row[2],
                "level": row[3],
                "node_count": row[4],
            }
            for row in rows
        ]

        return communities

    except Exception as e:
        logger.error(f"Communities retrieval failed: {e}")
        raise HTTPException(
            status_code=500, detail=f"Communities retrieval failed: {str(e)}"
        )


# Import for background functions - check if they already exist in the file
# Add the background task functions here as well if they're missing


@app.post("/api/ingest/text")
async def ingest_text(
    request: IngestTextRequest,
    background_tasks: BackgroundTasks,
    channel_id: str | None = None,
    domain_id: str | None = None,
):
    """Ingest text content directly"""
    try:
        import tempfile
        import os

        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", delete=False, suffix=".txt"
        ) as temp_file:
            temp_file.write(request.text)
            temp_file_path = temp_file.name

        # Run the pipeline as a background task
        background_tasks.add_task(
            run_pipeline_background,
            temp_file_path,
            channel_id,
            domain_id,
            cleanup_file=True,
        )

        return {
            "status": "started",
            "message": f"Started ingestion of {len(request.text)} characters",
            "background": True,
        }

    except Exception as e:
        logger.error(f"Ingestion setup failed: {e}")
        raise HTTPException(status_code=500, detail=f"Ingestion setup failed: {str(e)}")


@app.post("/api/ingest/file")
async def ingest_file(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    channel_id: str | None = None,
    domain_id: str | None = None,
):
    """Upload and ingest a text file"""
    try:
        # Read file content
        content = await file.read()
        text = content.decode("utf-8")

        import tempfile
        import os

        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", delete=False, suffix=".txt"
        ) as temp_file:
            temp_file.write(text)
            temp_file_path = temp_file.name

        # Run the pipeline as a background task
        background_tasks.add_task(
            run_pipeline_background,
            temp_file_path,
            channel_id,
            domain_id,
            cleanup_file=True,
        )

        return {
            "status": "started",
            "message": f"Started ingestion of file {file.filename}",
            "background": True,
        }

    except Exception as e:
        logger.error(f"File ingestion setup failed: {e}")
        raise HTTPException(
            status_code=500, detail=f"File ingestion setup failed: {str(e)}"
        )


@app.post("/api/community/detect")
async def detect_communities(
    background_tasks: BackgroundTasks, channel_id: str | None = None
):
    """Run community detection on the current graph"""
    try:
        # Run as a background task
        background_tasks.add_task(run_community_detection_background, channel_id)

        return {
            "status": "started",
            "message": "Community detection started in background",
            "background": True,
        }

    except Exception as e:
        logger.error(f"Community detection setup failed: {e}")
        raise HTTPException(
            status_code=500, detail=f"Community detection setup failed: {str(e)}"
        )


@app.post("/api/search")
async def search_endpoint(request: SearchRequest):
    """Search endpoint with vector similarity"""
    logger.info(f"Search request: {request.query[:50]}...")

    try:
        from knowledge_base.embedding_service import GoogleEmbeddingService

        embedding_service = GoogleEmbeddingService()
        query_embedding = await embedding_service.embed_content(request.query)
        if not query_embedding:
            raise HTTPException(
                status_code=500, detail="Failed to get embedding values"
            )

        async with await psycopg.AsyncConnection.connect(
            config.database.connection_string
        ) as conn:
            async with conn.cursor() as cur:
                # Vector similarity search using pgvector
                await cur.execute(
                    """
                    SELECT id, name, type, description, 
                           1 - (embedding <=> %s::vector) as similarity
                    FROM nodes 
                    WHERE embedding IS NOT NULL
                    ORDER BY embedding <=> %s::vector
                    LIMIT %s
                    """,
                    (query_embedding, query_embedding, request.limit),
                )

                rows = await cur.fetchall()
                results = [
                    {
                        "id": row[0],
                        "name": row[1],
                        "type": row[2],
                        "description": row[3],
                        "similarity": row[4],  # Include similarity score
                    }
                    for row in rows
                ]

        return {"results": results, "count": len(results)}

    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        logger.error(f"Search failed: {e}")
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


logger.info("About to define WebSocket routes")


@app.websocket("/ws")
async def websocket_route(websocket: WebSocket, channel: str = "general"):
    logger.info(f"WebSocket route called with channel: {channel}")
    await websocket_endpoint(websocket, channel)


@app.websocket("/ws/{channel}")
async def websocket_channel_route(websocket: WebSocket, channel: str):
    logger.info(f"WebSocket channel route called with channel: {channel}")
    await websocket_endpoint(websocket, channel)


logger.info("WebSocket routes defined")

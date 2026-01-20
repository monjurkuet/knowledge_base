"""
FastAPI application initialization
"""

import logging

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware

from knowledge_base.config import get_config
from knowledge_base.utils.errors import (
    DatabaseError,
    KnowledgeBaseError,
    LLMError,
)

from .middleware import (
    database_exception_handler,
    generic_exception_handler,
    knowledge_base_exception_handler,
    llm_exception_handler,
    validation_exception_handler,
)
from .routes import community, domain, health, ingest, search, stats, websocket

config = get_config()
logger = logging.getLogger(__name__)


def create_app() -> FastAPI:
    """Create and configure FastAPI application."""
    app = FastAPI(
        title="Knowledge Base API",
        description="GraphRAG system for extracting and querying knowledge from text",
        version="1.0.0",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=config.api.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.add_exception_handler(KnowledgeBaseError, knowledge_base_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(DatabaseError, database_exception_handler)
    app.add_exception_handler(LLMError, llm_exception_handler)
    app.add_exception_handler(Exception, generic_exception_handler)

    app.include_router(domain.router, prefix="/api/domains", tags=["domains"])
    app.include_router(ingest.router, prefix="/api/ingest", tags=["ingestion"])
    app.include_router(search.router, prefix="/api", tags=["search"])
    app.include_router(community.router, prefix="/api/community", tags=["community"])
    app.include_router(stats.router, prefix="/api/stats", tags=["stats"])
    app.include_router(health.router, prefix="/api", tags=["health"])
    app.include_router(websocket.router, tags=["websocket"])

    @app.get("/")
    async def root() -> dict[str, str]:
        return {"message": "Knowledge Base API", "version": "1.0.0"}

    return app


app = create_app()

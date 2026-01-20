"""
Health check endpoint
"""

import time
from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel

from knowledge_base.config import get_config
from knowledge_base.utils.logging_config import get_logger

logger = get_logger(__name__)
router = APIRouter()


class HealthResponse(BaseModel):
    """Health check response model."""

    status: str
    version: str
    uptime_seconds: float
    database: str
    timestamp: str


class DatabaseHealth(BaseModel):
    """Database health status."""

    status: str
    connection_time_ms: float | None = None
    error: str | None = None


start_time = time.time()


@router.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """
    Health check endpoint.
    Returns service health status and version information.
    """
    uptime = time.time() - start_time
    config = get_config()

    # Check database connection
    db_status = "healthy"
    try:
        import psycopg

        start = time.time()
        async with await psycopg.AsyncConnection.connect(
            config.database.connection_string
        ) as conn:
            async with conn.cursor() as cur:
                await cur.execute("SELECT 1")
        db_connection_time = (time.time() - start) * 1000
        logger.info(
            "health_check",
            status="healthy",
            db_connection_time_ms=db_connection_time,
            uptime_seconds=uptime,
        )
    except Exception as e:
        db_status = "unhealthy"
        logger.error(
            "health_check", status="unhealthy", error=str(e), uptime_seconds=uptime
        )

    return HealthResponse(
        status="healthy" if db_status == "healthy" else "degraded",
        version="1.0.0",
        uptime_seconds=uptime,
        database=db_status,
        timestamp=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    )


@router.get("/health/db", response_model=DatabaseHealth)
async def database_health_check() -> DatabaseHealth:
    """
    Database health check endpoint.
    Tests database connection and returns timing information.
    """
    config = get_config()

    try:
        import psycopg

        start = time.time()

        async with await psycopg.AsyncConnection.connect(
            config.database.connection_string
        ) as conn:
            async with conn.cursor() as cur:
                await cur.execute("SELECT 1")
                await cur.fetchone()

        connection_time = (time.time() - start) * 1000

        logger.info(
            "database_health_check",
            status="healthy",
            connection_time_ms=connection_time,
        )

        return DatabaseHealth(
            status="healthy", connection_time_ms=connection_time, error=None
        )
    except Exception as e:
        logger.error("database_health_check", status="unhealthy", error=str(e))

        return DatabaseHealth(status="unhealthy", connection_time_ms=None, error=str(e))


@router.get("/metrics")
async def metrics() -> dict[str, Any]:
    """
    Basic metrics endpoint.
    Returns simple application metrics.
    """
    import psutil
    import os

    process = psutil.Process(os.getpid())

    uptime = time.time() - start_time

    return {
        "uptime_seconds": uptime,
        "memory_usage_mb": process.memory_info().rss / 1024 / 1024,
        "cpu_percent": process.cpu_percent(),
        "thread_count": process.num_threads(),
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }

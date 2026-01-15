"""
Main API server for the Knowledge Base GraphRAG system
Combines FastAPI endpoints with WebSocket support for real-time updates
"""

import logging

import uvicorn

from knowledge_base.api import app as fastapi_app
from knowledge_base.config import get_config
from knowledge_base.websocket import websocket_endpoint

config = get_config()

logging.basicConfig(
    level=getattr(logging, config.logging.level), format=config.logging.format
)
logger = logging.getLogger(__name__)


@fastapi_app.websocket("/ws")
async def websocket_route(websocket, channel: str = "general"):
    """WebSocket endpoint for real-time updates"""
    await websocket_endpoint(websocket, channel)


@fastapi_app.websocket("/ws/{channel}")
async def websocket_channel_route(websocket, channel: str):
    """WebSocket endpoint for specific channels"""
    await websocket_endpoint(websocket, channel)


def main():
    """Main entry point for the API server"""
    logger.info("Starting Knowledge Base API server...")

    logger.info(
        f"Server will be available at http://{config.api.host}:{config.api.port}"
    )
    logger.info(f"WebSocket endpoints: ws://{config.api.host}:{config.api.port}/ws")
    logger.info(f"API documentation: http://{config.api.host}:{config.api.port}/docs")

    uvicorn.run(
        "knowledge_base.main_api:fastapi_app",
        host=config.api.host,
        port=config.api.port,
        reload=config.api.reload,
        log_level=config.logging.level.lower(),
    )


if __name__ == "__main__":
    main()

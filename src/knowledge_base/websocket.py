"""
WebSocket implementation for real-time updates in the Knowledge Base API
"""

import asyncio
import json
import logging

from fastapi import WebSocket, WebSocketDisconnect

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Manages WebSocket connections and broadcasts messages"""

    def __init__(self):
        self.active_connections: dict[str, set[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, channel: str = "general"):
        """Connect a WebSocket to a specific channel"""
        await websocket.accept()

        if channel not in self.active_connections:
            self.active_connections[channel] = set()

        self.active_connections[channel].add(websocket)
        logger.info(
            f"WebSocket connected to channel '{channel}'. Total connections: {len(self.active_connections[channel])}"
        )

    def disconnect(self, websocket: WebSocket, channel: str = "general"):
        """Disconnect a WebSocket from a channel"""
        if channel in self.active_connections:
            self.active_connections[channel].discard(websocket)
            logger.info(
                f"WebSocket disconnected from channel '{channel}'. Remaining connections: {len(self.active_connections[channel])}"
            )

            if not self.active_connections[channel]:
                del self.active_connections[channel]

    async def broadcast(self, message: dict, channel: str = "general"):
        """Broadcast a message to all connections in a channel"""
        if channel not in self.active_connections:
            return

        disconnected = set()
        message_json = json.dumps(message)

        for connection in self.active_connections[channel]:
            try:
                await connection.send_text(message_json)
            except Exception as e:
                logger.warning(f"Failed to send message to connection: {e}")
                disconnected.add(connection)

        for connection in disconnected:
            self.disconnect(connection, channel)

    async def send_progress(
        self, operation: str, progress: float, message: str, channel: str = "general"
    ):
        """Send progress update"""
        await self.broadcast(
            {
                "type": "progress",
                "operation": operation,
                "progress": progress,
                "message": message,
                "timestamp": asyncio.get_event_loop().time(),
            },
            channel,
        )

    async def send_status(
        self,
        operation: str,
        status: str,
        details: dict | None = None,
        channel: str = "general",
    ):
        """Send status update"""
        message = {
            "type": "status",
            "operation": operation,
            "status": status,
            "timestamp": asyncio.get_event_loop().time(),
        }
        if details:
            message.update(details)

        await self.broadcast(message, channel)

    async def send_error(self, operation: str, error: str, channel: str = "general"):
        """Send error message"""
        await self.broadcast(
            {
                "type": "error",
                "operation": operation,
                "error": error,
                "timestamp": asyncio.get_event_loop().time(),
            },
            channel,
        )


manager = ConnectionManager()


async def websocket_endpoint(websocket: WebSocket, channel: str = "general"):
    """WebSocket endpoint for real-time updates"""
    await manager.connect(websocket, channel)

    try:
        await websocket.send_text(
            json.dumps(
                {
                    "type": "connection",
                    "status": "connected",
                    "channel": channel,
                    "timestamp": asyncio.get_event_loop().time(),
                }
            )
        )
    except Exception as e:
        logger.warning(f"Failed to send connection acknowledgment: {e}")

    try:
        while True:
            data = await websocket.receive_text()
            try:
                message = json.loads(data)
                logger.debug(f"Received message from client: {message}")
                await websocket.send_text(
                    json.dumps(
                        {
                            "type": "echo",
                            "data": message,
                            "timestamp": asyncio.get_event_loop().time(),
                        }
                    )
                )
            except json.JSONDecodeError:
                logger.warning(f"Invalid JSON received: {data}")
                await websocket.send_text(
                    json.dumps(
                        {
                            "type": "echo",
                            "data": data,
                            "timestamp": asyncio.get_event_loop().time(),
                        }
                    )
                )

    except WebSocketDisconnect:
        manager.disconnect(websocket, channel)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(websocket, channel)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(websocket, channel)


class ProgressTracker:
    """Tracks progress of long-running operations"""

    def __init__(self, operation: str, channel: str = "general"):
        self.operation = operation
        self.channel = channel
        self.start_time = asyncio.get_event_loop().time()

    async def update_progress(self, progress: float, message: str):
        """Update progress (0.0 to 1.0)"""
        await manager.send_progress(self.operation, progress, message, self.channel)

    async def update_status(self, status: str, details: dict | None = None):
        """Update operation status"""
        await manager.send_status(self.operation, status, details, self.channel)

    async def report_error(self, error: str):
        """Report an error"""
        await manager.send_error(self.operation, error, self.channel)

    async def complete(self, details: dict | None = None):
        """Mark operation as completed"""
        elapsed = asyncio.get_event_loop().time() - self.start_time
        details = details or {}
        details["elapsed_time"] = elapsed

        await manager.send_status(self.operation, "completed", details, self.channel)

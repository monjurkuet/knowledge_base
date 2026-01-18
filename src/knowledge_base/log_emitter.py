"""
Utility for emitting real-time log messages via WebSockets.
"""

import logging

from knowledge_base.websocket import manager

logger = logging.getLogger(__name__)


async def emit_log(channel_id: str, message: str, log_type: str = "info"):
    """
    Emits a structured log message to a specific WebSocket channel.

    Args:
        channel_id: The WebSocket channel to send the message to.
        message: The log message content.
        log_type: The type of log (e.g., 'info', 'warning', 'error', 'success').
    """
    if not channel_id:
        return

    log_payload = {
        "type": "log",
        "data": {
            "message": message,
            "log_type": log_type,
        },
    }

    try:
        await manager.broadcast(log_payload, channel=channel_id)
        logger.debug(f"Emitted log to channel '{channel_id}': {message}")
    except Exception as e:
        logger.error(f"Failed to emit log to channel '{channel_id}': {e}")

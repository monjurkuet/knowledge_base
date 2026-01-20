"""
Route modules for API endpoints
"""

from . import community, domain, health, ingest, search, stats, websocket

__all__ = ["domain", "ingest", "search", "community", "stats", "websocket", "health"]

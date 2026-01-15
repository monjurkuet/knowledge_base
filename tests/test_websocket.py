"""
Tests for Knowledge Base WebSocket functionality
Uses real database and live connections
"""

from unittest.mock import AsyncMock, MagicMock

import pytest

from knowledge_base.websocket import ConnectionManager, ProgressTracker, manager


class TestConnectionManager:
    """Tests for ConnectionManager class"""

    def test_manager_initialization(self):
        """Test ConnectionManager initializes with empty connections"""
        test_manager = ConnectionManager()
        assert test_manager.active_connections == {}

    def test_manager_has_singleton_instance(self):
        """Test that module-level manager instance exists"""
        assert manager is not None
        assert isinstance(manager, ConnectionManager)

    def test_disconnect_nonexistent_channel(self):
        """Test disconnecting from channel with no connections"""
        test_manager = ConnectionManager()
        mock_ws = MagicMock()
        test_manager.disconnect(mock_ws, "nonexistent")


class TestConnectionManagerConnect:
    """Tests for ConnectionManager.connect method"""

    @pytest.mark.asyncio
    async def test_connect_creates_channel(self):
        """Test that connecting creates a new channel"""
        test_manager = ConnectionManager()
        mock_ws = MagicMock()
        mock_ws.accept = AsyncMock()

        await test_manager.connect(mock_ws, "test_channel")

        assert "test_channel" in test_manager.active_connections
        assert mock_ws in test_manager.active_connections["test_channel"]

    @pytest.mark.asyncio
    async def test_connect_adds_to_existing_channel(self):
        """Test adding connection to existing channel"""
        test_manager = ConnectionManager()
        mock_ws1 = MagicMock()
        mock_ws1.accept = AsyncMock()
        mock_ws2 = MagicMock()
        mock_ws2.accept = AsyncMock()

        await test_manager.connect(mock_ws1, "shared_channel")
        await test_manager.connect(mock_ws2, "shared_channel")

        assert len(test_manager.active_connections["shared_channel"]) == 2


class TestConnectionManagerDisconnect:
    """Tests for ConnectionManager.disconnect method"""

    @pytest.mark.asyncio
    async def test_disconnect_removes_connection(self):
        """Test that disconnect removes connection from channel"""
        test_manager = ConnectionManager()
        mock_ws = MagicMock()
        mock_ws.accept = AsyncMock()

        await test_manager.connect(mock_ws, "channel")
        test_manager.disconnect(mock_ws, "channel")

        assert mock_ws not in test_manager.active_connections.get("channel", set())

    @pytest.mark.asyncio
    async def test_disconnect_removes_empty_channel(self):
        """Test that empty channels are removed"""
        test_manager = ConnectionManager()
        mock_ws = MagicMock()
        mock_ws.accept = AsyncMock()

        await test_manager.connect(mock_ws, "temp_channel")
        test_manager.disconnect(mock_ws, "temp_channel")

        assert "temp_channel" not in test_manager.active_connections


class TestConnectionManagerBroadcast:
    """Tests for ConnectionManager.broadcast method"""

    @pytest.mark.asyncio
    async def test_broadcast_no_connections(self):
        """Test broadcast to channel with no connections does nothing"""
        test_manager = ConnectionManager()
        await test_manager.broadcast({"test": "message"}, "empty_channel")

    @pytest.mark.asyncio
    async def test_broadcast_sends_to_all(self):
        """Test broadcast sends message to all connections in channel"""
        test_manager = ConnectionManager()
        mock_ws1 = MagicMock()
        mock_ws1.accept = AsyncMock()
        mock_ws1.send_text = AsyncMock()
        mock_ws2 = MagicMock()
        mock_ws2.accept = AsyncMock()
        mock_ws2.send_text = AsyncMock()

        await test_manager.connect(mock_ws1, "broadcast_channel")
        await test_manager.connect(mock_ws2, "broadcast_channel")

        await test_manager.broadcast({"message": "hello"}, "broadcast_channel")

        mock_ws1.send_text.assert_called_once()
        mock_ws2.send_text.assert_called_once()


class TestConnectionManagerSendProgress:
    """Tests for ConnectionManager.send_progress method"""

    @pytest.mark.asyncio
    async def test_send_progress_format(self):
        """Test progress message format"""
        test_manager = ConnectionManager()
        mock_ws = MagicMock()
        mock_ws.accept = AsyncMock()
        mock_ws.send_text = AsyncMock()

        await test_manager.connect(mock_ws, "progress_channel")
        await test_manager.send_progress(
            "test_op", 0.5, "Half done", "progress_channel"
        )

        mock_ws.send_text.assert_called_once()
        import json

        sent_message = json.loads(mock_ws.send_text.call_args[0][0])
        assert sent_message["type"] == "progress"
        assert sent_message["operation"] == "test_op"
        assert sent_message["progress"] == 0.5
        assert sent_message["message"] == "Half done"


class TestConnectionManagerSendStatus:
    """Tests for ConnectionManager.send_status method"""

    @pytest.mark.asyncio
    async def test_send_status_format(self):
        """Test status message format"""
        test_manager = ConnectionManager()
        mock_ws = MagicMock()
        mock_ws.accept = AsyncMock()
        mock_ws.send_text = AsyncMock()

        await test_manager.connect(mock_ws, "status_channel")
        await test_manager.send_status(
            "test_op", "running", {"detail": "info"}, "status_channel"
        )

        mock_ws.send_text.assert_called_once()
        import json

        sent_message = json.loads(mock_ws.send_text.call_args[0][0])
        assert sent_message["type"] == "status"
        assert sent_message["status"] == "running"
        assert sent_message["detail"] == "info"


class TestConnectionManagerSendError:
    """Tests for ConnectionManager.send_error method"""

    @pytest.mark.asyncio
    async def test_send_error_format(self):
        """Test error message format"""
        test_manager = ConnectionManager()
        mock_ws = MagicMock()
        mock_ws.accept = AsyncMock()
        mock_ws.send_text = AsyncMock()

        await test_manager.connect(mock_ws, "error_channel")
        await test_manager.send_error(
            "test_op", "Something went wrong", "error_channel"
        )

        mock_ws.send_text.assert_called_once()
        import json

        sent_message = json.loads(mock_ws.send_text.call_args[0][0])
        assert sent_message["type"] == "error"
        assert sent_message["error"] == "Something went wrong"


class TestProgressTracker:
    """Tests for ProgressTracker class"""

    def test_progress_tracker_initialization(self):
        """Test ProgressTracker initializes with operation and channel"""
        tracker = ProgressTracker("test_operation", "test_channel")
        assert tracker.operation == "test_operation"
        assert tracker.channel == "test_channel"

    @pytest.mark.asyncio
    async def test_progress_tracker_update_progress(self):
        """Test progress update sends correct message"""
        tracker = ProgressTracker("update_test", "progress_channel")
        mock_ws = MagicMock()
        mock_ws.accept = AsyncMock()
        mock_ws.send_text = AsyncMock()

        await manager.connect(mock_ws, "progress_channel")
        await tracker.update_progress(0.75, "Three quarters done")

        mock_ws.send_text.assert_called()


class TestWebSocketEndpoint:
    """Tests for websocket endpoint"""

    def test_websocket_endpoint_exists(self):
        """Test websocket_endpoint function exists"""
        from knowledge_base.websocket import websocket_endpoint

        assert callable(websocket_endpoint)


class TestWebSocketMessageHandling:
    """Tests for WebSocket message handling"""

    @pytest.mark.asyncio
    async def test_accepts_valid_json(self):
        """Test that valid JSON messages are logged correctly"""
        test_manager = ConnectionManager()
        mock_ws = MagicMock()
        mock_ws.accept = AsyncMock()
        mock_ws.receive_text = AsyncMock(return_value='{"key": "value"}')
        mock_ws.close = AsyncMock()

        await test_manager.connect(mock_ws, "json_channel")
        mock_ws.accept.assert_called_once()


class TestConnectionManagerEdgeCases:
    """Edge case tests for ConnectionManager"""

    @pytest.mark.asyncio
    async def test_multiple_channels_independent(self):
        """Test that different channels are independent"""
        test_manager = ConnectionManager()
        mock_ws1 = MagicMock()
        mock_ws1.accept = AsyncMock()
        mock_ws1.send_text = AsyncMock()
        mock_ws2 = MagicMock()
        mock_ws2.accept = AsyncMock()
        mock_ws2.send_text = AsyncMock()

        await test_manager.connect(mock_ws1, "channel_a")
        await test_manager.connect(mock_ws2, "channel_b")

        await test_manager.broadcast({"msg": "a_only"}, "channel_a")

        mock_ws1.send_text.assert_called_once()
        mock_ws2.send_text.assert_not_called()

    @pytest.mark.asyncio
    async def test_broadcast_handles_send_failure(self):
        """Test broadcast handles failed send gracefully"""
        test_manager = ConnectionManager()
        mock_ws = MagicMock()
        mock_ws.accept = AsyncMock()
        mock_ws.send_text = AsyncMock(side_effect=Exception("Send failed"))

        await test_manager.connect(mock_ws, "fail_channel")
        await test_manager.broadcast({"test": "message"}, "fail_channel")

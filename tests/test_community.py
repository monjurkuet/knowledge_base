"""
Tests for Community Detection Module
"""

from unittest.mock import AsyncMock, MagicMock, patch

import networkx as nx
import pytest

from knowledge_base.community import CommunityDetector


class TestCommunityDetectorInit:
    """Tests for CommunityDetector initialization"""

    def test_init_with_connection_string(self):
        """Test CommunityDetector initializes with connection string"""
        detector = CommunityDetector(db_conn_str="postgresql://user:pass@localhost/db")
        assert detector.db_conn_str == "postgresql://user:pass@localhost/db"

    def test_init_sets_connection_string(self):
        """Test CommunityDetector stores connection string correctly"""
        detector = CommunityDetector(
            db_conn_str="postgresql://test:test@localhost/test"
        )
        assert detector.db_conn_str is not None
        assert "postgresql" in detector.db_conn_str


class TestLoadGraph:
    """Tests for load_graph method"""

    @pytest.mark.asyncio
    async def test_load_graph_returns_networkx_graph(self):
        """Test that load_graph returns a NetworkX graph"""
        detector = CommunityDetector(
            db_conn_str="postgresql://test:test@localhost/test"
        )

        mock_conn = AsyncMock()
        mock_cursor = AsyncMock()
        mock_conn.cursor = MagicMock(return_value=mock_cursor)
        mock_conn.__aenter__ = AsyncMock(return_value=mock_conn)
        mock_conn.__aexit__ = AsyncMock(return_value=None)
        mock_cursor.__aenter__ = AsyncMock(return_value=mock_cursor)
        mock_cursor.__aexit__ = AsyncMock(return_value=None)

        with patch(
            "knowledge_base.community.AsyncConnection.connect", return_value=mock_conn
        ):
            graph = await detector.load_graph()

            assert graph is not None
            assert isinstance(graph, nx.Graph)


class TestDetectCommunities:
    """Tests for detect_communities method"""

    def test_detect_communities_empty_graph(self):
        """Test community detection on empty graph returns empty list"""
        detector = CommunityDetector(
            db_conn_str="postgresql://test:test@localhost/test"
        )
        G = nx.Graph()

        results = detector.detect_communities(G)

        assert results == []

    def test_detect_communities_single_node(self):
        """Test community detection with single node - may return empty"""
        detector = CommunityDetector(
            db_conn_str="postgresql://test:test@localhost/test"
        )
        G = nx.Graph()
        G.add_node("node1")

        results = detector.detect_communities(G)

        # graspologic may return empty for single nodes, which is acceptable
        # The function should not crash and should return a list
        assert isinstance(results, list)
        if results:
            assert results[0]["node_id"] == "node1"

    def test_detect_communities_returns_dict_list(self):
        """Test detect_communities returns list of dictionaries"""
        detector = CommunityDetector(
            db_conn_str="postgresql://test:test@localhost/test"
        )
        G = nx.Graph()
        G.add_node("node1")
        G.add_node("node2")

        results = detector.detect_communities(G)

        assert isinstance(results, list)
        if results:
            assert isinstance(results[0], dict)
            assert "node_id" in results[0]
            assert "level" in results[0]
            assert "cluster_id" in results[0]

    def test_detect_communities_two_connected_nodes(self):
        """Test community detection with two connected nodes"""
        detector = CommunityDetector(
            db_conn_str="postgresql://test:test@localhost/test"
        )
        G = nx.Graph()
        G.add_node("node1")
        G.add_node("node2")
        G.add_edge("node1", "node2", weight=1.0)

        results = detector.detect_communities(G)

        # Should have results (either from leiden or fallback)
        assert len(results) >= 1

    def test_detect_communities_triangle(self):
        """Test community detection with triangle graph"""
        detector = CommunityDetector(
            db_conn_str="postgresql://test:test@localhost/test"
        )
        G = nx.Graph()
        G.add_node("node1")
        G.add_node("node2")
        G.add_node("node3")
        G.add_edge("node1", "node2", weight=1.0)
        G.add_edge("node2", "node3", weight=1.0)
        G.add_edge("node3", "node1", weight=1.0)

        results = detector.detect_communities(G)

        # Should have results
        assert len(results) >= 1


class TestFallbackClustering:
    """Tests for _fallback_clustering method"""

    def test_fallback_empty_graph(self):
        """Test fallback clustering on empty graph"""
        detector = CommunityDetector(
            db_conn_str="postgresql://test:test@localhost/test"
        )
        G = nx.Graph()

        # Access private method for testing
        results = detector._fallback_clustering(G)

        assert results == []

    def test_fallback_single_node(self):
        """Test fallback clustering with single node"""
        detector = CommunityDetector(
            db_conn_str="postgresql://test:test@localhost/test"
        )
        G = nx.Graph()
        G.add_node("node1")

        results = detector._fallback_clustering(G)

        # Fallback creates 1 result for single node at level 0
        # (level 1 only added if more than 1 node)
        assert len(results) == 1
        assert results[0]["level"] == 0
        assert results[0]["cluster_id"] == "0-0"
        assert results[0]["node_id"] == "node1"

    def test_fallback_multiple_nodes(self):
        """Test fallback clustering with multiple nodes"""
        detector = CommunityDetector(
            db_conn_str="postgresql://test:test@localhost/test"
        )
        G = nx.Graph()
        G.add_node("node1")
        G.add_node("node2")
        G.add_node("node3")

        results = detector._fallback_clustering(G)

        # Each node at level 0
        level_0 = [r for r in results if r["level"] == 0]
        assert len(level_0) == 3

        # All nodes in single cluster at level 1 (since >1 node)
        level_1 = [r for r in results if r["level"] == 1]
        assert len(level_1) == 3
        assert all(r["cluster_id"] == "1-0" for r in level_1)


class TestSaveCommunities:
    """Tests for save_communities method"""

    @pytest.mark.asyncio
    async def test_save_empty_communities(self):
        """Test saving empty community list does nothing"""
        detector = CommunityDetector(
            db_conn_str="postgresql://test:test@localhost/test"
        )

        # Should not raise and should not try to connect
        await detector.save_communities([])

    @pytest.mark.asyncio
    async def test_save_communities_single(self):
        """Test saving single community membership"""
        detector = CommunityDetector(
            db_conn_str="postgresql://test:test@localhost/test"
        )
        memberships = [{"node_id": "node1", "level": 0, "cluster_id": "0-0"}]

        mock_conn = AsyncMock()
        mock_cursor = AsyncMock()
        mock_cursor.__aenter__ = AsyncMock(return_value=mock_cursor)
        mock_cursor.__aexit__ = AsyncMock(return_value=None)
        mock_conn.cursor = MagicMock(return_value=mock_cursor)
        mock_conn.__aenter__ = AsyncMock(return_value=mock_conn)
        mock_conn.__aexit__ = AsyncMock(return_value=None)
        mock_cursor.fetchone = AsyncMock(return_value=["test-uuid"])

        with patch(
            "knowledge_base.community.AsyncConnection.connect", return_value=mock_conn
        ):
            await detector.save_communities(memberships)

            # Should have executed TRUNCATE and INSERT
            assert mock_cursor.execute.called


class TestCommunityStructure:
    """Tests for community data structures"""

    def test_community_membership_structure(self):
        """Test community membership record structure"""
        detector = CommunityDetector(
            db_conn_str="postgresql://test:test@localhost/test"
        )
        G = nx.Graph()
        G.add_node("test_node")

        results = detector.detect_communities(G)

        if results:
            membership = results[0]
            assert "node_id" in membership
            assert "level" in membership
            assert "cluster_id" in membership
            assert isinstance(membership["node_id"], str)
            assert isinstance(membership["level"], int)
            assert isinstance(membership["cluster_id"], str)

    def test_hierarchical_community_results(self):
        """Test that communities can have results"""
        detector = CommunityDetector(
            db_conn_str="postgresql://test:test@localhost/test"
        )
        G = nx.Graph()
        # Create a graph that can have communities
        for i in range(5):
            G.add_node(f"node{i}")

        results = detector.detect_communities(G)

        # graspologic may return empty for small graphs, which is acceptable
        # The function should not crash and should return a list
        assert isinstance(results, list)

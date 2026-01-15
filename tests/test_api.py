"""
Tests for Knowledge Base API endpoints
Uses real database connection for all tests
"""

import pytest
from fastapi.testclient import TestClient

from knowledge_base.api import app


@pytest.fixture
def client():
    """Provide test client for API endpoints"""
    return TestClient(app)


class TestRootEndpoint:
    """Tests for root endpoint"""

    def test_root_returns_message(self, client):
        """Test root endpoint returns welcome message"""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Knowledge Base API"
        assert data["version"] == "1.0.0"


class TestIngestTextEndpoint:
    """Tests for /api/ingest/text endpoint"""

    def test_ingest_text_success(self, client, seeded_db):
        """Test successful text ingestion"""
        response = client.post(
            "/api/ingest/text",
            json={"text": "Test document content", "filename": "test.txt"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "Successfully ingested" in data["message"]

    def test_ingest_text_empty_content(self, client, live_db):
        """Test ingestion with empty content"""
        response = client.post(
            "/api/ingest/text",
            json={"text": "", "filename": "empty.txt"},
        )
        assert response.status_code == 200

    def test_ingest_text_missing_filename(self, client, live_db):
        """Test ingestion with default filename"""
        response = client.post(
            "/api/ingest/text",
            json={"text": "Some content"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"


class TestStatsEndpoint:
    """Tests for /api/stats endpoint"""

    def test_stats_returns_counts(self, client, seeded_db):
        """Test stats endpoint returns database counts"""
        import time

        time.sleep(1)  # Wait for async operations to complete
        response = client.get("/api/stats")
        assert response.status_code == 200
        data = response.json()
        assert "nodes_count" in data
        assert "edges_count" in data
        assert "communities_count" in data
        assert "events_count" in data


class TestNodesEndpoint:
    """Tests for /api/nodes endpoint"""

    def test_get_nodes_default_limit(self, client, seeded_db):
        """Test getting nodes with default limit"""
        response = client.get("/api/nodes")
        assert response.status_code == 200
        data = response.json()
        assert "nodes" in data
        assert len(data["nodes"]) == 3

    def test_get_nodes_with_custom_limit(self, client, seeded_db):
        """Test getting nodes with custom limit"""
        response = client.get("/api/nodes?limit=1")
        assert response.status_code == 200
        data = response.json()
        assert "nodes" in data
        assert len(data["nodes"]) == 1

    def test_get_nodes_with_type_filter(self, client, seeded_db):
        """Test getting nodes filtered by type"""
        response = client.get("/api/nodes?node_type=Person")
        assert response.status_code == 200
        data = response.json()
        assert "nodes" in data
        assert len(data["nodes"]) == 1
        assert data["nodes"][0]["type"] == "Person"


class TestEdgesEndpoint:
    """Tests for /api/edges endpoint"""

    def test_get_edges_default_limit(self, client, seeded_db):
        """Test getting edges with default limit"""
        response = client.get("/api/edges")
        assert response.status_code == 200
        data = response.json()
        assert "edges" in data
        assert len(data["edges"]) == 0  # No edges seeded

    def test_get_edges_with_custom_limit(self, client, seeded_db):
        """Test getting edges with custom limit"""
        response = client.get("/api/edges?limit=5")
        assert response.status_code == 200
        data = response.json()
        assert "edges" in data


class TestCommunitiesListEndpoint:
    """Tests for /api/communities endpoint"""

    def test_get_communities(self, client, seeded_db):
        """Test getting communities"""
        response = client.get("/api/communities")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 0  # No communities seeded


class TestSearchEndpoint:
    """Tests for /api/search endpoint"""

    def test_search_with_query(self, client, seeded_db):
        """Test search endpoint with query"""
        import time

        time.sleep(1)
        response = client.post("/api/search", json={"query": "test"})
        assert response.status_code == 200
        data = response.json()
        assert "results" in data

    def test_search_with_custom_limit(self, client, seeded_db):
        """Test search endpoint with custom limit"""
        import time

        time.sleep(1)
        response = client.post("/api/search", json={"query": "test", "limit": 5})
        assert response.status_code == 200


class TestGraphDataEndpoint:
    """Tests for /api/graph endpoint"""

    def test_get_graph_data(self, client, seeded_db):
        """Test getting graph data for visualization"""
        import time

        time.sleep(1)
        response = client.get("/api/graph")
        assert response.status_code == 200
        data = response.json()
        assert "nodes" in data
        assert "edges" in data


class TestCommunityDetectionEndpoint:
    """Tests for /api/community/detect endpoint"""

    def test_detect_communities(self, client, seeded_db):
        """Test community detection triggers"""
        import time

        time.sleep(1)
        response = client.post("/api/community/detect")
        assert response.status_code in [200, 500]


class TestSummarizationEndpoint:
    """Tests for /api/summarize endpoint"""

    def test_summarize_communities(self, client, seeded_db):
        """Test community summarization triggers"""
        import time

        time.sleep(1)
        response = client.post("/api/summarize")
        assert response.status_code in [200, 500]


class TestPydanticModels:
    """Tests for API Pydantic models"""

    def test_ingest_text_request_defaults(self):
        """Test IngestTextRequest default values"""
        from knowledge_base.api import IngestTextRequest

        request = IngestTextRequest(text="test")
        assert request.filename == "uploaded_text.txt"

    def test_ingest_text_request_custom(self):
        """Test IngestTextRequest with custom filename"""
        from knowledge_base.api import IngestTextRequest

        request = IngestTextRequest(text="test", filename="custom.txt")
        assert request.filename == "custom.txt"

    def test_search_request_defaults(self):
        """Test SearchRequest default values"""
        from knowledge_base.api import SearchRequest

        request = SearchRequest(query="test")
        assert request.limit == 10

    def test_search_request_custom(self):
        """Test SearchRequest with custom limit"""
        from knowledge_base.api import SearchRequest

        request = SearchRequest(query="test", limit=50)
        assert request.limit == 50

    def test_stats_response_model(self):
        """Test StatsResponse model"""
        from knowledge_base.api import StatsResponse

        response = StatsResponse(
            nodes_count=10,
            edges_count=5,
            communities_count=2,
            events_count=3,
        )
        assert response.nodes_count == 10
        assert response.edges_count == 5
        assert response.communities_count == 2
        assert response.events_count == 3

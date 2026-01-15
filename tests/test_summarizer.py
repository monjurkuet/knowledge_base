from knowledge_base.summarizer import CommunityReport, CommunitySummarizer, Finding


class TestCommunitySummarizerInit:
    """Test CommunitySummarizer initialization"""

    def test_summarizer_initialization(self):
        """Test that CommunitySummarizer initializes correctly"""
        summarizer = CommunitySummarizer(
            db_conn_str="postgresql://test:test@localhost:5432/test",
            base_url="http://localhost:8317/v1",
            api_key="test-key",
            model_name="gemini-2.5-pro",
        )
        assert summarizer is not None
        assert summarizer.db_conn_str == "postgresql://test:test@localhost:5432/test"
        assert summarizer.client is not None
        assert summarizer.model_name == "gemini-2.5-pro"


class TestCommunityReportModel:
    """Test Pydantic models for summarization"""

    def test_community_report_creation(self):
        """Test CommunityReport model creation"""
        finding = Finding(
            summary="Test finding summary",
            explanation="Detailed explanation of the finding",
        )
        report = CommunityReport(
            title="Test Community Report",
            summary="High-level summary",
            rating=8.5,
            findings=[finding],
        )
        assert report.title == "Test Community Report"
        assert report.summary == "High-level summary"
        assert report.rating == 8.5
        assert len(report.findings) == 1
        assert report.findings[0].summary == "Test finding summary"

    def test_community_report_findings_list(self):
        """Test CommunityReport with multiple findings"""
        findings = [
            Finding(summary=f"Finding {i}", explanation=f"Explanation {i}")
            for i in range(3)
        ]
        report = CommunityReport(
            title="Multi-finding Report",
            summary="Summary with multiple findings",
            rating=7.0,
            findings=findings,
        )
        assert len(report.findings) == 3

    def test_community_report_rating_range(self):
        """Test CommunityReport rating validation"""
        finding = Finding(summary="Finding", explanation="Explanation")
        report = CommunityReport(
            title="Test",
            summary="Test summary",
            rating=5.0,
            findings=[finding],
        )
        assert report.rating >= 0
        assert report.rating <= 10

    def test_finding_model(self):
        """Test Finding model fields"""
        finding = Finding(summary="Key insight", explanation="Detailed explanation")
        assert finding.summary == "Key insight"
        assert finding.explanation == "Detailed explanation"

    def test_finding_model_empty(self):
        """Test Finding with minimal data"""
        finding = Finding(summary="Minimal", explanation="Desc")
        assert finding.summary == "Minimal"
        assert finding.explanation == "Desc"


class TestSummarizerModels:
    """Test model serialization and validation"""

    def test_community_report_json_serialization(self):
        """Test CommunityReport can be serialized to JSON"""
        report = CommunityReport(
            title="Test Report",
            summary="Summary",
            rating=8.0,
            findings=[
                Finding(summary="Finding 1", explanation="Explanation 1"),
                Finding(summary="Finding 2", explanation="Explanation 2"),
            ],
        )
        json_str = report.model_dump_json()
        assert "Test Report" in json_str
        assert "Summary" in json_str
        assert "Finding 1" in json_str

    def test_community_report_nested_findings(self):
        """Test CommunityReport with nested findings structure"""
        report = CommunityReport(
            title="Complex Report",
            summary="Complex summary",
            rating=9.5,
            findings=[
                Finding(summary=f"Finding {i}", explanation=f"Explanation {i}")
                for i in range(5)
            ],
        )
        assert len(report.findings) == 5
        for i, finding in enumerate(report.findings):
            assert finding.summary == f"Finding {i}"
            assert finding.explanation == f"Explanation {i}"


class TestSummarizerAttributes:
    """Test CommunitySummarizer attribute access"""

    def test_summarizer_connection_string(self):
        """Test connection string is stored correctly"""
        conn_str = "postgresql://user:pass@localhost:5432/testdb"
        summarizer = CommunitySummarizer(db_conn_str=conn_str)
        assert summarizer.db_conn_str == conn_str

    def test_summarizer_client_configuration(self):
        """Test client is configured with correct parameters"""
        summarizer = CommunitySummarizer(
            db_conn_str="postgresql://test:test@localhost:5432/test",
            base_url="http://custom:1234/v1",
            api_key="custom-key",
        )
        assert "custom:1234" in str(summarizer.client.api_url)
        assert summarizer.client.api_key == "custom-key"

    def test_summarizer_model_name(self):
        """Test model name is stored correctly"""
        summarizer = CommunitySummarizer(
            db_conn_str="postgresql://test:test@localhost:5432/test",
            model_name="custom-model",
        )
        assert summarizer.model_name == "custom-model"


class TestSummarizerEdgeCases:
    """Test edge cases and error handling"""

    def test_community_report_empty_findings(self):
        """Test CommunityReport with no findings"""
        report = CommunityReport(
            title="Empty Report",
            summary="Summary with no findings",
            rating=5.0,
            findings=[],
        )
        assert len(report.findings) == 0

    def test_community_report_long_content(self):
        """Test CommunityReport with long content"""
        long_text = "A" * 10000
        report = CommunityReport(
            title=long_text[:100],
            summary=long_text[:500],
            rating=5.0,
            findings=[Finding(summary=long_text[:200], explanation=long_text[:500])],
        )
        assert len(report.title) == 100
        assert len(report.summary) == 500

import pytest
import tempfile
import os
from unittest.mock import patch, AsyncMock


@pytest.mark.asyncio
async def test_pipeline_initialization(pipeline):
    """Test that KnowledgePipeline initializes correctly"""
    assert pipeline is not None
    assert pipeline.ingestor is not None
    assert pipeline.resolver is not None
    assert pipeline.community_detector is not None


@pytest.mark.asyncio
async def test_pipeline_config(pipeline):
    """Test that pipeline loads configuration correctly"""
    assert pipeline.config is not None
    assert pipeline.config.llm.model_name is not None
    assert pipeline.config.database.connection_string is not None


@pytest.mark.asyncio
async def test_pipeline_file_reading(live_db, pipeline, test_data_dir):
    """Test pipeline can read test data files"""
    test_file = test_data_dir / "doc_1_history.txt"
    if not test_file.exists():
        pytest.skip(f"Test data file not found: {test_file}")

    try:
        with open(test_file, encoding="utf-8") as f:
            text = f.read()
        assert len(text) > 0
    except Exception as e:
        pytest.fail(f"Failed to read test file: {e}")


@pytest.mark.asyncio
async def test_pipeline_get_embedding(live_db, pipeline):
    """Test embedding generation"""
    try:
        embedding = await pipeline._get_embedding("Test entity description")
        assert embedding is not None
        assert len(embedding) > 0
    except Exception as e:
        pytest.skip(f"Embedding generation failed (may need API): {e}")


@pytest.mark.asyncio
async def test_pipeline_run_with_mocked_components(live_db, pipeline):
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".txt", delete=False
    ) as temp_file:
        temp_file.write("Test document content about Dr. Elena Vance and her research.")
        temp_file_path = temp_file.name

    try:
        with patch.object(
            pipeline.ingestor, "extract", new_callable=AsyncMock
        ) as mock_extract:
            from knowledge_base.ingestor import (
                KnowledgeGraph,
                Entity,
                Relationship,
                Event,
            )

            mock_graph = KnowledgeGraph(
                entities=[
                    Entity(
                        name="Dr. Elena Vance",
                        type="Person",
                        description="Research scientist",
                    )
                ],
                relationships=[
                    Relationship(
                        source="Dr. Elena Vance",
                        target="Research",
                        type="CONDUCTS",
                        description="Conducts research",
                    )
                ],
                events=[
                    Event(
                        primary_entity="Dr. Elena Vance",
                        description="Published research paper",
                        raw_time="2023",
                        normalized_date="2023",
                    )
                ],
            )
            mock_extract.return_value = mock_graph

            with patch.object(
                pipeline, "_store_graph", new_callable=AsyncMock
            ) as mock_store:
                with patch.object(
                    pipeline.community_detector, "load_graph"
                ) as mock_load_graph:
                    with patch.object(
                        pipeline.community_detector, "detect_communities"
                    ) as mock_detect:
                        with patch.object(
                            pipeline.community_detector,
                            "save_communities",
                            new_callable=AsyncMock,
                        ) as mock_save:
                            with patch(
                                "knowledge_base.summarizer.CommunitySummarizer",
                                autospec=True,
                            ) as mock_summarizer_class:
                                mock_summarizer = AsyncMock()
                                mock_summarizer_class.return_value = mock_summarizer

                                await pipeline.run(temp_file_path)

                                mock_extract.assert_called_once()
                                mock_store.assert_called_once()
                                mock_load_graph.assert_called_once()
                                mock_detect.assert_called_once()
                                mock_save.assert_called_once()
                                mock_summarizer.summarize_all.assert_called_once()

    finally:
        if os.path.exists(temp_file_path):
            os.unlink(temp_file_path)


@pytest.mark.asyncio
async def test_pipeline_store_graph(live_db, pipeline):
    from knowledge_base.ingestor import KnowledgeGraph, Entity, Relationship, Event

    graph = KnowledgeGraph(
        entities=[
            Entity(name="Test Entity", type="Person", description="Test description")
        ],
        relationships=[
            Relationship(
                source="Test Entity",
                target="Another Entity",
                type="RELATED_TO",
                description="Test relationship",
            )
        ],
        events=[
            Event(
                primary_entity="Test Entity",
                description="Test event",
                raw_time="2023",
                normalized_date="2023",
            )
        ],
    )

    with patch.object(
        pipeline.resolver, "resolve_and_insert", new_callable=AsyncMock
    ) as mock_resolve:
        mock_resolve.return_value = "test-entity-id"

        with patch(
            "psycopg.AsyncConnection.connect", new_callable=AsyncMock
        ) as mock_connect:
            mock_conn = AsyncMock()
            mock_cursor = AsyncMock()
            mock_conn.__aenter__.return_value = mock_conn
            mock_conn.cursor.return_value.__aenter__.return_value = mock_cursor
            mock_connect.return_value = mock_conn

            await pipeline._store_graph(graph, domain_id="test-domain")

            mock_resolve.assert_called_once()
            assert mock_cursor.execute.call_count >= 2

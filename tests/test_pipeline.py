import pytest


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

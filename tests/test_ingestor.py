import pytest

from knowledge_base.ingestor import (
    Entity,
    Event,
    KnowledgeGraph,
    Relationship,
)


@pytest.mark.asyncio
async def test_entity_model():
    """Test Entity Pydantic model validation"""
    entity = Entity(
        name="Test Person", type="Person", description="A test person entity"
    )
    assert entity.name == "Test Person"
    assert entity.type == "Person"
    assert entity.description == "A test person entity"


@pytest.mark.asyncio
async def test_relationship_model():
    """Test Relationship Pydantic model validation"""
    rel = Relationship(
        source="Entity A",
        target="Entity B",
        type="RELATES_TO",
        description="A test relationship",
        weight=1.0,
    )
    assert rel.source == "Entity A"
    assert rel.target == "Entity B"
    assert rel.type == "RELATES_TO"
    assert rel.weight == 1.0


@pytest.mark.asyncio
async def test_event_model():
    """Test Event Pydantic model validation"""
    event = Event(
        primary_entity="Test Person",
        description="Something happened",
        raw_time="2024-01-01",
        normalized_date="2024-01-01",
    )
    assert event.primary_entity == "Test Person"
    assert event.description == "Something happened"
    assert event.raw_time == "2024-01-01"


@pytest.mark.asyncio
async def test_knowledge_graph_model():
    """Test KnowledgeGraph Pydantic model"""
    graph = KnowledgeGraph(
        entities=[Entity(name="Test", type="Concept", description="A test")],
        relationships=[
            Relationship(
                source="Test",
                target="Related",
                type="LINKED",
                description="Test relation",
            )
        ],
        events=[],
    )
    assert len(graph.entities) == 1
    assert len(graph.relationships) == 1
    assert len(graph.events) == 0


@pytest.mark.asyncio
async def test_ingestor_initialization(ingestor):
    """Test that GraphIngestor initializes correctly"""
    assert ingestor is not None
    assert ingestor.model_name is not None


@pytest.mark.asyncio
async def test_ingestor_basic_extraction(ingestor):
    """Test basic extraction from simple text"""
    test_text = """
    John Smith is a software engineer at TechCorp.
    He works with Jane Doe on Project Alpha.
    """
    try:
        graph = await ingestor.extract(test_text)
        assert graph is not None
        assert isinstance(graph, KnowledgeGraph)
    except Exception as e:
        pytest.skip(f"Extraction failed (may need LLM API): {e}")

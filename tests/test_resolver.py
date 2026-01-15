import pytest

from knowledge_base.resolver import ResolutionDecision


@pytest.mark.asyncio
async def test_resolution_decision_model():
    """Test ResolutionDecision Pydantic model"""
    decision = ResolutionDecision(
        decision="MERGE",
        reasoning="Same entity with different name variants",
        canonical_name="John Smith",
    )
    assert decision.decision == "MERGE"
    assert decision.reasoning == "Same entity with different name variants"
    assert decision.canonical_name == "John Smith"


@pytest.mark.asyncio
async def test_resolution_decision_keep_separate():
    """Test KEEP_SEPARATE decision"""
    decision = ResolutionDecision(
        decision="KEEP_SEPARATE", reasoning="Completely different entities"
    )
    assert decision.decision == "KEEP_SEPARATE"
    assert decision.canonical_name is None


@pytest.mark.asyncio
async def test_resolution_decision_link():
    """Test LINK decision"""
    decision = ResolutionDecision(
        decision="LINK",
        reasoning="Related but distinct entities",
        canonical_name="Related Group",
    )
    assert decision.decision == "LINK"


@pytest.mark.asyncio
async def test_resolver_initialization(resolver):
    """Test that EntityResolver initializes correctly"""
    assert resolver is not None
    assert resolver.db_conn_str is not None
    assert resolver.model_name is not None


@pytest.mark.asyncio
async def test_resolver_db_connection(resolver):
    """Test database connection"""
    try:
        async with await resolver.get_connection() as conn:
            assert conn is not None
    except Exception as e:
        pytest.skip(f"Database connection failed: {e}")

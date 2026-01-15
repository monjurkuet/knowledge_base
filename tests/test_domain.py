"""
Unit tests for domain management and multi-domain schema.
"""

from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest

from knowledge_base.domain import (
    DomainCreate,
    DomainManager,
    DomainResponse,
    DomainTemplate,
    EntityTypeTemplate,
    ExtractionConfig,
    RelationshipTypeTemplate,
)


class TestEntityTypeTemplate:
    """Tests for EntityTypeTemplate model."""

    def test_entity_type_template_creation(self):
        """Test creating an entity type template."""
        entity_type = EntityTypeTemplate(
            name="research_paper",
            display_name="Research Paper",
            description="Academic research paper",
            icon="article",
            color="#4285F4",
            extraction_prompt="Extract paper details",
            example_patterns=["arXiv:1234.5678", "NeurIPS 2024"],
        )

        assert entity_type.name == "research_paper"
        assert entity_type.display_name == "Research Paper"
        assert entity_type.color == "#4285F4"
        assert len(entity_type.example_patterns) == 2

    def test_entity_type_template_defaults(self):
        """Test entity type template default values."""
        entity_type = EntityTypeTemplate(
            name="test_entity",
            display_name="Test Entity",
            extraction_prompt="Extract test entity",
        )

        assert entity_type.icon == "circle"
        assert entity_type.color == "#4285F4"
        assert entity_type.validation_rules == {}
        assert entity_type.example_patterns == []


class TestRelationshipTypeTemplate:
    """Tests for RelationshipTypeTemplate model."""

    def test_relationship_type_template_creation(self):
        """Test creating a relationship type template."""
        rel_type = RelationshipTypeTemplate(
            name="cites",
            display_name="Cites",
            description="Paper A cites Paper B",
            source_entity_types=["research_paper"],
            target_entity_types=["research_paper"],
            is_directional=True,
            extraction_prompt="Identify citations",
        )

        assert rel_type.name == "cites"
        assert rel_type.is_directional is True
        assert "research_paper" in rel_type.source_entity_types

    def test_relationship_type_bidirectional(self):
        """Test non-directional relationship."""
        rel_type = RelationshipTypeTemplate(
            name="related_to",
            display_name="Related To",
            source_entity_types=["concept"],
            target_entity_types=["concept"],
            is_directional=False,
            extraction_prompt="Find relationships",
        )

        assert rel_type.is_directional is False


class TestDomainCreate:
    """Tests for DomainCreate model."""

    def test_domain_create_valid(self):
        """Test valid domain creation."""
        domain_data = DomainCreate(
            name="ai_research",
            display_name="AI Research",
            description="AI engineering research domain",
        )

        assert domain_data.name == "ai_research"
        assert domain_data.display_name == "AI Research"
        assert domain_data.description == "AI engineering research domain"

    def test_domain_create_minimal(self):
        """Test domain creation with minimal data."""
        domain_data = DomainCreate(
            name="test_domain",
            display_name="Test Domain",
        )

        assert domain_data.description is None
        assert domain_data.template_config == {}

    def test_domain_create_name_validation(self):
        """Test domain name validation."""
        from pydantic import ValidationError


# ... imports


class TestDomainCreate:
    # ... tests

    def test_domain_create_name_validation(self):
        """Test domain name validation."""
        with pytest.raises(ValidationError):
            DomainCreate(
                name="ab",  # Too short
                display_name="Test",
            )

        with pytest.raises(ValidationError):
            DomainCreate(
                name="Invalid Name",  # Contains space
                display_name="Test",
            )


class TestDomainResponse:
    """Tests for DomainResponse model."""

    def test_domain_response_creation(self):
        """Test creating domain response."""
        domain_id = uuid4()
        response = DomainResponse(
            id=domain_id,
            name="test_domain",
            display_name="Test Domain",
            description=None,
            is_active=True,
            created_at="2024-01-01T00:00:00Z",
            updated_at="2024-01-01T00:00:00Z",
        )

        assert response.id == domain_id
        assert response.is_active is True
        assert response.node_count == 0


class TestDomainTemplate:
    """Tests for DomainTemplate model."""

    def test_domain_template_creation(self):
        """Test creating a domain template."""
        template = DomainTemplate(
            id="ai_engineering",
            name="ai_engineering_research",
            display_name="AI Engineering Research",
            description="AI engineering research domain",
            entity_types=[
                EntityTypeTemplate(
                    name="model",
                    display_name="Model",
                    extraction_prompt="Extract model details",
                )
            ],
            relationship_types=[
                RelationshipTypeTemplate(
                    name="uses",
                    display_name="Uses",
                    source_entity_types=["model"],
                    target_entity_types=["technique"],
                    extraction_prompt="Extract usage",
                )
            ],
        )

        assert template.id == "ai_engineering"
        assert len(template.entity_types) == 1
        assert len(template.relationship_types) == 1

    def test_domain_template_with_config(self):
        """Test domain template with extraction config."""
        template = DomainTemplate(
            id="test",
            name="test_domain",
            display_name="Test Domain",
            extraction_config=ExtractionConfig(
                llm_model="gemini-2.5-flash",
                temperature=0.1,
                confidence_threshold=0.8,
            ),
        )

        assert template.extraction_config.llm_model == "gemini-2.5-flash"
        assert template.extraction_config.confidence_threshold == 0.8


from uuid import uuid4
import pytest
from pydantic import ValidationError
from knowledge_base.domain import (
    DomainCreate,
    DomainManager,
    DomainTemplate,
    EntityTypeTemplate,
    RelationshipTypeTemplate,
)

# ... (keep other Test classes like TestEntityTypeTemplate)


class TestDomainCreate:
    """Tests for DomainCreate model."""

    def test_domain_create_valid(self):
        """Test valid domain creation."""
        domain_data = DomainCreate(
            name="ai_research",
            display_name="AI Research",
            description="AI engineering research domain",
        )
        assert domain_data.name == "ai_research"

    def test_domain_create_name_validation(self):
        """Test domain name validation."""
        with pytest.raises(ValidationError):
            DomainCreate(name="ab", display_name="Test")

        with pytest.raises(ValidationError):
            DomainCreate(name="Invalid Name", display_name="Test")


class TestDomainManager:
    """Tests for DomainManager class using a live database."""

    @pytest.mark.asyncio
    async def test_create_domain(self, live_db):
        """Test creating a domain."""
        manager = DomainManager()
        domain_data = DomainCreate(
            name="real_test_domain",
            display_name="Real Test Domain",
            description="A domain for real testing.",
        )
        result = await manager.create_domain(domain_data)
        assert result.name == "real_test_domain"

        # Verify it was written to the DB
        fetched = await manager.get_domain(result.id)
        assert fetched is not None
        assert fetched.name == "real_test_domain"

    @pytest.mark.asyncio
    async def test_get_domain(self, live_db):
        """Test getting a domain by ID."""
        manager = DomainManager()
        domain_data = DomainCreate(name="get_me", display_name="Get Me")
        created = await manager.create_domain(domain_data)

        fetched = await manager.get_domain(created.id)
        assert fetched is not None
        assert fetched.id == created.id
        assert fetched.name == "get_me"

    @pytest.mark.asyncio
    async def test_get_domain_not_found(self, live_db):
        """Test getting a non-existent domain."""
        manager = DomainManager()
        result = await manager.get_domain(uuid4())
        assert result is None

    @pytest.mark.asyncio
    async def test_list_domains(self, live_db):
        """Test listing all domains."""
        manager = DomainManager()
        await manager.create_domain(
            DomainCreate(name="list_one", display_name="List 1")
        )
        await manager.create_domain(
            DomainCreate(name="list_two", display_name="List 2")
        )

        results = await manager.list_domains()
        assert len(results) >= 2
        names = {d.name for d in results}
        assert "list_one" in names
        assert "list_two" in names

    @pytest.mark.asyncio
    async def test_update_domain(self, live_db):
        """Test updating a domain."""
        manager = DomainManager()
        created = await manager.create_domain(
            DomainCreate(name="to_update", display_name="Update Me")
        )

        result = await manager.update_domain(created.id, display_name="Updated Name")
        assert result is not None
        assert result.display_name == "Updated Name"

        fetched = await manager.get_domain(created.id)
        assert fetched.display_name == "Updated Name"

    @pytest.mark.asyncio
    async def test_delete_domain(self, live_db):
        """Test soft deleting a domain."""
        manager = DomainManager()
        created = await manager.create_domain(
            DomainCreate(name="to_delete", display_name="Delete Me")
        )

        result = await manager.delete_domain(created.id)
        assert result is True

        fetched = await manager.get_domain(created.id)
        assert fetched.is_active is False

    @pytest.mark.asyncio
    async def test_add_entity_type(self, live_db):
        """Test adding an entity type to a domain."""
        manager = DomainManager()
        domain = await manager.create_domain(
            DomainCreate(name="domain_with_entity", display_name="...")
        )

        entity_type = EntityTypeTemplate(
            name="test_entity",
            display_name="Test Entity",
            extraction_prompt="Extract test entity",
        )

        entity_type_id = await manager.add_entity_type(domain.id, entity_type)
        assert isinstance(entity_type_id, uuid4().__class__)

        entity_types = await manager.get_entity_types(domain.id)
        assert len(entity_types) == 1
        assert entity_types[0]["name"] == "test_entity"

    @pytest.mark.asyncio
    async def test_apply_template(self, live_db):
        """Test applying a domain template."""
        manager = DomainManager()
        domain = await manager.create_domain(
            DomainCreate(name="template_domain", display_name="...")
        )

        template = DomainTemplate(
            id="test",
            name="test_template",
            display_name="Test Template",
            entity_types=[
                EntityTypeTemplate(
                    name="entity1", display_name="Entity 1", extraction_prompt="..."
                )
            ],
            relationship_types=[
                RelationshipTypeTemplate(
                    name="rel1",
                    display_name="Rel 1",
                    source_entity_types=["entity1"],
                    target_entity_types=["entity1"],
                    extraction_prompt="...",
                )
            ],
        )

        await manager.apply_template(domain.id, template)

        entities = await manager.get_entity_types(domain.id)
        relationships = await manager.get_relationship_types(domain.id)

        assert len(entities) == 1
        assert entities[0]["name"] == "entity1"
        assert len(relationships) == 1
        assert relationships[0]["name"] == "rel1"


class TestDomainTemplateLoading:
    """Tests for loading domain templates."""

    def test_load_template_from_dict(self):
        """Test loading template from dictionary."""
        data = {
            "id": "ai_engineering",
            "name": "ai_engineering_research",
            "display_name": "AI Engineering Research",
            "description": "AI engineering research",
            "entity_types": [
                {
                    "name": "research_paper",
                    "display_name": "Research Paper",
                    "extraction_prompt": "Extract paper details",
                }
            ],
            "relationship_types": [
                {
                    "name": "cites",
                    "display_name": "Cites",
                    "source_entity_types": ["research_paper"],
                    "target_entity_types": ["research_paper"],
                    "extraction_prompt": "Find citations",
                }
            ],
        }

        template = DomainManager.load_template_from_dict(data)

        assert template.id == "ai_engineering"
        assert len(template.entity_types) == 1
        assert template.entity_types[0].name == "research_paper"

    def test_load_template_complex_config(self):
        """Test loading template with complex config."""
        data = {
            "id": "test",
            "name": "test_domain",
            "display_name": "Test Domain",
            "extraction_config": {
                "llm_model": "gemini-2.5-flash",
                "temperature": 0.1,
                "max_tokens": 8192,
                "confidence_threshold": 0.7,
            },
            "analysis_config": {
                "community_detection": {
                    "algorithm": "leiden",
                    "resolution": 1.0,
                }
            },
            "ui_config": {
                "color_scheme": {
                    "primary": "#4285F4",
                    "background": "#FFFFFF",
                }
            },
        }

        template = DomainManager.load_template_from_dict(data)

        assert template.extraction_config.llm_model == "gemini-2.5-flash"
        assert template.ui_config.color_scheme["primary"] == "#4285F4"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

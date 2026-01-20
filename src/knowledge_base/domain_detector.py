"""
AI-powered domain detection and management for multi-domain knowledge base.
Automatically detects appropriate domains based on content analysis and manages
domain creation/updating without user intervention.
"""

import logging
from typing import Any
from uuid import UUID

from psycopg import AsyncConnection

from knowledge_base.config import get_config
from knowledge_base.domain import DomainManager
from knowledge_base.domain.models import (
    DomainTemplate,
    EntityTypeTemplate,
    ExtractionConfig,
    RelationshipTypeTemplate,
)
from knowledge_base.http_client import ChatCompletionRequest, ChatMessage, HTTPClient

logger = logging.getLogger(__name__)
config = get_config()


class DomainDetectionPrompt:
    """Prompts for domain detection and analysis."""

    @staticmethod
    def get_domain_analysis_prompt() -> str:
        """Get prompt for analyzing text content and detecting domain."""
        return """
You are an expert domain analyst. Analyze the provided text content and determine the most appropriate knowledge domain for organizing this information.

Your goal is to define a **Rich Schema** (Ontology) that best represents the knowledge in this text.

Respond with a JSON object containing:
- "domain_name": snake_case name for the domain (e.g., "clinical_trials")
- "display_name": Human-readable domain name (e.g., "Clinical Trials")
- "description": Brief description of what this domain covers
- "confidence": Confidence score (0.0-1.0) in your domain classification
- "entity_types": A list of entity definitions. Each object must have:
    - "name": snake_case unique identifier (e.g., "study_protocol")
    - "display_name": Human readable name (e.g., "Study Protocol")
    - "description": Definition of this entity
    - "synonyms": List of strings (e.g., ["Protocol", "Study Plan"])
    - "attributes": List of strings representing key properties (e.g., ["id", "title", "date"])
- "relationship_types": A list of relationship definitions. Each object must have:
    - "name": snake_case unique identifier (e.g., "has_investigator")
    - "display_name": Human readable name (e.g., "Has Investigator")
    - "description": Definition of this relationship
    - "source": The "name" of the source entity type
    - "target": The "name" of the target entity type
    - "synonyms": List of strings (e.g., ["investigated_by", "led_by"])

Example response:
{
    "domain_name": "clinical_trials",
    "display_name": "Clinical Trials",
    "description": "Medical research studies involving human participants",
    "confidence": 0.95,
    "entity_types": [
        {
            "name": "drug",
            "display_name": "Drug",
            "description": "A substance used for medical treatment",
            "synonyms": ["Medication", "Compound", "Intervention"],
            "attributes": ["name", "dosage", "manufacturer"]
        }
    ],
    "relationship_types": [
        {
            "name": "treats",
            "display_name": "Treats",
            "description": "Indicates a drug is used for a condition",
            "source": "drug",
            "target": "condition",
            "synonyms": ["prescribed_for", "targets"]
        }
    ]
}

Keep responses concise and focused on the actual content provided. Ensure entity and relationship names are valid snake_case identifiers.
"""

    @staticmethod
    def get_domain_template_prompt(
        domain_name: str,
        display_name: str,
        entity_types: list[str],
        relationship_types: list[str],
    ) -> str:
        """Get prompt for generating detailed domain template configuration."""
        entity_list = ", ".join(entity_types)
        relationship_list = ", ".join(relationship_types)

        return f"""
Generate a comprehensive domain template configuration for "{display_name}" ({domain_name}).

Based on the entity types [{entity_list}] and relationship types [{relationship_list}], create detailed configurations including:

1. **Entity Type Templates**: For each entity type, provide:
   - Detailed description
   - Appropriate UI icon (Material Design icon name)
   - Color scheme (hex color code)
   - LLM extraction prompt specific to this entity type

2. **Relationship Type Templates**: For each relationship type, provide:
   - Detailed description  
   - Source and target entity type mappings
   - Directionality (true/false)
   - LLM extraction prompt specific to this relationship type

3. **Extraction Configuration**: Optimal LLM settings for this domain

4. **Analysis Configuration**: Community detection and summarization settings

5. **UI Configuration**: Color scheme and layout preferences

Return a complete JSON configuration that can be used to initialize this domain.
"""


class DomainDetector:
    """AI-powered domain detector and manager."""

    def __init__(self, db_conn_str: str | None = None):
        """Initialize domain detector with database connection."""
        self.config = get_config()
        self.db_conn_str = db_conn_str or self.config.database.connection_string
        self.domain_manager = DomainManager(self.db_conn_str)
        logger.info("DomainDetector initialized")

    async def get_connection(self) -> AsyncConnection:
        """Get async database connection."""
        return await AsyncConnection.connect(self.db_conn_str)

    async def detect_domain_from_text(self, text: str) -> DomainTemplate | None:
        """
        Analyze text content and detect the most appropriate domain.

        Args:
            text: Input text to analyze for domain detection

        Returns:
            DomainTemplate if domain detected with sufficient confidence, None otherwise
        """
        try:
            logger.info("Starting AI-powered domain detection...")

            prompt = DomainDetectionPrompt.get_domain_analysis_prompt()
            messages = [
                ChatMessage(role="system", content=prompt),
                ChatMessage(
                    role="user", content=f"Analyze the following text:\n\n{text[:2000]}"
                ),
            ]

            import json
            import re

            model_name = self.config.llm.model_name
            http_client = HTTPClient()
            request = ChatCompletionRequest(
                model=model_name, messages=messages, temperature=0.1, max_tokens=1000
            )

            response_data = await http_client.chat_completion(request)

            if response_data is None:
                logger.warning("LLM API call failed")
                return None

            if "choices" not in response_data or len(response_data["choices"]) == 0:
                logger.warning("LLM API returned empty choices")
                return None

            content = response_data["choices"][0]["message"]["content"]
            json_match = re.search(r"\{.*\}", content, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
                try:
                    domain_data = json.loads(json_str)
                    confidence = domain_data.get("confidence", 0.0)
                    if confidence < 0.7:
                        logger.info(
                            f"Domain detection confidence too low ({confidence}), using fallback"
                        )
                        return None

                    # Parse Entity Types
                    entity_templates = []
                    for et in domain_data.get("entity_types", []):
                        entity_templates.append(
                            EntityTypeTemplate(
                                name=et.get("name"),
                                display_name=et.get("display_name"),
                                description=et.get("description", ""),
                                synonyms=et.get("synonyms", []),
                                extraction_prompt=f"Extract entities of type {et.get('display_name')}. Attributes: {', '.join(et.get('attributes', []))}",
                                validation_rules={
                                    "attributes": et.get("attributes", [])
                                },
                            )
                        )

                    # Parse Relationship Types
                    relationship_templates = []
                    for rt in domain_data.get("relationship_types", []):
                        # Ensure source/target exist in entity types (basic validation)
                        # For now, we trust the LLM or allow loose coupling,
                        # but ideally we should check if source/target are in entity_templates
                        relationship_templates.append(
                            RelationshipTypeTemplate(
                                name=rt.get("name"),
                                display_name=rt.get("display_name"),
                                description=rt.get("description", ""),
                                source_entity_types=[rt.get("source")]
                                if rt.get("source")
                                else [],
                                target_entity_types=[rt.get("target")]
                                if rt.get("target")
                                else [],
                                synonyms=rt.get("synonyms", []),
                                extraction_prompt=f"Extract relationships of type {rt.get('display_name')} between {rt.get('source')} and {rt.get('target')}.",
                            )
                        )

                    domain_template = DomainTemplate(
                        id=domain_data.get("domain_name", "general_knowledge"),
                        name=domain_data.get("domain_name", "general_knowledge"),
                        display_name=domain_data.get(
                            "display_name", "General Knowledge"
                        ),
                        description=domain_data.get("description", ""),
                        entity_types=entity_templates,
                        relationship_types=relationship_templates,
                        extraction_config=ExtractionConfig(
                            llm_model=model_name,
                            temperature=0.1,
                            confidence_threshold=confidence,
                        ),
                    )

                    logger.info(
                        f"Domain detection successful: {domain_template.name} (confidence: {confidence})"
                    )
                    return domain_template

                except json.JSONDecodeError as e:
                    logger.warning(f"Failed to parse LLM response as JSON: {e}")
                    return None
            else:
                logger.warning("No JSON found in LLM response")
                return None

        except Exception as e:
            logger.error(f"Domain detection failed: {e}", exc_info=True)
            return None

    async def _generate_domain_template(
        self,
        domain_name: str,
        display_name: str,
        entity_types: list[str],
        relationship_types: list[str],
    ) -> dict[str, Any]:
        """Generate detailed domain template configuration."""
        # Return default configuration
        return {
            "extraction_config": {
                "llm_model": self.config.llm.model_name,
                "temperature": 0.1,
                "confidence_threshold": 0.7,
            },
            "analysis_config": {},
            "ui_config": {},
        }

    async def get_or_create_domain_for_text(self, text: str) -> UUID | None:
        """
        Get existing domain or create new domain based on text content.

        Args:
            text: Input text to analyze for domain assignment

        Returns:
            Domain UUID if successful, None if no suitable domain found
        """
        detected_template = await self.detect_domain_from_text(text)

        if detected_template:
            existing_domain = await self.domain_manager.get_domain_by_name(
                detected_template.name
            )
            if existing_domain:
                logger.info(f"Using existing domain: {detected_template.name}")
                # Sync schema (evolve ontology)
                await self.domain_manager.sync_domain_schema(
                    existing_domain.id, detected_template
                )
                return existing_domain.id

            try:
                from knowledge_base.domain.models import DomainCreate

                domain_create = DomainCreate(
                    name=detected_template.name,
                    display_name=detected_template.display_name,
                    description=detected_template.description,
                    template_config=detected_template.model_dump(),
                )
                new_domain = await self.domain_manager.create_domain(domain_create)

                # Apply the template to create entity/relationship types
                await self.domain_manager.apply_template(
                    new_domain.id, detected_template
                )

                logger.info(f"Created new domain: {detected_template.name}")
                return new_domain.id
            except Exception as e:
                logger.warning(f"Failed to create domain {detected_template.name}: {e}")

        logger.info("Using default general knowledge domain")
        default_domain = await self.domain_manager.get_domain_by_name(
            "general_knowledge"
        )
        if default_domain:
            return default_domain.id
        return None

    async def assign_domain_to_existing_nodes(self, domain_id: UUID) -> int:
        """
        Assign domain to existing nodes that don't have a domain assigned.
        This is useful when migrating from single-domain to multi-domain.

        Args:
            domain_id: Domain UUID to assign

        Returns:
            Number of nodes updated
        """
        async with await self.get_connection() as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    "UPDATE nodes SET domain_id = %s WHERE domain_id IS NULL",
                    (domain_id,),
                )
                updated_count = cur.rowcount
                await conn.commit()

        logger.info("Assigned domain %s to %d existing nodes", domain_id, updated_count)
        return updated_count


# Global domain detector instance
_domain_detector: DomainDetector | None = None


def get_domain_detector() -> DomainDetector:
    """Get global domain detector instance."""
    global _domain_detector
    if _domain_detector is None:
        _domain_detector = DomainDetector()
    return _domain_detector

import json
import logging
import re
from typing import Any

from pydantic import BaseModel, Field

from knowledge_base.config import get_config
from knowledge_base.http_client import ChatCompletionRequest, ChatMessage, HTTPClient
from knowledge_base.repositories import NodeRepository

# Configure logging
config = get_config()
logging.basicConfig(
    level=getattr(logging, config.logging.level), format=config.logging.format
)
logger = logging.getLogger(__name__)

# --- Resolution Decision Model ---


class ResolutionDecision(BaseModel):
    decision: str = Field(
        ...,
        description="One of: 'MERGE' (same entity), 'LINK' (related but distinct), 'KEEP_SEPARATE' (unrelated).",
    )
    reasoning: str = Field(
        ..., description="Brief explanation of why this decision was made."
    )
    canonical_name: str | None = Field(
        None, description="If MERGE, the best name to use for the unified entity."
    )


# --- Entity Resolver Class ---


def _extract_json_from_content(content: str) -> dict[str, Any] | None:
    """
    Extract JSON from markdown code block or plain text.

    Args:
        content: Response content from LLM

    Returns:
        Parsed JSON dict or None if extraction fails
    """
    # Try to find JSON in markdown code block first
    json_match = re.search(r"```json\s*\n(.*?)\n```", content, re.DOTALL)
    if json_match:
        try:
            return json.loads(json_match.group(1))
        except json.JSONDecodeError:
            pass

    # Try to find JSON without markdown
    json_match = re.search(r"\{.*\}", content, re.DOTALL)
    if json_match:
        try:
            return json.loads(json_match.group(0))
        except json.JSONDecodeError:
            pass

    return None


class EntityResolver:
    def __init__(
        self,
        db_conn_str: str,
        base_url: str | None = None,
        api_key: str | None = None,
        model_name: str | None = None,
    ):
        """
        Hybrid Entity Resolver: Combines Vector Similarity (Recall) with LLM Reasoning (Precision).
        """
        config = get_config()
        self.db_conn_str = db_conn_str
        self.client = HTTPClient(base_url, api_key)
        self.model_name = model_name or config.llm.model_name
        self.node_repository = NodeRepository(db_conn_str)

    async def find_candidates(
        self, entity_name: str, embedding: list[float], threshold: float = 0.70
    ) -> list[dict[str, Any]]:
        """
        Find potential duplicates in the DB using vector similarity.
        """
        return await self.node_repository.find_similar(embedding, threshold, limit=5)

    def _normalize_name(self, name: str) -> str:
        """Normalize name by removing titles, parentheses, and extra whitespace."""
        import re

        # Remove titles
        normalized = re.sub(
            r"\b(Dr\.?|Director|Prof\.?|Mr\.?|Ms\.?|Mrs\.?)\s*",
            "",
            name,
            flags=re.IGNORECASE,
        )
        # Remove content in parentheses
        normalized = re.sub(r"\([^)]*\)", "", normalized)
        # Remove extra whitespace and quotes
        normalized = re.sub(r"\s+", " ", normalized.strip())
        normalized = normalized.replace("'", "").replace('"', "")
        return normalized.lower()

    async def judge_pair(
        self, new_entity: dict[str, Any], existing_candidate: dict[str, Any]
    ) -> ResolutionDecision:
        """
        Ask LLM to decide if two entities are the same using plain JSON response.
        """
        messages = [
            ChatMessage(
                role="system",
                content=f"""**Task:** Compare these two entities and decide their relationship.

**Entity A (New):**
- Name: {new_entity["name"]}
- Type: {new_entity["type"]}
- Desc: {new_entity.get("description", "N/A")}

**Entity B (Existing in DB):**
- Name: {existing_candidate["name"]}
- Type: {existing_candidate["type"]}
- Desc: {existing_candidate["description"]}

**Special Instructions for Person Entities:**
- Consider common name variations: titles (Dr., Director, Prof.), nicknames (Sam/Samuel), middle initials (J./John)
- Same person can have different roles/titles over time
- Focus on core identity: last name + first name root

**Options:**
- MERGE: They are same real-world entity (e.g., "Dr. Samuel Oakley" vs "Director Samuel Oakley")
- LINK: They are closely related but distinct (e.g., "Apple" vs "Apple iPhone")
- KEEP_SEPARATE: They are different or just share a generic name

Make a decision based on whether these represent the same real-world entity.

Respond ONLY with valid JSON in this exact format:
{{
  "decision": "MERGE|LINK|KEEP_SEPARATE",
  "reasoning": "Brief explanation of your decision",
  "canonical_name": "Best name to use if MERGE, otherwise null"
}}""",
            ),
        ]

        request = ChatCompletionRequest(
            model=self.model_name,
            messages=messages,
            temperature=0.1,
            max_tokens=500,
        )

        response = await self.client.chat_completion(request)
        if not response or "choices" not in response:
            logger.error("No response from API")
            return ResolutionDecision(
                decision="KEEP_SEPARATE", reasoning="API error", canonical_name=None
            )

        message = response["choices"][0]["message"]
        content = message.get("content", "")

        if not content:
            logger.error("Empty response content")
            return ResolutionDecision(
                decision="KEEP_SEPARATE",
                reasoning="Empty response",
                canonical_name=None,
            )

        # Extract JSON from response
        json_data = _extract_json_from_content(content)

        if not json_data:
            logger.error(f"Failed to extract JSON from response: {content[:200]}...")
            return ResolutionDecision(
                decision="KEEP_SEPARATE",
                reasoning="JSON parse error",
                canonical_name=None,
            )

        # Validate decision
        decision = json_data.get("decision", "KEEP_SEPARATE")
        valid_decisions = ["MERGE", "LINK", "KEEP_SEPARATE"]
        if decision not in valid_decisions:
            logger.warning(
                f"Invalid decision '{decision}', defaulting to KEEP_SEPARATE"
            )
            decision = "KEEP_SEPARATE"

        return ResolutionDecision(
            decision=decision,
            reasoning=json_data.get("reasoning", "No reasoning provided"),
            canonical_name=json_data.get("canonical_name"),
        )

    async def resolve_and_insert(
        self,
        entity: dict[str, Any],
        embedding: list[float],
        domain_id: str | None = None,
    ) -> str:
        candidates = await self.find_candidates(entity["name"], embedding)

        for candidate in candidates:
            if (
                candidate["name"].lower() == entity["name"].lower()
                and candidate["type"] == entity["type"]
            ):
                logger.info(
                    f"Exact match found for {entity['name']}. Returning existing ID."
                )
                return str(candidate["id"])

            normalized_new = self._normalize_name(entity["name"])
            normalized_candidate = self._normalize_name(candidate["name"])
            if (
                normalized_new == normalized_candidate
                and candidate["type"] == entity["type"]
            ):
                logger.info(
                    f"Normalized match found for {entity['name']}. Returning existing ID."
                )
                return str(candidate["id"])

            logger.info(
                f"Judging pair: {entity['name']} vs {candidate['name']} (Sim: {candidate['similarity']:.2f})"
            )
            decision = await self.judge_pair(entity, candidate)

            if decision.decision == "MERGE":
                logger.info(
                    f"Merging {entity['name']} -> {candidate['name']} ({decision.reasoning})"
                )
                return str(candidate["id"])

            elif decision.decision == "LINK":
                pass

        return await self._insert_entity(entity, embedding, domain_id)

    async def _insert_entity(
        self,
        entity: dict[str, Any],
        embedding: list[float],
        domain_id: str | None = None,
    ) -> str:
        return await self.node_repository.create(entity, embedding, domain_id)


# --- Usage Example ---
if __name__ == "__main__":
    # Dummy test without DB connection
    print("EntityResolver defined. Requires live DB and Embeddings to run full test.")

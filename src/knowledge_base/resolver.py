import logging

import psycopg
from pydantic import BaseModel, Field

from knowledge_base.config import get_config
from knowledge_base.http_client import ChatCompletionRequest, ChatMessage, HTTPClient

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

    async def find_candidates(
        self, entity_name: str, embedding: list[float], threshold: float = 0.70
    ) -> list[dict]:
        """
        Find potential duplicates in the DB using vector similarity.
        """
        candidates = []
        async with await psycopg.AsyncConnection.connect(self.db_conn_str) as conn:
            async with conn.cursor() as cur:
                # Use cosine distance (<=>). Lower is better, so 1 - distance = similarity.
                # Threshold check: distance < (1 - threshold)
                await cur.execute(
                    """
                    SELECT id, name, type, description, 1 - (embedding <=> %s::vector) as similarity
                    FROM nodes
                    WHERE 1 - (embedding <=> %s::vector) > %s
                    ORDER BY similarity DESC
                    LIMIT 5
                    """,
                    (embedding, embedding, threshold),
                )
                async for row in cur:
                    candidates.append(
                        {
                            "id": str(row[0]),
                            "name": row[1],
                            "type": row[2],
                            "description": row[3],
                            "similarity": row[4],
                        }
                    )
        return candidates

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
        self, new_entity: dict, existing_candidate: dict
    ) -> ResolutionDecision:
        """
        Ask LLM to decide if two entities are the same.
        """
        messages = [
            ChatMessage(
                role="system",
                content=f"""
                   **Task:** Compare these two entities and decide their relationship.
                   
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
                   """,
            ),
        ]

        # Define the structured output tool
        tools = [
            {
                "type": "function",
                "function": {
                    "name": "make_resolution_decision",
                    "description": "Make a decision about entity relationship",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "decision": {
                                "type": "string",
                                "enum": ["MERGE", "LINK", "KEEP_SEPARATE"],
                                "description": "One of: 'MERGE' (same entity), 'LINK' (related but distinct), 'KEEP_SEPARATE' (unrelated).",
                            },
                            "reasoning": {
                                "type": "string",
                                "description": "Brief explanation of why this decision was made.",
                            },
                            "canonical_name": {
                                "type": "string",
                                "description": "If MERGE, best name to use for unified entity.",
                            },
                        },
                        "required": ["decision", "reasoning"],
                    },
                },
            }
        ]

        request = ChatCompletionRequest(
            model=self.model_name,
            messages=messages,
            tools=tools,
            tool_choice="auto",
            max_tokens=1000,
        )

        response = await self.client.chat_completion(request)
        if not response or "choices" not in response:
            logger.error("No response from API")
            return ResolutionDecision(
                decision="KEEP_SEPARATE", reasoning="API error", canonical_name=None
            )

        message = response["choices"][0]["message"]
        tool_calls = message.get("tool_calls", [])

        if not tool_calls:
            logger.error("No tool calls in response")
            return ResolutionDecision(
                decision="KEEP_SEPARATE", reasoning="No tool calls", canonical_name=None
            )

        tool_call = tool_calls[0]
        if tool_call["function"]["name"] != "make_resolution_decision":
            logger.error(f"Unexpected tool call: {tool_call['function']['name']}")
            return ResolutionDecision(
                decision="KEEP_SEPARATE", reasoning="Wrong tool", canonical_name=None
            )

        try:
            import json

            arguments = json.loads(tool_call["function"]["arguments"])
            return ResolutionDecision(
                decision=arguments.get("decision", "KEEP_SEPARATE"),
                reasoning=arguments.get("reasoning", "Parse error"),
                canonical_name=arguments.get("canonical_name"),
            )
        except Exception as e:
            logger.error(f"Failed to parse tool response: {e}")
            return ResolutionDecision(
                decision="KEEP_SEPARATE", reasoning="Parse error", canonical_name=None
            )

    async def resolve_and_insert(
        self, entity: dict, embedding: list[float], domain_id: str | None = None
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
                return candidate["id"]

            normalized_new = self._normalize_name(entity["name"])
            normalized_candidate = self._normalize_name(candidate["name"])
            if (
                normalized_new == normalized_candidate
                and candidate["type"] == entity["type"]
            ):
                logger.info(
                    f"Normalized match found for {entity['name']}. Returning existing ID."
                )
                return candidate["id"]

            logger.info(
                f"Judging pair: {entity['name']} vs {candidate['name']} (Sim: {candidate['similarity']:.2f})"
            )
            decision = await self.judge_pair(entity, candidate)

            if decision.decision == "MERGE":
                logger.info(
                    f"Merging {entity['name']} -> {candidate['name']} ({decision.reasoning})"
                )
                return candidate["id"]

            elif decision.decision == "LINK":
                pass

        return await self._insert_entity(entity, embedding, domain_id)

    async def _insert_entity(
        self, entity: dict, embedding: list[float], domain_id: str | None = None
    ) -> str:
        async with await psycopg.AsyncConnection.connect(self.db_conn_str) as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    """
                    INSERT INTO nodes (name, type, description, embedding, domain_id)
                    VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT (name, type, domain_id) DO UPDATE
                    SET description = EXCLUDED.description, updated_at = NOW()
                    RETURNING id
                    """,
                    (
                        entity["name"],
                        entity["type"],
                        entity.get("description", ""),
                        embedding,
                        domain_id,
                    ),
                )
                row = await cur.fetchone()
                await conn.commit()
                if row is None:
                    await cur.execute(
                        "SELECT id FROM nodes WHERE name = %s AND type = %s AND domain_id = %s",
                        (entity["name"], entity["type"], domain_id),
                    )
                    row = await cur.fetchone()
                    if row is None:
                        raise RuntimeError(
                            f"Failed to insert or find entity: {entity['name']}"
                        )
                return str(row[0])


# --- Usage Example ---
if __name__ == "__main__":
    # Dummy test without DB connection
    print("EntityResolver defined. Requires live DB and Embeddings to run full test.")

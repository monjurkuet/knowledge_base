import asyncio
import json
import logging
from typing import Sequence, Union, Any

from pydantic import BaseModel, Field

from knowledge_base.config import get_config
from knowledge_base.http_client import HTTPClient, ChatMessage, ChatCompletionRequest

# Configure logging
config = get_config()
logging.basicConfig(
    level=getattr(logging, config.logging.level), format=config.logging.format
)
logger = logging.getLogger(__name__)

# --- Pydantic Models for Structured Output ---


class Entity(BaseModel):
    name: str = Field(..., description="Unique name of the entity.")
    type: str = Field(
        ...,
        description="Type of the entity (e.g., Person, Organization, Event, Concept).",
    )
    description: str = Field(
        ..., description="Comprehensive description of the entity based on the text."
    )


class Relationship(BaseModel):
    source: str = Field(..., description="Name of the source entity.")
    target: str = Field(..., description="Name of the target entity.")
    type: str = Field(
        ...,
        description="Type of relationship (e.g., AUTHORED, LEADS, PART_OF). UPPERCASE.",
    )
    description: str = Field(
        ..., description="Contextual explanation of why this relationship exists."
    )
    weight: float = Field(
        default=1.0, description="Strength of relationship (0.0 to 1.0)."
    )


class Event(BaseModel):
    primary_entity: str = Field(
        ..., description="The main entity involved in the event."
    )
    description: str = Field(..., description="Specific description of what happened.")
    raw_time: str = Field(
        ...,
        description="The original time description from the text (e.g., 'Q1 2026', 'last week').",
    )
    normalized_date: str | None = Field(
        None, description="ISO 8601 date if possible (YYYY-MM-DD)."
    )


class KnowledgeGraph(BaseModel):
    """
    Structured representation of a knowledge graph extracted from text.
    """

    entities: list[Entity] = Field(default_factory=list)
    relationships: list[Relationship] = Field(default_factory=list)
    events: list[Event] = Field(default_factory=list)


# --- Ingestor Class ---


class GraphIngestor:
    def __init__(
        self,
        base_url: str | None = None,
        api_key: str | None = None,
        model_name: str | None = None,
    ):
        """
        Initialize the Graph Ingestor with OpenAI-compatible local API.

        Args:
            base_url: The local endpoint for your inference server (from config if None).
            api_key: API key (from config if None, not required for local servers).
            model_name: The ID of the model (from config if None).
        """
        config = get_config()
        self.client = HTTPClient(base_url, api_key)
        self.model_name = model_name or config.llm.model_name
        logger.info(f"Initialized GraphIngestor with model: {self.model_name}")

    async def list_available_models(self) -> list[str]:
        """Fetch the list of model IDs available on the server."""
        try:
            import httpx

            url = f"{self.client.api_url}/models"
            headers = {"Content-Type": "application/json"}
            async with httpx.AsyncClient(timeout=self.client.timeout) as client:
                response = await client.get(url, headers=headers)
                response.raise_for_status()
                return [m["id"] for m in response.json().get("data", [])]
        except Exception as e:
            logger.error(f"Failed to list models: {e}")
            return []

    async def extract(
        self,
        text: str,
        entity_types: Sequence[Union[str, dict[str, Any]]] | None = None,
        relationship_types: Sequence[Union[str, dict[str, Any]]] | None = None,
    ) -> KnowledgeGraph:
        """
        High-Fidelity Extraction Pipeline (2-Pass Gleaning).
        Uses hierarchical prompting to ensure zero compromise on quality.
        """
        logger.info(f"Starting extraction using model: {self.model_name}...")

        # Pass 1: Core Extraction
        core_graph = await self._pass_1_core(text, entity_types, relationship_types)
        logger.info(f"Pass 1 complete. Found {len(core_graph.entities)} entities.")

        # Pass 2: Gleaning (Finding missed details)
        # For gleaning, we might want to pass the types again, but for now let's keep it simple
        gleaned_graph = await self._pass_2_gleaning(text, core_graph, entity_types)
        logger.info(
            f"Pass 2 complete. Found {len(gleaned_graph.entities)} additional entities."
        )

        # Merge
        final_graph = self._merge_graphs(core_graph, gleaned_graph)
        logger.info(
            f"Extraction complete. Final count: {len(final_graph.entities)} entities, {len(final_graph.relationships)} relationships."
        )

        return final_graph

    async def _pass_1_core(
        self,
        text: str,
        entity_types: Sequence[Union[str, dict[str, Any]]] | None = None,
        relationship_types: Sequence[Union[str, dict[str, Any]]] | None = None,
    ) -> KnowledgeGraph:
        # Construct dynamic guidelines
        entity_guideline = "1. ENTITIES: Identify People, Organizations, Projects, Concepts, and Locations."
        if entity_types:
            # Handle both strings and dicts
            formatted_types = []
            for et in entity_types:
                if isinstance(et, str):
                    formatted_types.append(et)
                elif isinstance(et, dict):
                    # Rich definition
                    desc = f"{et.get('name')} ({et.get('description', '')})"
                    if et.get("synonyms"):
                        desc += f" [Synonyms: {', '.join(et['synonyms'])}]"
                    formatted_types.append(desc)

            comma_joined_types = "; ".join(formatted_types)
            entity_guideline = f"1. ENTITIES: Identify the following specific types: {comma_joined_types}. Pay special attention to these categories."

        relationship_guideline = (
            "2. RELATIONSHIPS: Define explicit, typed relationships in UPPERCASE."
        )
        if relationship_types:
            formatted_rels = []
            for rt in relationship_types:
                if isinstance(rt, str):
                    formatted_rels.append(rt)
                elif isinstance(rt, dict):
                    desc = f"{rt.get('name')} ({rt.get('description', '')})"
                    if rt.get("synonyms"):
                        desc += f" [Synonyms: {', '.join(rt['synonyms'])}]"
                    formatted_rels.append(desc)

            comma_joined_types = "; ".join(formatted_rels)
            relationship_guideline = f"2. RELATIONSHIPS: Identify the following specific relationship types: {comma_joined_types}. Use UPPERCASE."

        messages = [
            ChatMessage(
                role="system",
                content="You are a JSON-only extraction engine. You do not speak. You do not offer help. You only output valid JSON matching the requested schema.",
            ),
            ChatMessage(
                role="user",
                content=f"""
                Analyze the text below and extract the knowledge graph.
                
                **CRITICAL INSTRUCTION:** 
                Output ONLY a valid JSON object. 
                Do NOT include markdown formatting (like ```json). 
                Do NOT include any introductory text.
                
                **Text to Analyze:**
                {text}

                **Schema Guidelines:**
                {entity_guideline}
                {relationship_guideline}
                3. EVENTS: Extract specific occurrences with their original time descriptions. 
                   - Link event to its primary entity.
                   - Try to normalize date to ISO 8601 (YYYY-MM-DD) if possible.
                4. DESCRIPTIONS: Provide rich, factual descriptions for every node, edge, and event.

                **Required JSON Structure:**
                {{
                    "entities": [
                        {{"name": "EntityName", "type": "EntityType", "description": "Description..."}}
                    ],
                    "relationships": [
                        {{"source": "EntityName", "target": "OtherEntity", "type": "RELATIONSHIP_TYPE", "description": "Context...", "weight": 1.0}}
                    ],
                    "events": [
                        {{"primary_entity": "EntityName", "description": "Event description", "raw_time": "2024", "normalized_date": "2024-01-01"}}
                    ]
                }}
                """,
            ),
        ]

        # Add function definition for structured output
        tools = [
            {
                "type": "function",
                "function": {
                    "name": "extract_knowledge_graph",
                    "description": "Extract entities, relationships, and events from text",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "entities": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "name": {"type": "string"},
                                        "type": {"type": "string"},
                                        "description": {"type": "string"},
                                    },
                                    "required": ["name", "type", "description"],
                                },
                            },
                            "relationships": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "source": {"type": "string"},
                                        "target": {"type": "string"},
                                        "type": {"type": "string"},
                                        "description": {"type": "string"},
                                        "weight": {"type": "number"},
                                    },
                                    "required": [
                                        "source",
                                        "target",
                                        "type",
                                        "description",
                                    ],
                                },
                            },
                            "events": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "primary_entity": {"type": "string"},
                                        "description": {"type": "string"},
                                        "raw_time": {"type": "string"},
                                        "normalized_date": {"type": "string"},
                                    },
                                    "required": [
                                        "primary_entity",
                                        "description",
                                        "raw_time",
                                    ],
                                },
                            },
                        },
                        "required": ["entities", "relationships", "events"],
                    },
                },
            }
        ]

        request = ChatCompletionRequest(
            model=self.model_name,
            messages=messages,
            # tools=tools,
            # tool_choice="auto",
            max_tokens=3000,
            temperature=0.1,
        )

        response = await self.client.chat_completion(request)
        if not response or "choices" not in response:
            logger.error("No response from API")
            return KnowledgeGraph()

        message = response["choices"][0]["message"]
        tool_calls = message.get("tool_calls", [])
        content = message.get("content")

        # Strategy 1: Try to use Tool Calls
        if tool_calls:
            tool_call = tool_calls[0]
            try:
                import json

                arguments = json.loads(tool_call["function"]["arguments"])
                # If arguments are not empty, use them
                if arguments and (
                    arguments.get("entities")
                    or arguments.get("relationships")
                    or arguments.get("events")
                ):
                    logger.info(f"Successfully extracted via Tool Call.")
                    return KnowledgeGraph(**arguments)
                else:
                    logger.warning(
                        "Tool call received but arguments were empty. Attempting fallback to content parsing."
                    )
            except Exception as e:
                logger.error(f"Failed to parse tool response: {e}")

        # Strategy 2: Fallback to Content Parsing (JSON in text)
        if content:
            try:
                import json
                import re

                # Find JSON block
                json_match = re.search(r"\{.*\}", content, re.DOTALL)
                if json_match:
                    json_str = json_match.group(0)
                    data = json.loads(json_str)
                    logger.info(
                        "Successfully extracted via Content Parsing (Fallback)."
                    )
                    return KnowledgeGraph(**data)
            except Exception as e:
                logger.error(f"Failed to parse content JSON: {e}")

        logger.error(
            f"Extraction failed. No valid JSON found in tool calls or content. Raw content: {content}"
        )
        return KnowledgeGraph()

        tool_call = tool_calls[0]
        if tool_call["function"]["name"] != "extract_knowledge_graph":
            logger.error(f"Unexpected tool call: {tool_call['function']['name']}")
            return KnowledgeGraph()

        try:
            import json

            arguments = json.loads(tool_call["function"]["arguments"])
            logger.info(
                f"DEBUG: Tool arguments received: {json.dumps(arguments, indent=2)}"
            )
            return KnowledgeGraph(**arguments)
        except Exception as e:
            logger.error(f"Failed to parse tool response: {e}")
            return KnowledgeGraph()

    async def _pass_2_gleaning(
        self,
        text: str,
        existing_graph: KnowledgeGraph,
        entity_types: Sequence[Union[str, dict[str, Any]]] | None = None,
    ) -> KnowledgeGraph:
        """
        The 'Zero Compromise' quality pass. Finds details missed in first pass.
        """
        existing_names = [e.name for e in existing_graph.entities]

        messages = [
            ChatMessage(
                role="system",
                content="You are a Detail-Oriented Forensic Auditor. Your goal is to find missed entities, subtle relationships, and overlooked TEMPORAL EVENTS.",
            ),
            ChatMessage(
                role="user",
                content=f"""
                I have already extracted these entities: {json.dumps(existing_names[:60])}.
                
                **Your Goal:**
                Perform a second pass on text. Identify:
                1. ANY entity or relationship not listed above.
                2. Specific DATES or TIME-BOUND milestones that were skipped.
                3. Chronological links between events.
                
                **Constraint:** Only output NEW information.
                
                **Text to Analyze:**
                {text}
                """,
            ),
        ]

        # Use same tool definition as pass 1
        tools = [
            {
                "type": "function",
                "function": {
                    "name": "extract_knowledge_graph",
                    "description": "Extract entities, relationships, and events from text",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "entities": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "name": {"type": "string"},
                                        "type": {"type": "string"},
                                        "description": {"type": "string"},
                                    },
                                    "required": ["name", "type", "description"],
                                },
                            },
                            "relationships": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "source": {"type": "string"},
                                        "target": {"type": "string"},
                                        "type": {"type": "string"},
                                        "description": {"type": "string"},
                                        "weight": {"type": "number"},
                                    },
                                    "required": [
                                        "source",
                                        "target",
                                        "type",
                                        "description",
                                    ],
                                },
                            },
                            "events": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "primary_entity": {"type": "string"},
                                        "description": {"type": "string"},
                                        "raw_time": {"type": "string"},
                                        "normalized_date": {"type": "string"},
                                    },
                                    "required": [
                                        "primary_entity",
                                        "description",
                                        "raw_time",
                                    ],
                                },
                            },
                        },
                        "required": ["entities", "relationships", "events"],
                    },
                },
            }
        ]

        request = ChatCompletionRequest(
            model=self.model_name,
            messages=messages,
            tools=tools,
            tool_choice="auto",
            max_tokens=3000,
        )

        response = await self.client.chat_completion(request)
        if not response or "choices" not in response:
            logger.error("No response from API")
            return KnowledgeGraph()

        message = response["choices"][0]["message"]
        tool_calls = message.get("tool_calls", [])

        if not tool_calls:
            logger.error("No tool calls in response")
            return KnowledgeGraph()

        tool_call = tool_calls[0]
        if tool_call["function"]["name"] != "extract_knowledge_graph":
            logger.error(f"Unexpected tool call: {tool_call['function']['name']}")
            return KnowledgeGraph()

        try:
            arguments = json.loads(tool_call["function"]["arguments"])
            return KnowledgeGraph(**arguments)
        except Exception as e:
            logger.error(f"Failed to parse tool response: {e}")
            return KnowledgeGraph()

    def _merge_graphs(self, g1: KnowledgeGraph, g2: KnowledgeGraph) -> KnowledgeGraph:
        """
        Merge two graphs, preventing exact name duplicates.
        """
        entities = {e.name.lower(): e for e in g1.entities}

        for e in g2.entities:
            if e.name.lower() not in entities:
                entities[e.name.lower()] = e
            else:
                if len(e.description) > len(entities[e.name.lower()].description):
                    entities[e.name.lower()].description = e.description

        # Merge edges
        edges = set()
        final_edges = []

        for r in g1.relationships + g2.relationships:
            key = (r.source.lower(), r.target.lower(), r.type.upper())
            if key not in edges:
                edges.add(key)
                final_edges.append(r)

        # Merge events (simple dedupe by description)
        event_descs = set()
        final_events = []
        for ev in g1.events + g2.events:
            if ev.description not in event_descs:
                event_descs.add(ev.description)
                final_events.append(ev)

        return KnowledgeGraph(
            entities=list(entities.values()),
            relationships=final_edges,
            events=final_events,
        )


# --- Usage Example ---
if __name__ == "__main__":

    async def run_test():
        ingestor = GraphIngestor()

        sample_text = """
        Project Alpha is a confidential research initiative led by Dr. Sarah Chen at the AI Research Division of Cyberdyne Systems. 
        It focuses on developing self-optimizing cognitive architectures. 
        The project received funding from the Department of Advanced Technology in late 2024.
        """

        try:
            # Check models first to be sure
            available = await ingestor.list_available_models()
            print(f"Available Models: {available}")

            if ingestor.model_name not in available and available:
                print(
                    f"Warning: {ingestor.model_name} not found. Switching to {available[0]}"
                )
                ingestor.model_name = available[0]

            result = await ingestor.extract(sample_text)
            print("\n--- Extracted Knowledge Graph ---")
            print(result.model_dump_json(indent=2))

        except Exception as e:
            logger.error(f"Extraction failed: {e}")

    asyncio.run(run_test())

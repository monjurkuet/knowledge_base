import asyncio
import logging
import os

from google import genai
from psycopg import AsyncConnection
from pydantic import BaseModel, Field

from knowledge_base.config import get_config
from knowledge_base.http_client import HTTPClient, ChatMessage, ChatCompletionRequest

# Configure logging
config = get_config()
logging.basicConfig(
    level=getattr(logging, config.logging.level), format=config.logging.format
)
logger = logging.getLogger(__name__)

# --- Pydantic Models for Summaries ---


class Finding(BaseModel):
    summary: str = Field(..., description="Concise statement of a key fact or insight.")
    explanation: str = Field(..., description="Detailed explanation of the finding.")


class CommunityReport(BaseModel):
    title: str = Field(
        ..., description="A descriptive title for this community of entities."
    )
    summary: str = Field(
        ..., description="High-level executive summary of the community's themes."
    )
    rating: float = Field(
        ...,
        description="Importance rating (0-10) of this community to the overall domain.",
    )
    findings: list[Finding] = Field(
        ..., description="List of specific insights or claims found in this community."
    )


# --- Summarizer Class ---


class CommunitySummarizer:
    def __init__(
        self,
        db_conn_str: str,
        base_url: str | None = None,
        api_key: str | None = None,
        model_name: str | None = None,
    ):
        config = get_config()
        self.db_conn_str = db_conn_str
        self.client = HTTPClient(base_url, api_key)
        self.model_name = model_name or config.llm.model_name

    async def summarize_all(self):
        """
        Main entry point: Summarize communities level by level, bottom-up.
        """
        # 1. Get max level
        async with await AsyncConnection.connect(self.db_conn_str) as conn:
            async with conn.cursor() as cur:
                await cur.execute("SELECT MAX(level) FROM communities")
                row = await cur.fetchone()
                max_level = row[0] if row and row[0] is not None else 0

        logger.info(f"Starting Recursive Summarization. Max Level: {max_level}")

        # 2. Iterate levels from 0 (Leaf) to Max (Root)
        # Note: In some implementations, 0 is root. In ours (Leiden), let's assume 0 is the finest grain (Leaf).
        # We process Level 0 first, then Level 1 can use Level 0's summaries.

        for level in range(max_level + 1):
            logger.info(f"--- Processing Level {level} ---")
            await self._process_level(level)

    async def _process_level(self, level: int):
        """
        Summarize all communities at a specific level.
        """
        async with await AsyncConnection.connect(self.db_conn_str) as conn:
            async with conn.cursor() as cur:
                # Fetch communities at this level needing summarization
                # (For now, we re-summarize everything. Production would use a 'dirty' flag)
                await cur.execute(
                    "SELECT id, title FROM communities WHERE level = %s", (level,)
                )
                communities = await cur.fetchall()

                for comm_id, _ in communities:
                    await self._summarize_community(comm_id, level)

    async def _summarize_community(self, community_id: str, level: int):
        """
        Generate a report for a single community.
        """
        context_text = await self._gather_context(community_id, level)

        if not context_text:
            logger.warning(f"No context found for Community {community_id}. Skipping.")
            return

        logger.info(
            f"Generating report for Community {community_id} (Level {level})..."
        )

        try:
            messages = [
                ChatMessage(
                    role="system",
                    content="You are an expert Intelligence Analyst. Your goal is to synthesize structured data into a comprehensive report.",
                ),
                ChatMessage(
                    role="user",
                    content=f"""
                    **Task:** Analyze provided entities and relationships to generate a Community Report.
                    
                    **Context (Entities & Relations):**
                    {context_text[:50000]}  # Truncate to avoid context overflow if huge
                    
                    **Requirements:**
                    1. Title: Create a specific, descriptive title.
                    2. Summary: Write a high-level overview.
                    3. Findings: List key insights, contradictions, or patterns.
                    4. Rating: Assess importance (0-10).
                    """,
                ),
            ]

            # Define tool for structured output
            tools = [
                {
                    "type": "function",
                    "function": {
                        "name": "generate_community_report",
                        "description": "Generate a community analysis report",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "title": {
                                    "type": "string",
                                    "description": "A descriptive title for this community of entities.",
                                },
                                "summary": {
                                    "type": "string",
                                    "description": "High-level executive summary of community's themes.",
                                },
                                "rating": {
                                    "type": "number",
                                    "description": "Importance rating (0-10) of this community to overall domain.",
                                },
                                "findings": {
                                    "type": "array",
                                    "items": {
                                        "type": "object",
                                        "properties": {
                                            "summary": {"type": "string"},
                                            "explanation": {"type": "string"},
                                        },
                                        "required": ["summary", "explanation"],
                                    },
                                    "description": "List of specific insights or claims found in this community.",
                                },
                            },
                            "required": ["title", "summary", "rating", "findings"],
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
                return None

            message = response["choices"][0]["message"]
            tool_calls = message.get("tool_calls", [])

            if not tool_calls:
                logger.error("No tool calls in response")
                return None

            tool_call = tool_calls[0]
            if tool_call["function"]["name"] != "generate_community_report":
                logger.error(f"Unexpected tool call: {tool_call['function']['name']}")
                return None

            try:
                import json

                arguments = json.loads(tool_call["function"]["arguments"])
                report = CommunityReport(**arguments)
            except Exception as e:
                logger.error(f"Failed to parse tool response: {e}")
                return None

            # Save to DB
            await self._save_report(community_id, report)

        except Exception as e:
            logger.error(f"Failed to summarize community {community_id}: {e}")

    async def _gather_context(self, community_id: str, level: int) -> str:
        """
        Gather text context.
        - If Level 0: Gather raw Entity descriptions + Relations.
        - If Level > 0: Gather Summaries of child communities (Recursive step).
        """
        context = []

        async with await AsyncConnection.connect(self.db_conn_str) as conn:
            async with conn.cursor() as cur:
                if level == 0:
                    # Gather Entities
                    await cur.execute(
                        """
                        SELECT n.name, n.description 
                        FROM community_membership cm
                        JOIN nodes n ON cm.node_id = n.id
                        WHERE cm.community_id = %s
                        LIMIT 50
                        """,
                        (community_id,),
                    )
                    rows = await cur.fetchall()
                    context.append("### Member Entities:")
                    for r in rows:
                        context.append(f"- {r[0]}: {r[1]}")

                    # Gather Relationships
                    await cur.execute(
                        """
                        SELECT n1.name, e.type, n2.name, e.description
                        FROM edges e
                        JOIN nodes n1 ON e.source_id = n1.id
                        JOIN nodes n2 ON e.target_id = n2.id
                        JOIN community_membership cm1 ON n1.id = cm1.node_id
                        JOIN community_membership cm2 ON n2.id = cm2.node_id
                        WHERE cm1.community_id = %s AND cm2.community_id = %s
                        LIMIT 50
                        """,
                        (community_id, community_id),
                    )
                    rows = await cur.fetchall()
                    context.append("\n### Internal Relationships:")
                    for r in rows:
                        context.append(f"- {r[0]} --[{r[1]}]--> {r[2]}: {r[3]}")

                else:
                    # Level > 0: Gather Child Community Summaries
                    await cur.execute(
                        """
                        SELECT c.title, c.summary 
                        FROM community_hierarchy ch
                        JOIN communities c ON ch.child_id = c.id
                        WHERE ch.parent_id = %s
                        """,
                        (community_id,),
                    )
                    rows = await cur.fetchall()
                    context.append("### Sub-Communities (Children):")
                    for r in rows:
                        context.append(f"#### {r[0]}\nSummary: {r[1]}\n")

        return "\n".join(context)

    async def _get_embedding(self, text: str) -> list[float]:
        """
        Helper to get embeddings using Google GenAI.
        """
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("GOOGLE_API_KEY is missing. Cannot generate embeddings.")

        client = genai.Client(api_key=api_key)

        try:
            result = client.models.embed_content(
                model="text-embedding-004",
                contents=text,
            )
            if not result or not hasattr(result, "embeddings") or not result.embeddings:
                raise RuntimeError("API response is invalid or missing embeddings.")

            embedding = result.embeddings[0]

            if not hasattr(embedding, "values"):
                raise RuntimeError("Embedding object is invalid or missing 'values'.")

            if embedding.values is None:
                raise ValueError("Embedding values are None.")

            return embedding.values
        except Exception as e:
            raise RuntimeError(f"Google embedding API failed: {e}") from e

    async def _save_report(self, community_id: str, report: CommunityReport):
        """
        Persist the generated report and its vector embedding.
        """
        # Generate embedding for the summary to enable global semantic search
        embedding = await self._get_embedding(f"{report.title} {report.summary}")

        async with await AsyncConnection.connect(self.db_conn_str) as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    """
                    UPDATE communities 
                    SET title = %s, summary = %s, full_content = %s, embedding = %s, updated_at = NOW()
                    WHERE id = %s
                    """,
                    (
                        report.title,
                        report.summary,
                        report.model_dump_json(),
                        embedding,
                        community_id,
                    ),
                )
                await conn.commit()


# --- CLI Test ---
if __name__ == "__main__":

    async def main():
        config = get_config()
        conn_str = config.database.connection_string

        summarizer = CommunitySummarizer(conn_str)
        await summarizer.summarize_all()

    asyncio.run(main())

import asyncio
import logging
import os

from google import genai
from psycopg import AsyncConnection
from pydantic import BaseModel, Field

from knowledge_base.config import get_config
from knowledge_base.http_client import ChatCompletionRequest, ChatMessage, HTTPClient
from knowledge_base.utils.errors import LLMError, SummarizationError

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

    async def summarize_all(self) -> None:
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

    async def _process_level(self, level: int) -> None:
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

    async def _summarize_community(self, community_id: str, level: int) -> None:
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
                    content="You are an expert Intelligence Analyst. Your goal is to synthesize structured data into a comprehensive report. You do not speak. You only output valid JSON.",
                ),
                ChatMessage(
                    role="user",
                    content=f"""
                    **Task:** Analyze provided entities and relationships to generate a Community Report.
                    
                    **Context (Entities & Relations):**
                    {context_text[:50000]}
                    
                    **CRITICAL INSTRUCTION:** 
                    Output ONLY a valid JSON object matching the structure below.
                    Do NOT include markdown formatting.
                    
                    **Required JSON Structure:**
                    {{
                        "title": "Descriptive Title",
                        "summary": "High-level executive summary...",
                        "rating": 8.5,
                        "findings": [
                            {{"summary": "Key insight 1", "explanation": "Detailed explanation..."}},
                            {{"summary": "Key insight 2", "explanation": "Detailed explanation..."}}
                        ]
                    }}
                    """,
                ),
            ]

            # NOTE: Removed tool definitions to force raw JSON output (more reliable)
            request = ChatCompletionRequest(
                model=self.model_name,
                messages=messages,
                max_tokens=3000,
                temperature=0.1,
            )

            response = await self.client.chat_completion(request)
            if not response or "choices" not in response:
                raise LLMError(
                    "No response from API",
                    model=self.model_name,
                    details={"community_id": community_id, "response": str(response)},
                )

            message = response["choices"][0]["message"]
            content = message.get("content", "")

            try:
                import json
                import re

                # Robust JSON extraction
                json_match = re.search(r"\{.*\}", content, re.DOTALL)
                if json_match:
                    json_str = json_match.group(0)
                    data = json.loads(json_str)
                    report = CommunityReport(**data)

                    # Save to DB
                    await self._save_report(community_id, report)
                    logger.info(f"Successfully generated report for {community_id}")
                else:
                    raise SummarizationError(
                        "No JSON found in response",
                        community_id=community_id,
                        level=level,
                        details={"content": content[:100]},
                    )

            except SummarizationError:
                raise
            except Exception as e:
                raise SummarizationError(
                    "Failed to parse summary response",
                    community_id=community_id,
                    level=level,
                    details={
                        "error": str(e),
                        "content": content[:500] if content else None,
                    },
                ) from e

        except SummarizationError:
            raise
        except Exception as e:
            raise SummarizationError(
                "Failed to summarize community",
                community_id=community_id,
                level=level,
                details={"error": str(e)},
            ) from e

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

    async def _save_report(self, community_id: str, report: CommunityReport) -> None:
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

    async def main() -> None:
        config = get_config()
        conn_str = config.database.connection_string

        summarizer = CommunitySummarizer(conn_str)
        await summarizer.summarize_all()

    asyncio.run(main())

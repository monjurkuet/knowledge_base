import argparse
import asyncio
import logging
import os
from google import genai

from dotenv import load_dotenv

from knowledge_base.community import CommunityDetector
from knowledge_base.config import get_config
from knowledge_base.ingestor import GraphIngestor, KnowledgeGraph
from knowledge_base.resolver import EntityResolver

load_dotenv()

config = get_config()

# Configure logging
logging.basicConfig(
    level=getattr(logging, config.logging.level), format=config.logging.format
)
logger = logging.getLogger(__name__)


class KnowledgePipeline:
    def __init__(self):
        self.config = get_config()
        self.db_conn_str = self.config.database.connection_string

        # Initialize Components
        self.ingestor = GraphIngestor()
        self.resolver = EntityResolver(db_conn_str=self.db_conn_str)
        self.community_detector = CommunityDetector(
            db_conn_str=self.config.database.connection_string
        )

    async def run(self, file_path: str, domain_id: str | None = None):
        """
        Run the full High-Fidelity Pipeline on a single file.
        """
        logger.info(f"=== Starting Pipeline for {file_path} ===")

        # 1. Read File
        try:
            with open(file_path, encoding="utf-8") as f:
                text = f.read()
        except Exception as e:
            logger.error(f"Failed to read file: {e}")
            return

        # 2. Ingestion (Extraction)
        logger.info("--- Stage 1: High-Resolution Extraction ---")
        graph: KnowledgeGraph = await self.ingestor.extract(text)

        # 3. Resolution & Storage
        logger.info("--- Stage 2: Hybrid Entity Resolution & Storage ---")
        await self._store_graph(graph, domain_id)

        # 4. Community Detection (Optional: Usually run in batch, not per file)
        # We'll run it here for the demo/prototype feel
        logger.info("--- Stage 3: Community Detection ---")
        G = await self.community_detector.load_graph()
        if G.number_of_nodes() > 0:
            memberships = self.community_detector.detect_communities(G)
            await self.community_detector.save_communities(memberships)

        # 5. Recursive Summarization
        logger.info("--- Stage 4: Recursive Summarization ---")
        from knowledge_base.summarizer import CommunitySummarizer

        summarizer = CommunitySummarizer(self.db_conn_str)
        await summarizer.summarize_all()

        logger.info("=== Pipeline Complete ===")

    async def _store_graph(self, graph: KnowledgeGraph, domain_id: str | None = None):
        """
        Resolves entities and inserts edges.
        """
        # Map localized entity names to resolved DB UUIDs
        # name_to_id = {"Project Alpha": "uuid-123", ...}
        name_to_id = {}

        # 1. Resolve Entities
        for entity in graph.entities:
            # TODO: Generate embedding for entity (using a simplified method or call an embedding service)
            # For this prototype, we'll use a placeholder or call Google Embeddings if available
            embedding = await self._get_embedding(f"{entity.name} {entity.description}")

            # Resolve and Insert
            # Convert Pydantic model to dict for resolver
            entity_dict = entity.model_dump()
            resolved_id = await self.resolver.resolve_and_insert(
                entity_dict, embedding, domain_id
            )
            name_to_id[entity.name] = resolved_id

        # 2. Insert Edges
        # We need a direct DB connection here or move this to Resolver
        from psycopg import AsyncConnection

        async with await AsyncConnection.connect(self.db_conn_str) as conn:
            async with conn.cursor() as cur:
                for edge in graph.relationships:
                    source_id = name_to_id.get(edge.source)
                    target_id = name_to_id.get(edge.target)

                    if source_id and target_id:
                        await cur.execute(
                            """
                            INSERT INTO edges (source_id, target_id, type, description, weight, domain_id)
                            VALUES (%s, %s, %s, %s, %s, %s)
                            ON CONFLICT (source_id, target_id, type, domain_id) DO NOTHING
                            """,
                            (
                                source_id,
                                target_id,
                                edge.type,
                                edge.description,
                                edge.weight,
                                domain_id,
                            ),
                        )

                # 3. Insert Events
                for event in graph.events:
                    node_id = name_to_id.get(event.primary_entity)
                    if node_id:
                        # Normalize date
                        clean_date = event.normalized_date
                        if clean_date and len(clean_date) == 4 and clean_date.isdigit():
                            clean_date = f"{clean_date}-01-01"
                        elif (
                            clean_date and len(clean_date) == 7 and clean_date[4] == "-"
                        ):
                            clean_date = f"{clean_date}-01"  # Handle YYYY-MM

                        # Use a sub-transaction (SAVEPOINT) to protect the main transaction
                        try:
                            async with conn.transaction():
                                await cur.execute(
                                    """
                                    INSERT INTO events (node_id, description, timestamp, raw_time_desc)
                                    VALUES (%s, %s, %s, %s)
                                    """,
                                    (
                                        node_id,
                                        event.description,
                                        clean_date,
                                        event.raw_time,
                                    ),
                                )
                        except Exception as e:
                            logger.warning(
                                f"Skipping invalid date '{clean_date}' for event: {event.description}. Error: {e}"
                            )
                            # Try one more time without the date
                            try:
                                async with conn.transaction():
                                    await cur.execute(
                                        """
                                        INSERT INTO events (node_id, description, raw_time_desc)
                                        VALUES (%s, %s, %s)
                                        """,
                                        (node_id, event.description, event.raw_time),
                                    )
                            except Exception:
                                pass  # Give up on this specific event

                await conn.commit()

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


def main():
    """CLI entry point for the pipeline"""
    parser = argparse.ArgumentParser(description="Run Knowledge Base Pipeline")
    parser.add_argument("file", help="Path to text file to ingest")
    args = parser.parse_args()

    pipeline = KnowledgePipeline()
    asyncio.run(pipeline.run(args.file))


if __name__ == "__main__":
    main()

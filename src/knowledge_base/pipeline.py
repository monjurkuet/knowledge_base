import argparse
import asyncio
import logging

from dotenv import load_dotenv

from knowledge_base.community import CommunityDetector
from knowledge_base.config import get_config
from knowledge_base.domain_detector import get_domain_detector
from knowledge_base.embedding_service import GoogleEmbeddingService
from knowledge_base.ingestor import GraphIngestor, KnowledgeGraph
from knowledge_base.log_emitter import emit_log
from knowledge_base.resolver import EntityResolver
from knowledge_base.summarizer import CommunitySummarizer

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
        self.domain_detector = get_domain_detector()

        # Initialize Components
        self.ingestor = GraphIngestor()
        self.resolver = EntityResolver(db_conn_str=self.db_conn_str)
        self.community_detector = CommunityDetector(
            db_conn_str=self.config.database.connection_string
        )
        self.embedding_service = GoogleEmbeddingService()

    async def run(
        self,
        file_path: str,
        domain_id: str | None = None,
        channel_id: str | None = None,
    ):
        """
        Run the full High-Fidelity Pipeline on a single file.
        """
        if channel_id:
            await emit_log(channel_id, f"=== Starting Pipeline for {file_path} ===")

        try:
            # 1. Read File
            if channel_id:
                await emit_log(channel_id, "--- Stage 1: Reading file ---")
            try:
                with open(file_path, encoding="utf-8") as f:
                    text = f.read()
            except Exception as e:
                if channel_id:
                    await emit_log(channel_id, f"Failed to read file: {e}", "error")
                return

            # 2. Domain Detection (AI-managed)
            final_domain_id = domain_id
            detected_domain_uuid = None
            if not domain_id:
                if channel_id:
                    await emit_log(channel_id, "--- Stage 1.5: AI Domain Detection ---")
                detected_domain_uuid = (
                    await self.domain_detector.get_or_create_domain_for_text(text)
                )
                if channel_id:
                    if detected_domain_uuid:
                        await emit_log(channel_id, "Domain assigned successfully.")
                    else:
                        await emit_log(
                            channel_id,
                            "Using default domain (domain detection failed).",
                        )

                # Convert UUID to string for database operations
                final_domain_id = (
                    str(detected_domain_uuid) if detected_domain_uuid else None
                )

            # 3. Ingestion (Extraction)
            if channel_id:
                await emit_log(
                    channel_id, "--- Stage 2: High-Resolution Extraction ---"
                )

            entity_types_list = None
            rel_types_list = None

            if detected_domain_uuid:
                try:
                    entity_types = (
                        await self.domain_detector.domain_manager.get_entity_types(
                            detected_domain_uuid
                        )
                    )
                    # Pass the full dicts (rich schema) to ingestor
                    entity_types_list = entity_types

                    rel_types = await self.domain_detector.domain_manager.get_relationship_types(
                        detected_domain_uuid
                    )
                    # Pass the full dicts (rich schema) to ingestor
                    rel_types_list = rel_types

                    if channel_id:
                        await emit_log(
                            channel_id,
                            f"Injecting schema: {len(entity_types_list)} entities, {len(rel_types_list)} relationships.",
                        )
                except Exception as e:
                    logger.error(f"Failed to fetch domain schema: {e}")

            graph: KnowledgeGraph = await self.ingestor.extract(
                text, entity_types=entity_types_list, relationship_types=rel_types_list
            )
            if channel_id:
                await emit_log(
                    channel_id,
                    f"Extracted {len(graph.entities)} entities and {len(graph.relationships)} relationships.",
                )

            # 4. Resolution & Storage
            if channel_id:
                await emit_log(
                    channel_id, "--- Stage 3: Hybrid Entity Resolution & Storage ---"
                )
            await self._store_graph(graph, final_domain_id, channel_id)

            # 5. Community Detection
            if channel_id:
                await emit_log(channel_id, "--- Stage 4: Community Detection ---")
            G = await self.community_detector.load_graph()
            if G.number_of_nodes() > 0:
                memberships = self.community_detector.detect_communities(G)
                await self.community_detector.save_communities(memberships)
                if channel_id:
                    # Extract unique cluster IDs from the list of membership records
                    cluster_ids = {record["cluster_id"] for record in memberships}
                    await emit_log(
                        channel_id,
                        f"Detected {len(cluster_ids)} communities.",
                    )

            # 6. Recursive Summarization
            if channel_id:
                await emit_log(channel_id, "--- Stage 5: Recursive Summarization ---")
            summarizer = CommunitySummarizer(self.db_conn_str)
            await summarizer.summarize_all()
            if channel_id:
                await emit_log(channel_id, "Community summarization complete.")

            if channel_id:
                await emit_log(channel_id, "=== Pipeline Complete ===", "success")

        except Exception as e:
            if channel_id:
                await emit_log(channel_id, f"Pipeline failed: {str(e)}", "error")
            logger.error(f"Pipeline failed for {file_path}: {e}", exc_info=True)

    async def _store_graph(
        self,
        graph: KnowledgeGraph,
        domain_id: str | None = None,
        channel_id: str | None = None,
    ):
        """
        Resolves entities and inserts edges.
        """
        name_to_id = {}

        # 1. Resolve Entities
        if channel_id:
            await emit_log(channel_id, f"Resolving {len(graph.entities)} entities...")
        for i, entity in enumerate(graph.entities):
            embedding = await self._get_embedding(f"{entity.name} {entity.description}")

            entity_dict = entity.model_dump()
            resolved_id = await self.resolver.resolve_and_insert(
                entity_dict, embedding, domain_id
            )
            name_to_id[entity.name] = resolved_id
            if channel_id and (i + 1) % 10 == 0:
                await emit_log(
                    channel_id, f"Resolved {i + 1}/{len(graph.entities)} entities..."
                )

        if channel_id:
            await emit_log(channel_id, "Entity resolution complete.")

        # 2. Insert Edges
        if channel_id:
            await emit_log(
                channel_id, f"Inserting {len(graph.relationships)} relationships..."
            )
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

                if channel_id:
                    await emit_log(channel_id, "Relationship insertion complete.")

                # 3. Insert Events
                if channel_id:
                    await emit_log(
                        channel_id, f"Inserting {len(graph.events)} events..."
                    )
                for event in graph.events:
                    node_id = name_to_id.get(event.primary_entity)
                    if node_id:
                        clean_date = event.normalized_date
                        if clean_date and len(clean_date) == 4 and clean_date.isdigit():
                            clean_date = f"{clean_date}-01-01"
                        elif (
                            clean_date and len(clean_date) == 7 and clean_date[4] == "-"
                        ):
                            clean_date = f"{clean_date}-01"

                        try:
                            async with conn.transaction():
                                await cur.execute(
                                    """
                                    INSERT INTO events (node_id, description, timestamp, raw_time_desc)
                                    VALUES (%s, %s, %s, %s)
                                    ON CONFLICT (node_id, description, raw_time_desc) DO NOTHING
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

                if channel_id:
                    await emit_log(channel_id, "Event insertion complete.")
                await conn.commit()

    async def _get_embedding(self, text: str) -> list[float]:
        """
        Helper to get embeddings using GoogleEmbeddingService with consistent patterns.
        """
        return await self.embedding_service.embed_content(text)


def main():
    """CLI entry point for the pipeline"""
    parser = argparse.ArgumentParser(description="Run Knowledge Base Pipeline")
    parser.add_argument("file", help="Path to text file to ingest")
    args = parser.parse_args()

    pipeline = KnowledgePipeline()
    # For CLI, we don't have a channel_id, so logging will be local
    asyncio.run(pipeline.run(args.file))


if __name__ == "__main__":
    main()

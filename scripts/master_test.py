import asyncio
import logging
import os
import sys

import psycopg
from dotenv import load_dotenv

# Ensure local modules are findable
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from rich.console import Console
from rich.table import Table

from knowledge_base.pipeline import KnowledgePipeline

# Setup
logging.basicConfig(level=logging.ERROR)  # Lower noise for the test runner
logger = logging.getLogger(__name__)
console = Console()
load_dotenv()


class MasterKBTest:
    def __init__(self):
        from knowledge_base.config import get_config

        config = get_config()
        self.db_conn_str = config.database.connection_string
        self.pipeline = KnowledgePipeline()
        self.data_dir = "knowledge_base/tests/data"

    async def reset_db(self):
        """Wipes the DB for a clean test run."""
        console.print("[bold red]Resetting Knowledge Base...[/bold red]")
        async with await psycopg.AsyncConnection.connect(self.db_conn_str) as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    "TRUNCATE nodes, edges, communities, community_membership, community_hierarchy, events CASCADE"
                )
                await conn.commit()

    async def run_pipeline(self):
        """Runs the pipeline on the test dataset."""
        files = sorted(
            [
                os.path.join(self.data_dir, f)
                for f in os.listdir(self.data_dir)
                if f.endswith(".txt")
            ]
        )

        for i, file_path in enumerate(files):
            console.print(
                f"[bold blue]Step {i + 1}: Ingesting {os.path.basename(file_path)}...[/bold blue]"
            )
            await self.pipeline.run(file_path)

    async def verify_results(self):
        """Audits the Knowledge Base state with high precision."""
        console.print("\n[bold green]=== KB MASTER AUDIT REPORT ===[/bold green]")

        async with await psycopg.AsyncConnection.connect(self.db_conn_str) as conn:
            async with conn.cursor() as cur:
                # 1. Entity Resolution Check (The Oakley & Thorne Test)
                await cur.execute(
                    "SELECT id, name FROM nodes WHERE name ILIKE '%Oakley%'"
                )
                oakley_nodes = await cur.fetchall()

                await cur.execute(
                    "SELECT id, name FROM nodes WHERE name ILIKE '%Thorne%'"
                )
                thorne_nodes = await cur.fetchall()

                # 2. Graph Metrics
                await cur.execute("SELECT COUNT(*) FROM nodes")
                node_count_row = await cur.fetchone()
                node_count = node_count_row[0] if node_count_row else 0
                await cur.execute("SELECT COUNT(*) FROM edges")
                edge_count_row = await cur.fetchone()
                edge_count = edge_count_row[0] if edge_count_row else 0

                # 3. Hierarchy Check
                await cur.execute("SELECT MAX(level) FROM communities")
                max_level_row = await cur.fetchone()
                max_level = (
                    max_level_row[0]
                    if max_level_row and max_level_row[0] is not None
                    else -1
                )
                await cur.execute(
                    "SELECT COUNT(*) FROM communities WHERE summary IS NOT NULL AND embedding IS NOT NULL"
                )
                summarized_comms_row = await cur.fetchone()
                summarized_comms = (
                    summarized_comms_row[0] if summarized_comms_row else 0
                )

                # 4. Temporal Check
                await cur.execute("SELECT COUNT(*) FROM events")
                event_count_row = await cur.fetchone()
                event_count = event_count_row[0] if event_count_row else 0

                # 5. Relationship Integrity (Deep Check)
                # Verify if Oakley is linked to 'Project Synapse' or 'Aether'
                await cur.execute("""
                    SELECT COUNT(*) FROM edges e 
                    JOIN nodes n1 ON e.source_id = n1.id 
                    JOIN nodes n2 ON e.target_id = n2.id 
                    WHERE n1.name ILIKE '%Oakley%' AND (n2.name ILIKE '%Synapse%' OR n2.name ILIKE '%Aether%')
                """)
                oakley_rels_row = await cur.fetchone()
                oakley_rels = oakley_rels_row[0] if oakley_rels_row else 0

        # --- Display Results ---
        table = Table(title="Knowledge Base Quality Metrics")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="magenta")
        table.add_column("Status", style="bold")

        # Status Logic
        res_oakley = "PASS" if len(oakley_nodes) == 1 else f"FAIL ({len(oakley_nodes)})"
        res_thorne = "PASS" if len(thorne_nodes) == 1 else f"FAIL ({len(thorne_nodes)})"
        hier_status = (
            "PASS" if max_level is not None and max_level >= 0 else "WARNING (Flat)"
        )
        summ_status = "PASS" if summarized_comms > 0 else "FAIL"
        temp_status = "PASS" if event_count > 8 else "FAIL"
        rel_status = "PASS" if oakley_rels > 0 else "FAIL"
        table.add_row("Resolution: Samuel Oakley", str(len(oakley_nodes)), res_oakley)
        table.add_row("Resolution: Elara Thorne", str(len(thorne_nodes)), res_thorne)
        table.add_row("Relationship Integrity", str(oakley_rels), rel_status)
        table.add_row("Hierarchy Depth", str(max_level), hier_status)
        table.add_row("Intelligence Reports", str(summarized_comms), summ_status)
        table.add_row("Timeline Events", str(event_count), temp_status)
        table.add_row(
            "Total Graph Size", f"{node_count} nodes / {edge_count} edges", "INFO"
        )

        console.print(table)

        # Details on failures
        if len(oakley_nodes) > 1 or len(thorne_nodes) > 1:
            console.print(
                "[red]Deduplication Error:[/red] Cognitive resolution missed some variants."
            )
        if oakley_rels == 0:
            console.print(
                "[red]Context Error:[/red] Failed to extract core project-leader relationships."
            )

    async def run(self):
        await self.reset_db()
        await self.run_pipeline()
        await self.verify_results()


if __name__ == "__main__":
    test = MasterKBTest()
    asyncio.run(test.run())

import asyncio
import logging

import networkx as nx
from graspologic.partition import hierarchical_leiden
from psycopg import AsyncConnection

from knowledge_base.config import get_config

# Configure logging
config = get_config()
logging.basicConfig(
    level=getattr(logging, config.logging.level), format=config.logging.format
)
logger = logging.getLogger(__name__)


class CommunityDetector:
    def __init__(self, db_conn_str: str):
        self.db_conn_str = db_conn_str

    async def load_graph(self) -> nx.Graph:
        """
        Load the entire active knowledge graph from Postgres into NetworkX.
        """
        logger.info("Loading graph from database...")
        G = nx.Graph()

        async with await AsyncConnection.connect(self.db_conn_str) as conn:
            async with conn.cursor() as cur:
                # Load Nodes
                await cur.execute("SELECT id FROM nodes")
                async for row in cur:
                    G.add_node(str(row[0]))

                # Load Edges (weighted)
                await cur.execute("SELECT source_id, target_id, weight FROM edges")
                async for row in cur:
                    G.add_edge(str(row[0]), str(row[1]), weight=float(row[2]))

        logger.info(
            f"Graph loaded: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges."
        )
        return G

    def detect_communities(self, G: nx.Graph) -> list[dict]:
        """Run Hierarchical Leiden algorithm and extract node-to-community mappings."""
        if G.number_of_nodes() == 0:
            logger.warning("Graph is empty. No communities to detect.")
            return []

        max_cluster_size = min(10, max(3, G.number_of_nodes() // 2))

        logger.info(
            f"Running Hierarchical Leiden with max_cluster_size={max_cluster_size}..."
        )
        try:
            hierarchy = hierarchical_leiden(
                G, max_cluster_size=max_cluster_size, random_seed=42
            )

            results = []
            for partition in hierarchy:
                node_id = getattr(partition, "node", None)
                cluster_id = getattr(partition, "cluster", None)
                level = getattr(partition, "level", 0)

                if node_id is not None and cluster_id is not None:
                    results.append(
                        {
                            "node_id": str(node_id),
                            "level": int(level),
                            "cluster_id": f"{level}-{cluster_id}",
                        }
                    )

            levels = len(set(r["level"] for r in results))
            logger.info(
                f"Detection complete. Generated {len(results)} membership records across {levels} level(s)."
            )
            if levels == 1:
                logger.info("Flat clustering is natural for this small graph.")
            return results

        except Exception as e:
            logger.error(f"Failed to run hierarchical clustering: {e}")
            logger.info("Falling back to simple clustering...")
            return self._fallback_clustering(G)

    def _fallback_clustering(self, G: nx.Graph) -> list[dict]:
        """Fallback clustering when hierarchical fails."""
        results = []
        # Level 0: each node in its own cluster
        for i, node in enumerate(G.nodes()):
            results.append({"node_id": str(node), "level": 0, "cluster_id": f"0-{i}"})

        # Level 1: all nodes in single cluster (if more than 1 node)
        if len(G.nodes()) > 1:
            for node in G.nodes():
                results.append({"node_id": str(node), "level": 1, "cluster_id": "1-0"})

        return results

    async def save_communities(self, memberships: list[dict]):
        """
        Persist the community structure and hierarchy to Postgres.
        """
        if not memberships:
            logger.info("No communities to save.")
            return

        logger.info("Saving communities to database...")

        async with await AsyncConnection.connect(self.db_conn_str) as conn:
            async with conn.cursor() as cur:
                # 1. Clear old community data
                await cur.execute(
                    "TRUNCATE community_hierarchy, community_membership, communities CASCADE"
                )

                # 2. Identify unique communities and their parents
                # membership records: {"node_id": uuid, "level": 0, "cluster_id": "0-5"}
                # We need to find for each cluster_id, who is its parent at level + 1
                unique_comms = {}  # cluster_id -> level
                node_paths = {}  # node_id -> {level: cluster_id}

                for m in memberships:
                    unique_comms[m["cluster_id"]] = m["level"]
                    if m["node_id"] not in node_paths:
                        node_paths[m["node_id"]] = {}
                    node_paths[m["node_id"]][m["level"]] = m["cluster_id"]

                # 3. Insert Community Headers
                comm_uuid_map = {}  # map "0-5" -> UUID
                for cid, level in unique_comms.items():
                    await cur.execute(
                        """
                        INSERT INTO communities (title, level, summary)
                        VALUES (%s, %s, %s)
                        RETURNING id
                        """,
                        (f"Cluster {cid}", level, "Pending Summarization"),
                    )
                    row = await cur.fetchone()
                    if row is None:
                        raise RuntimeError(f"Failed to insert community {cid}")
                    new_id = row[0]
                    comm_uuid_map[cid] = new_id

                # 4. Insert Hierarchy
                # A cluster's parent is the cluster the same node belongs to at level + 1
                hierarchy_pairs = set()
                for _, path in node_paths.items():
                    levels = sorted(path.keys())
                    for i in range(len(levels) - 1):
                        child_cid = path[levels[i]]
                        parent_cid = path[levels[i + 1]]
                        hierarchy_pairs.add(
                            (comm_uuid_map[child_cid], comm_uuid_map[parent_cid])
                        )

                for child_uuid, parent_uuid in hierarchy_pairs:
                    await cur.execute(
                        "INSERT INTO community_hierarchy (child_id, parent_id) VALUES (%s, %s)",
                        (child_uuid, parent_uuid),
                    )

                # 5. Insert Memberships
                for m in memberships:
                    comm_uuid = comm_uuid_map[m["cluster_id"]]
                    await cur.execute(
                        "INSERT INTO community_membership (community_id, node_id) VALUES (%s, %s)",
                        (comm_uuid, m["node_id"]),
                    )

                await conn.commit()
        logger.info(
            f"Communities saved. Clusters: {len(comm_uuid_map)}, Hierarchy Links: {len(hierarchy_pairs)}"
        )


# --- CLI Test ---
if __name__ == "__main__":

    async def main():
        import os

        conn_str = f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"

        detector = CommunityDetector(conn_str)
        try:
            G = await detector.load_graph()
            if G.number_of_nodes() > 0:
                memberships = detector.detect_communities(G)
                await detector.save_communities(memberships)
            else:
                print("Graph empty. Skipping detection.")
        except Exception as e:
            logger.error(f"Failed: {e}")

    asyncio.run(main())

import os
from typing import Any

import psycopg
from dotenv import load_dotenv
from rich.console import Console
from rich.panel import Panel
from rich.tree import Tree

load_dotenv()


def fetch_hierarchy() -> tuple[list[Any], list[Any], list[Any]]:
    """
    Fetch the entire community and node hierarchy from Postgres.
    """
    conn_str = f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"

    with psycopg.connect(conn_str) as conn:
        with conn.cursor() as cur:
            # 1. Fetch Communities
            cur.execute(
                "SELECT id, title, level, summary FROM communities ORDER BY level DESC, title ASC"
            )
            communities = cur.fetchall()

            # 2. Fetch Hierarchy Links
            cur.execute("SELECT parent_id, child_id FROM community_hierarchy")
            links = cur.fetchall()

            # 3. Fetch Node Memberships
            cur.execute(
                "SELECT community_id, n.name, n.type FROM community_membership cm JOIN nodes n ON cm.node_id = n.id"
            )
            members = cur.fetchall()

    return communities, links, members


def visualize() -> None:
    console = Console()
    communities, links, members = fetch_hierarchy()

    if not communities:
        console.print(
            "[yellow]Knowledge Base is empty. Run the pipeline first.[/yellow]"
        )
        return

    # Build data structures
    comm_dict = {
        c[0]: {
            "title": c[1],
            "level": c[2],
            "summary": c[3],
            "children": [],
            "nodes": [],
        }
        for c in communities
    }

    # Add children to parents
    for parent_id, child_id in links:
        if parent_id in comm_dict and child_id in comm_dict:
            comm_dict[parent_id]["children"].append(child_id)

    # Add nodes to communities
    for comm_id, node_name, node_type in members:
        if comm_id in comm_dict:
            comm_dict[comm_id]["nodes"].append(f"{node_name} ({node_type})")

    # Find root communities (those that are not children of anyone)
    child_ids = {link[1] for link in links}
    roots = [
        cid
        for cid in comm_dict
        if cid not in child_ids
        and comm_dict[cid]["level"] == max(c[2] for c in communities)
    ]

    # If Leiden didn't create a perfect hierarchy, just take all highest level
    if not roots:
        max_level = max(c[2] for c in communities)
        roots = [cid for cid in comm_dict if comm_dict[cid]["level"] == max_level]

    def add_to_tree(tree: Tree, comm_id: str) -> None:
        data = comm_dict[comm_id]

        # Format the summary
        summary = (
            (data["summary"][:75] + "...")
            if data["summary"] and len(data["summary"]) > 75
            else data["summary"]
        )

        # Branch for community
        branch = tree.add(
            f"[bold cyan]{data['title']}[/bold cyan] [dim](Level {data['level']})[/dim]\n[italic white]{summary}[/italic white]"
        )

        # Add sub-communities
        for child_id in data["children"]:
            add_to_tree(branch, child_id)

        # Add nodes (if Level 0)
        if data["level"] == 0:
            for node in sorted(data["nodes"]):
                branch.add(f"[green]● {node}[/green]")

    # Create Rich Tree
    master_tree = Tree(
        "[bold reverse white] KNOWLEDGE BASE HIERARCHY [/bold reverse white]"
    )

    for root_id in roots:
        add_to_tree(master_tree, root_id)

    console.print(Panel(master_tree, expand=False, border_style="blue"))


if __name__ == "__main__":
    visualize()

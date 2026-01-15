"""
Streamlit UI for the Knowledge Base GraphRAG system
Connects to the FastAPI backend for real-time knowledge graph exploration
"""

import os
from collections import defaultdict
from typing import Any, cast

import networkx as nx  # type: ignore
import plotly.graph_objects as go  # type: ignore
import requests
import streamlit as st  # type: ignore
from dotenv import load_dotenv

load_dotenv()

# --- Configuration ---
API_BASE_URL = os.getenv("STREAMLIT_API_URL", "http://localhost:8000")
WS_URL = os.getenv("STREAMLIT_WS_URL", "ws://localhost:8000/ws")

st.set_page_config(
    page_title="Knowledge Base Explorer",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --- Custom CSS ---
st.markdown(
    """
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .stats-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1f77b4;
        margin: 0.5rem 0;
    }
    .node-card {
        background-color: #ffffff;
        border: 1px solid #e0e0e0;
        border-radius: 0.5rem;
        padding: 1rem;
        margin: 0.5rem 0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
</style>
""",
    unsafe_allow_html=True,
)


# --- API Client ---
class APIClient:
    """Client for interacting with the Knowledge Base API"""

    def __init__(self, base_url: str = API_BASE_URL):
        self.base_url = base_url

    def get_stats(self) -> dict[str, Any]:
        try:
            response = requests.get(f"{self.base_url}/api/stats")
            response.raise_for_status()
            return cast(dict[str, Any], response.json())
        except Exception as e:
            st.error(f"Failed to get stats: {e}")
            return {}

    def get_graph_data(
        self, node_types: list[str] | None = None, limit: int = 200
    ) -> dict[str, Any]:
        try:
            params: dict[str, Any] = {"limit": limit}
            if node_types:
                params["node_types"] = node_types
            response = requests.get(f"{self.base_url}/api/graph", params=params)
            response.raise_for_status()
            return cast(dict[str, Any], response.json())
        except Exception as e:
            st.error(f"Failed to get graph data: {e}")
            return {"nodes": [], "edges": []}

    def get_communities(self) -> list[dict]:
        try:
            response = requests.get(f"{self.base_url}/api/communities")
            response.raise_for_status()
            return cast(list[dict], response.json())
        except Exception:
            return []

    def search_nodes(self, query: str, limit: int = 10) -> dict[str, Any]:
        try:
            response = requests.post(
                f"{self.base_url}/api/search", json={"query": query, "limit": limit}
            )
            response.raise_for_status()
            return cast(dict[str, Any], response.json())
        except Exception as e:
            st.error(f"Search failed: {e}")
            return {"results": [], "count": 0}

    def ingest_text(
        self, text: str, filename: str = "streamlit_upload.txt"
    ) -> dict[str, Any]:
        try:
            response = requests.post(
                f"{self.base_url}/api/ingest/text",
                json={"text": text, "filename": filename},
            )
            response.raise_for_status()
            return cast(dict[str, Any], response.json())
        except Exception as e:
            st.error(f"Ingestion failed: {e}")
            return {"status": "error", "message": str(e)}

    def detect_communities(self) -> dict[str, Any]:
        try:
            response = requests.post(f"{self.base_url}/api/community/detect")
            response.raise_for_status()
            return cast(dict[str, Any], response.json())
        except Exception as e:
            st.error(f"Community detection failed: {e}")
            return {"status": "error", "message": str(e)}

    def run_summarization(self) -> dict[str, Any]:
        try:
            response = requests.post(f"{self.base_url}/api/summarize")
            response.raise_for_status()
            return cast(dict[str, Any], response.json())
        except Exception as e:
            st.error(f"Summarization failed: {e}")
            return {"status": "error", "message": str(e)}


# --- Graph Visualization ---
def create_network_graph(nodes: list[dict], edges: list[dict]) -> go.Figure:
    """Create an interactive network graph visualization"""
    G = nx.Graph()
    node_map = {node["id"]: node for node in nodes}
    for node in nodes:
        G.add_node(node["id"], **node)
    for edge in edges:
        G.add_edge(edge["source"], edge["target"], **edge)

    pos = nx.spring_layout(G, k=0.8, iterations=50)
    edge_x, edge_y = [], []
    for edge in G.edges():
        x0, y0 = pos[edge[0]]
        x1, y1 = pos[edge[1]]
        edge_x.extend([x0, x1, None])
        edge_y.extend([y0, y1, None])

    edge_trace = go.Scatter(
        x=edge_x, y=edge_y, line={"width": 0.5, "color": "#888"}, mode="lines"
    )

    node_x, node_y, node_text, node_color = [], [], [], []
    color_map = {
        "Person": "#FF6B6B",
        "Organization": "#4ECDC4",
        "Event": "#45B7D1",
        "Concept": "#96CEB4",
        "Location": "#FFEAA7",
    }

    for node_id in G.nodes():
        node_data = node_map[node_id]
        x, y = pos[node_id]
        node_x.append(x)
        node_y.append(y)
        node_text.append(f"{node_data.get('name', node_id)}")
        node_color.append(color_map.get(node_data.get("type", "Unknown"), "#BDC3C7"))

    node_trace = go.Scatter(
        x=node_x,
        y=node_y,
        mode="markers+text",
        text=node_text,
        textposition="top center",
        marker={"showscale": False, "color": node_color, "size": 15, "line_width": 2},
    )

    fig = go.Figure(
        data=[edge_trace, node_trace],
        layout=go.Layout(
            showlegend=False,
            hovermode="closest",
            margin={"b": 5, "l": 5, "r": 5, "t": 5},
            xaxis={"showgrid": False, "zeroline": False, "showticklabels": False},
            yaxis={"showgrid": False, "zeroline": False, "showticklabels": False},
        ),
    )
    return fig


# --- Main App Logic ---
def main():
    """Main Streamlit application"""
    api_client = APIClient()

    # Initialize session state
    if "stats" not in st.session_state:
        st.session_state.stats = {}
    if "graph_data" not in st.session_state:
        st.session_state.graph_data = {"nodes": [], "edges": []}
    if "communities" not in st.session_state:
        st.session_state.communities = []
    if "node_types" not in st.session_state:
        st.session_state.node_types = []

    st.markdown(
        '<h1 class="main-header">🧠 Knowledge Base Explorer</h1>',
        unsafe_allow_html=True,
    )

    # --- Sidebar ---
    with st.sidebar:
        st.header("📊 Dashboard")
        if st.button("🔄 Refresh Stats"):
            with st.spinner("Loading..."):
                st.session_state.stats = api_client.get_stats()
        if st.session_state.stats:
            col1, col2 = st.columns(2)
            col1.metric("Nodes", st.session_state.stats.get("nodes_count", 0))
            col2.metric("Edges", st.session_state.stats.get("edges_count", 0))
            col1.metric(
                "Communities", st.session_state.stats.get("communities_count", 0)
            )
            col2.metric("Events", st.session_state.stats.get("events_count", 0))

        st.header("⚙️ Operations")
        if st.button("🔍 Detect Communities"):
            with st.spinner("Running..."):
                result = api_client.detect_communities()
                if result.get("status") == "success":
                    st.success(result.get("message", "Success!"))
                    st.session_state.communities = api_client.get_communities()
                else:
                    st.error("Failed")

        if st.button("📝 Run Summarization"):
            with st.spinner("Running..."):
                result = api_client.run_summarization()
                st.success("Done!") if result.get("status") == "success" else st.error(
                    "Failed"
                )

    # --- Main Content ---
    tab1, tab2, tab3 = st.tabs(["🕸️ Knowledge Graph", "🔍 Search", "📄 Ingest"])

    with tab1:
        st.header("Interactive Knowledge Graph")

        # Fetch initial data if not in state
        if not st.session_state.graph_data["nodes"]:
            with st.spinner("Loading graph..."):
                st.session_state.graph_data = api_client.get_graph_data()
                if st.session_state.graph_data["nodes"]:
                    all_types = sorted(
                        list(
                            {
                                node.get("type", "Unknown")
                                for node in st.session_state.graph_data["nodes"]
                            }
                        )
                    )
                    st.session_state.node_types = all_types

        if st.session_state.graph_data["nodes"]:
            # Node type filter
            selected_types = st.multiselect(
                "Filter by node type:",
                options=st.session_state.node_types,
                default=st.session_state.node_types,
            )

            if st.button("Apply Filter"):
                with st.spinner("Filtering graph..."):
                    st.session_state.graph_data = api_client.get_graph_data(
                        node_types=selected_types
                    )

            # Display graph
            fig = create_network_graph(
                st.session_state.graph_data["nodes"],
                st.session_state.graph_data["edges"],
            )
            st.plotly_chart(fig, use_container_width=True, height=600)

            # Community details
            st.header("Community Analysis")
            if not st.session_state.communities:
                st.session_state.communities = api_client.get_communities()

            if st.session_state.communities:
                for comm in st.session_state.communities:
                    with st.expander(f"Community {comm['id']}: {comm['title']}"):
                        st.write(f"**Nodes:** {comm['node_count']}")
                        if comm["summary"]:
                            st.write(f"**Summary:** {comm['summary']}")
            else:
                st.info("No communities found. Run detection from the sidebar.")

        else:
            st.info("No graph data. Ingest content to build the graph.")

    with tab2:
        st.header("Search Knowledge Base")
        query = st.text_input("Search query", placeholder="Enter search terms...")
        limit = st.slider("Results limit", 5, 50, 10)

        if st.button("🔍 Search") and query:
            with st.spinner("Searching..."):
                results = api_client.search_nodes(query, limit)
            st.subheader(f"Found {results.get('count', 0)} results")
            for res in results.get("results", []):
                st.markdown(
                    f'<div class="node-card"><strong>{res["name"]}</strong> ({res["type"]})<br><small>{res["description"]}</small></div>',
                    unsafe_allow_html=True,
                )

    with tab3:
        st.header("Ingest New Content")
        text_input = st.text_area("Enter text to ingest", height=200)
        uploaded_file = st.file_uploader("Or upload a text file", type=["txt", "md"])

        if st.button("🚀 Ingest Content"):
            content = ""
            if text_input.strip():
                content = text_input
            elif uploaded_file:
                content = uploaded_file.read().decode("utf-8")

            if content:
                with st.spinner("Ingesting..."):
                    result = api_client.ingest_text(content)
                if result.get("status") == "success":
                    st.success("Ingestion successful!")
                    # Clear caches to force a refresh
                    st.session_state.stats = {}
                    st.session_state.graph_data = {"nodes": [], "edges": []}
                    st.session_state.communities = []
                    st.rerun()
                else:
                    st.error(
                        f"Ingestion failed: {result.get('message', 'Unknown error')}"
                    )
            else:
                st.warning("Please provide text or upload a file.")


if __name__ == "__main__":
    main()

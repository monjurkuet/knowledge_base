"""
Streamlit UI for the Knowledge Base GraphRAG system
Connects to the FastAPI backend for real-time knowledge graph exploration
"""

import os
import asyncio
import json
import uuid
from collections import defaultdict
from typing import Any, cast

import networkx as nx
import plotly.graph_objects as go
import requests
import streamlit as st
import websockets
from dotenv import load_dotenv

load_dotenv()

API_BASE_URL = os.getenv("STREAMLIT_API_URL", "http://localhost:8000")
WS_URL = os.getenv("STREAMLIT_WS_URL", "ws://localhost:8000/ws")

st.set_page_config(
    page_title="Knowledge Base Explorer",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded",
)

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
    .log-container {
        background-color: #f0f2f6;
        border-left: 4px solid #1f77b4;
        padding: 1rem;
        border-radius: 0.5rem;
        height: 300px;
        overflow-y: scroll;
        font-family: monospace;
    }
</style>
""",
    unsafe_allow_html=True,
)


class APIClient:
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

    def ingest_text(self, text: str, filename: str, channel_id: str) -> dict[str, Any]:
        try:
            response = requests.post(
                f"{self.base_url}/api/ingest/text",
                json={"text": text, "filename": filename, "channel_id": channel_id},
            )
            response.raise_for_status()
            return cast(dict[str, Any], response.json())
        except Exception as e:
            st.error(f"Ingestion failed: {e}")
            return {"status": "error", "message": str(e)}

    def get_graph_data(self, limit: int = 500) -> dict[str, Any]:
        try:
            response = requests.get(
                f"{self.base_url}/api/graph", params={"limit": limit}
            )
            response.raise_for_status()
            return cast(dict[str, Any], response.json())
        except Exception as e:
            st.error(f"Failed to get graph data: {e}")
            return {}

    def search_nodes(self, query: str, limit: int = 10) -> dict[str, Any]:
        try:
            response = requests.post(
                f"{self.base_url}/api/search",
                json={"query": query, "limit": limit},
            )
            response.raise_for_status()
            return cast(dict[str, Any], response.json())
        except Exception as e:
            st.error(f"Search failed: {e}")
            return {"results": [], "count": 0}

    def get_communities(self) -> list[dict[str, Any]]:
        try:
            response = requests.get(f"{self.base_url}/api/communities")
            response.raise_for_status()
            return cast(list[dict[str, Any]], response.json())
        except Exception as e:
            st.error(f"Failed to get communities: {e}")
            return []


async def websocket_client(channel_id: str, log_container: st.container):
    uri = f"{WS_URL}/{channel_id}"
    try:
        async with websockets.connect(uri) as websocket:
            log_container.info(f"Connected to real-time log stream at {uri}")
            while True:
                try:
                    message = await websocket.recv()
                    data = json.loads(message)
                    if data.get("type") == "log":
                        log_data = data.get("data", {})
                        log_message = log_data.get("message", "")
                        log_type = log_data.get("log_type", "info")

                        if log_type == "success":
                            log_container.success(f"✅ {log_message}")
                        elif log_type == "error":
                            log_container.error(f"❌ {log_message}")
                        else:
                            log_container.text(f"📝 {log_message}")

                except websockets.ConnectionClosed:
                    log_container.warning("Log stream disconnected.")
                    break
    except Exception as e:
        log_container.error(f"WebSocket connection failed: {e}")


def main():
    api_client = APIClient()

    if "channel_id" not in st.session_state:
        st.session_state.channel_id = str(uuid.uuid4())

    st.markdown(
        '<h1 class="main-header">🧠 Knowledge Base Explorer</h1>',
        unsafe_allow_html=True,
    )

    with st.sidebar:
        st.header("📊 Dashboard")
        stats = api_client.get_stats()
        if stats:
            col1, col2 = st.columns(2)
            col1.metric("Nodes", stats.get("nodes_count", 0))
            col2.metric("Edges", stats.get("edges_count", 0))
            col3, col4 = st.columns(2)
            col3.metric("Communities", stats.get("communities_count", 0))
            col4.metric("Events", stats.get("events_count", 0))

        st.header("🔍 Graph Filters")
        node_limit = st.slider("Max Nodes to Display", 10, 1000, 200)
        node_type_filter = st.text_input("Filter by Node Type", "")
        show_labels = st.checkbox("Show Node Labels", True)

    tab1, tab2, tab3 = st.tabs(["🕸️ Knowledge Graph", "🔍 Search", "📄 Ingest"])

    with tab1:
        st.header("🕸️ Knowledge Graph Visualization")

        with st.spinner("Loading graph data..."):
            graph_data = api_client.get_graph_data(limit=node_limit)

        if graph_data and "nodes" in graph_data and "edges" in graph_data:
            nodes = graph_data["nodes"]
            edges = graph_data["edges"]

            if not nodes:
                st.info("No graph data available. Please ingest some content first.")
            else:
                G = nx.Graph()
                for node in nodes:
                    G.add_node(node["id"], **node)
                for edge in edges:
                    G.add_edge(edge["source"], edge["target"], **edge)

                pos = nx.spring_layout(G, k=3, iterations=50)

                node_x = []
                node_y = []
                node_text = []
                node_color = []
                node_size = []

                for node_id in G.nodes():
                    x, y = pos[node_id]
                    node_x.append(x)
                    node_y.append(y)
                    node_data = G.nodes[node_id]
                    label = f"{node_data.get('name', node_id)} ({node_data.get('type', 'Unknown')})"
                    node_text.append(label)
                    node_type = node_data.get("type", "Unknown")
                    color_map = {
                        "Person": "#FF6B6B",
                        "Organization": "#4ECDC4",
                        "Location": "#45B7D1",
                        "Concept": "#96CEB4",
                        "Event": "#FFEAA7",
                        "Publication": "#DDA0DD",
                        "Project": "#98D8C8",
                    }
                    node_color.append(color_map.get(node_type, "#CCCCCC"))
                    node_size.append(20)

                edge_x = []
                edge_y = []
                for edge in G.edges():
                    x0, y0 = pos[edge[0]]
                    x1, y1 = pos[edge[1]]
                    edge_x.extend([x0, x1, None])
                    edge_y.extend([y0, y1, None])

                fig = go.Figure()

                fig.add_trace(
                    go.Scatter(
                        x=edge_x,
                        y=edge_y,
                        line=dict(width=0.5, color="#888"),
                        hoverinfo="none",
                        mode="lines",
                    )
                )

                fig.add_trace(
                    go.Scatter(
                        x=node_x,
                        y=node_y,
                        mode="markers" + ("+text" if show_labels else ""),
                        text=node_text if show_labels else None,
                        textposition="middle center",
                        hovertemplate="%{text}<extra></extra>",
                        marker=dict(
                            size=node_size,
                            color=node_color,
                            line=dict(width=2, color="DarkSlateGrey"),
                        ),
                        name="Nodes",
                    )
                )

                fig.update_layout(
                    title="Knowledge Graph Network",
                    title_x=0.5,
                    showlegend=False,
                    hovermode="closest",
                    margin=dict(b=20, l=5, r=5, t=40),
                    xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                    yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                )

                st.plotly_chart(fig, use_container_width=True)

                st.subheader("🏘️ Communities")
                communities = api_client.get_communities()
                if communities:
                    for i, community in enumerate(communities[:5]):
                        with st.expander(
                            f"Community {i + 1}: {community.get('title', 'Untitled')} ({community.get('node_count', 0)} nodes)"
                        ):
                            st.write(community.get("summary", "No summary available"))
                else:
                    st.info(
                        "No communities detected yet. Run community detection after ingestion."
                    )
        else:
            st.warning(
                "Could not load graph data. Please ensure the API is running and has data."
            )

    with tab2:
        st.header("🔍 Search Knowledge Base")

        search_query = st.text_input(
            "Enter your search query:",
            placeholder="Search for people, organizations, concepts...",
            key="search_input",
        )

        if search_query:
            with st.spinner("Searching knowledge base..."):
                search_results = api_client.search_nodes(query=search_query, limit=10)

            if search_results and search_results.get("results"):
                results = search_results["results"]
                st.success(f"Found {len(results)} results for '{search_query}'")

                for i, result in enumerate(results):
                    with st.container():
                        col1, col2 = st.columns([1, 4])
                        with col1:
                            type_emoji = {
                                "Person": "👤",
                                "Organization": "🏢",
                                "Location": "📍",
                                "Concept": "💡",
                                "Event": "📅",
                                "Publication": "📚",
                                "Project": "📋",
                            }
                            st.markdown(
                                f"### {type_emoji.get(result.get('type', '❓'), '❓')}"
                            )
                        with col2:
                            st.markdown(f"### {result.get('name', 'Unnamed')}")
                            st.caption(f"**Type:** {result.get('type', 'Unknown')}")
                            st.write(
                                result.get("description", "No description available")
                            )
                        st.divider()
            else:
                st.info("No results found. Try a different search term.")
        else:
            st.info("Enter a search query to find entities in your knowledge base.")

    with tab3:
        st.header("Ingest New Content")

        text_input = st.text_area(
            "Enter text to ingest", height=200, key="ingest_text_area"
        )
        uploaded_file = st.file_uploader(
            "Or upload a text file", type=["txt", "md"], key="file_uploader"
        )

        st.header("Real-time Log")
        log_container = st.container()

        if st.button("🚀 Ingest Content", key="ingest_button"):
            content = ""
            filename = "streamlit_ingest.txt"

            if text_input.strip():
                content = text_input
            elif uploaded_file:
                content = uploaded_file.read().decode("utf-8")
                filename = uploaded_file.name

            if content:
                log_container.info("Starting ingestion process...")

                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)

                ws_task = loop.create_task(
                    websocket_client(st.session_state.channel_id, log_container)
                )

                api_task = loop.run_in_executor(
                    None,
                    api_client.ingest_text,
                    content,
                    filename,
                    st.session_state.channel_id,
                )

                loop.run_until_complete(asyncio.gather(ws_task, api_task))

                st.success("Ingestion process finished. Refreshing data...")
                st.experimental_rerun()
            else:
                st.warning("Please provide text or upload a file.")


if __name__ == "__main__":
    main()

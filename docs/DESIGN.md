# High-Fidelity Agentic GraphRAG Architecture

*This document describes the original design vision for the Knowledge Base GraphRAG system. For current implementation details, see [CODEBASE_ARCHITECTURE.md](CODEBASE_ARCHITECTURE.md).*

## Core Philosophy
**"Zero Compromise on Quality."**
We prioritize extraction accuracy, resolution fidelity, and depth of reasoning over ingestion speed. We adopt Microsoft's GraphRAG hierarchical summarization approach but implement it directly on our PostgreSQL + Gemini stack.

## The 4-Stage Pipeline

### Stage 1: High-Resolution Extraction (The "Gleaning" Pattern)
Standard extraction misses subtle connections. We will implement a multi-pass approach:
1.  **Pass 1 (Core)**: Extract primary Entities and explicit Relationships.
2.  **Pass 2 (Gleaning)**: Feed Pass 1 results back to the LLM and ask: *"What entities or subtle relationships did we miss?"*
3.  **Outcome**: Denser, richer graphs compared to single-pass extraction.

### Stage 2: Hybrid Entity Resolution (The Quality Gate)
Duplicate entities (e.g., "J. Doe" vs "Jane Doe") degrade graph quality.
1.  **Candidate Gen**: Use `pgvector` similarity to find existing nodes with similar embeddings.
2.  **LLM Judge**: A specialized prompt analyzes candidate pairs to decide: *Merge*, *Link*, or *Keep Separate*.
3.  **Outcome**: A canonical, clean knowledge graph with no duplication.

### Stage 3: Hierarchical Community Detection
We move beyond flat clustering.
1.  **Algorithm**: **Hierarchical Leiden**. It detects communities at multiple levels (Micro-clusters -> Macro-clusters).
2.  **Structure**:
    *   **Level 0**: Individual Entities/Nodes.
    *   **Level 1**: Small, tight-knit groups (e.g., a specific project team).
    *   **Level 2**: Broader domains (e.g., "AI Research Division").
3.  **Outcome**: A "Zoomable" map of the knowledge base.

### Stage 4: Recursive Summarization (The "Global Brain")
We generate intelligence, not just data.
1.  **Leaf Summaries**: Summarize Level 1 communities based on their contained entities/claims.
2.  **Parent Summaries**: Summarize Level 2 communities based on *Level 1 summaries* (not raw text).
3.  **Outcome**: The system can answer "What is the strategic direction of the organization?" by reading top-level summaries, tracing down to evidence only when needed.

## Database Schema Extensions (Postgres)
We need to extend our schema to support this hierarchy:

```sql
-- New Table: Communities
CREATE TABLE communities (
    id UUID PRIMARY KEY,
    level INTEGER, -- Hierarchy level (0=root, etc.)
    title TEXT,
    summary TEXT, -- The generated insight
    full_content TEXT, -- Detailed report
    embedding vector(768) -- For semantic search over *summaries*
);

-- New Table: Community_Membership
CREATE TABLE community_membership (
    node_id UUID REFERENCES nodes(id),
    community_id UUID REFERENCES communities(id),
    confidence FLOAT
);
```

## Agent Capabilities Upgrade
The Agent gets new, powerful tools:
1.  `global_search(query)`: Searches purely against Community Summaries (fast, high-level).
2.  `local_search(entity)`: Drills down into specific nodes/edges (standard graph traversal).
3.  `drift_search(topic)`: Compares community summaries across time (if we add temporal data).

# Quickstart & Verification Guide

This guide provides a step-by-step walkthrough to set up, run, and verify the core features of the Knowledge Base GraphRAG system. By the end of this guide, you will have:
1.  Set up the database and environment.
2.  Ingested a document and populated the knowledge graph.
3.  Verified the creation of nodes, edges, and communities.
4.  Queried the system via API and direct database access to confirm its state.

---

### 1. Prerequisites

Before you begin, ensure you have the following installed:
*   Python 3.12+
*   `uv` (the Python package manager used in this project)
*   PostgreSQL (v13 or newer)
*   `psql` command-line tool

---

### 2. Step-by-Step Verification

#### Step 1: Environment Setup

First, let's configure the project and database.

```bash
# 1. Install Python dependencies
uv sync --dev

# 2. Create the PostgreSQL database
# (Enter your sudo password if prompted)
createdb knowledge_base

# 3. Connect to the new database to enable extensions
psql -d knowledge_base -c "CREATE EXTENSION IF NOT EXISTS vector; CREATE EXTENSION IF NOT EXISTS \"uuid-ossp\";"

# 4. Initialize the database schema from the project file
psql -d knowledge_base -f database/schema.sql

# 5. Set up your local environment variables
# This copies the template. You should review .env and add your GOOGLE_API_KEY.
cp .env.template .env
```

#### Step 2: Initial State Verification (API)

Before ingesting data, let's confirm the knowledge base is empty.

```bash
# Start the API server in your terminal
uv run kb-server
```

In a **new terminal window**, run the following `curl` command to check the stats:

```bash
curl -X GET http://localhost:8000/api/stats
```

**Expected Output:** The knowledge base should be empty.
```json
{
  "nodes_count": 0,
  "edges_count": 0,
  "communities_count": 0,
  "events_count": 0
}
```
*This confirms the API is running and the database is empty.*

#### Step 3: Run the Ingestion Pipeline

Now, let's ingest a test document. We'll use one of the provided test files.

```bash
# Run the pipeline on a sample document
# This process will take a few minutes as it involves multiple LLM calls.
uv run kb-pipeline tests/data/doc_1_history.txt
```

You will see log output detailing the four stages: Extraction, Resolution, Community Detection, and Summarization.

#### Step 4: Post-Ingestion Verification (API)

Once the pipeline is complete, let's verify that the knowledge graph has been populated.

**1. Check Stats Again:**
```bash
curl -X GET http://localhost:8000/api/stats
```
**Expected Output:** The counts should now be greater than zero.
```json
// Expected output will have non-zero values
{
  "nodes_count": 25,
  "edges_count": 30,
  "communities_count": 5,
  "events_count": 10
}
```
*(Your numbers may vary slightly, but they should not be zero.)*

**2. Verify Node Creation:**
```bash
# Query for a specific entity you know is in the test data
curl -X POST http://localhost:8000/api/search -H "Content-Type: application/json" -d '{"query": "Dr. Aris Thorne"}' | jq
```
**Expected Output:** You should see the resolved entity for "Dr. Aris Thorne".
```json
{
  "results": [
    {
      "id": "some-uuid-string",
      "name": "Dr. Aris Thorne",
      "type": "Person",
      "description": "A pioneering scientist in quantum computing and AI, known for leading Project Synapse and his work on the Chronos mechanism."
    }
  ],
  "count": 1
}
```

**3. Verify Community Summarization:**
```bash
curl -X GET http://localhost:8000/api/communities | jq
```
**Expected Output:** You should see a list of communities, and their `summary` fields should be populated with text, not "Pending Summarization".
```json
[
  {
    "id": "some-uuid-string",
    "title": "Quantum AI Research Group",
    "summary": "This community focuses on the key individuals and concepts related to advanced AI and quantum research...",
    "node_count": 8
  }
]
```

#### Step 5: Advanced Verification (Direct Database Queries)

For a deeper check, you can query the PostgreSQL database directly.

```bash
# Connect to the database
psql -d knowledge_base
```

Now, run these SQL queries inside the `psql` shell:

**1. Confirm Entity Resolution:**
The test data contains both "Dr. Aris Thorne" and "Aris Thorne". The resolver should merge them into a single node. This query should return exactly **one** result.
```sql
SELECT name, type, description FROM nodes WHERE name ILIKE '%Aris Thorne%';
```

**2. Verify Relationship Creation:**
Check if a relationship was created between "Project Synapse" and "Dr. Aris Thorne".
```sql
SELECT n1.name AS source, e.type, n2.name AS target
FROM edges e
JOIN nodes n1 ON e.source_id = n1.id
JOIN nodes n2 ON e.target_id = n2.id
WHERE n1.name = 'Project Synapse' AND n2.name = 'Dr. Aris Thorne';
```
**Expected Output:** You should see a `LEAD_BY` or similar relationship.

**3. Check Community Hierarchy:**
This query shows the parent-child relationships between communities.
```sql
SELECT p.title AS parent_community, c.title AS child_community
FROM community_hierarchy ch
JOIN communities p ON ch.parent_id = p.id
JOIN communities c ON ch.child_id = c.id;
```
**Expected Output:** A list of parent-child community pairs, demonstrating the hierarchy.

**4. Check Event Timeline:**
Verify that temporal events have been extracted and linked to entities.
```sql
SELECT n.name, e.description, e.raw_time_desc
FROM events e
JOIN nodes n ON e.node_id = n.id
WHERE n.name = 'Project Synapse';
```
**Expected Output:** You should see events related to "Project Synapse", like its initiation date.

Type `\\q` to exit the `psql` shell.

#### Step 6: Use the CLI Visualizer

Finally, you can use the built-in tool to visualize the community hierarchy in your terminal.

```bash
# Run the visualization script
uv run python -m knowledge_base.visualize
```

**Expected Output:** A tree-like structure printed in your console, showing communities and the entities within them, which confirms that the entire pipeline from ingestion to analysis is working.

---

### Summary of Verification Checks

- [ ] **API is running:** `GET /api/stats` returns a response.
- [ ] **Ingestion works:** The stats count increases after running `kb-pipeline`.
- [ ] **Entity Resolution works:** Searching for "Dr. Aris Thorne" returns a single, resolved entity.
- [ ] **Relationship Extraction works:** A relationship exists between "Project Synapse" and "Dr. Aris Thorne".
- [ ] **Community Detection works:** The `GET /api/communities` endpoint returns multiple communities.
- [ ] **Hierarchical Summarization works:** Community summaries are descriptive and not "Pending".
- [ ] **CLI Visualization works:** The `visualize` script prints a hierarchy.

If you have successfully completed these steps, you have verified the core functionality of the Knowledge Base GraphRAG system.

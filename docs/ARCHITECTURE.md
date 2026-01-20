# Knowledge Base Architecture

## System Overview

The Knowledge Base is a GraphRAG (Graph Retrieval Augmented Generation) system that extracts knowledge from text documents using LLMs, stores it in a graph database, and provides query capabilities with vector search and hierarchical community detection.

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                         Client Layer                              │
│  ┌───────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │   Web UI       │  │   API Client  │  │   Streamlit  │          │
│  └───────────────┘  └──────────────┘  └──────────────┘          │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                         API Layer                                 │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │  FastAPI Application                                      │  │
│  │  - CORS Middleware                                       │  │
│  │  - Exception Handlers                                     │  │
│  │  - Route Modules                                         │  │
│  └─────────────────────────────────────────────────────────┘  │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │  Routes                                                  │  │
│  │  ├─ domain.py    - Domain management                   │  │
│  │  ├─ ingest.py    - Text/file ingestion                │  │
│  │  ├─ search.py    - Search & graph queries               │  │
│  │  ├─ community.py - Community detection/summarization    │  │
│  │  ├─ stats.py     - Statistics                       │  │
│  │  ├─ health.py    - Health checks & metrics             │  │
│  │  └─ websocket.py - Real-time updates                │  │
│  └─────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Business Logic Layer                          │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │  KnowledgePipeline                                        │  │
│  │  - Orchestrates text ingestion                          │  │
│  │  - Calls GraphIngestor, EntityResolver, etc.           │  │
│  └─────────────────────────────────────────────────────────┘  │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │  GraphIngestor                                            │  │
│  │  - 2-pass extraction (core + gleaning)                 │  │
│  │  - JSON-only response parsing                            │  │
│  └─────────────────────────────────────────────────────────┘  │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │  EntityResolver                                          │  │
│  │  - Hybrid: Vector similarity + LLM reasoning            │  │
│  │  - Uses NodeRepository for DB operations                │  │
│  └─────────────────────────────────────────────────────────┘  │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │  CommunityDetector                                        │  │
│  │  - Hierarchical Leiden algorithm                         │  │
│  │  - Paginated graph loading                               │  │
│  └─────────────────────────────────────────────────────────┘  │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │  CommunitySummarizer                                     │  │  │
│  │  - Recursive summarization                             │  │
│  │  - Uses Google GenAI embeddings                        │  │
│  └─────────────────────────────────────────────────────────┘  │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │  DomainDetector                                          │  │
│  │  - AI-powered domain detection                           │  │
│  │  - Creates domains automatically from content               │  │
│  └─────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Data Access Layer                            │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │  NodeRepository                                          │  │
│  │  - CRUD operations for entities                         │  │
│  │  - Vector similarity search                               │  │
│  └─────────────────────────────────────────────────────────┘  │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │  EdgeRepository                                          │  │
│  │  - CRUD operations for relationships                    │  │
│  └─────────────────────────────────────────────────────────┘  │
│  │  ┌─────────────────────────────────────────────────────┐  │  │
│  │  │  DomainRepository                                    │  │
│  │  │  - Domain CRUD operations                         │  │
│  │  │  - Entity/Relationship type management            │  │
│  │  └─────────────────────────────────────────────────────┘  │
│  │  ┌─────────────────────────────────────────────────────┐  │
│  │  │  CommunityRepository                                │  │
│  │  │  - Community CRUD operations                     │  │
│  │  │  - Membership management                           │  │
│  │  └─────────────────────────────────────────────────────┘  │
│  └─────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Database Layer                               │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │  PostgreSQL with pgvector extension                          │  │
│  │  - Tables: nodes, edges, communities, domains, etc.       │  │
│  │  - Vector similarity search (HNSW index)                  │  │
│  │  - Text search (trigram)                                   │  │
│  └─────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                    External Services                             │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │  Google GenAI API                                          │  │
│  │  - LLM for knowledge extraction (gemini-2.5-flash-lite)    │  │
│  │  - Embeddings for vector search (text-embedding-004)        │  │
│  └─────────────────────────────────────────────────────────┘  │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │  Local LLM Server (http://localhost:8317)               │  │
│  │  - OpenAI-compatible API                                   │  │
│  │  - Used for knowledge extraction                          │  │
│  └─────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

## Key Components

### Knowledge Pipeline Flow

```
Text Input
    │
    ▼
┌─────────────────────────────────────────┐
│  1. Domain Detection (AI-powered)       │
│     - Analyzes content                   │
│     - Creates/selects domain             │
└─────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────┐
│  2. Knowledge Extraction (2-pass)        │
│     ┌─────────────────────────────────┐ │
│     │  Pass 1: Core Extraction          │ │
│     │  - Main entities & relationships  │ │
│     └─────────────────────────────────┘ │
│     ┌─────────────────────────────────┐ │
│     │  Pass 2: Gleaning (JSON-only)    │ │
│     │  - Finds missed details         │ │
│     │  - Dates, temporal events         │ │
│     └─────────────────────────────────┘ │
└─────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────┐
│  3. Entity Resolution (Hybrid)          │
│     ┌─────────────────────────────────┐ │
│     │  Step 1: Vector Search            │ │
│     │  - Find similar entities (cosine) │ │
     │  - Threshold: 0.70                 │ │
│     └─────────────────────────────────┘ │
│     ┌─────────────────────────────────┐ │
     │  Step 2: LLM Reasoning            │ │
     │  - Decide: MERGE/LINK/KEEP       │ │
     │  - Handle name variations        │ │
     └─────────────────────────────────┘ │
│     ┌─────────────────────────────────┐ │
     │  Step 3: Insert/Update           │ │
     │  - Store with embeddings         │ │
│     └─────────────────────────────────┘ │
└─────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────┐
│  4. Community Detection                 │
│     - Hierarchical Leiden algorithm     │
│     - Paginated loading (10K nodes/page)│
│     - Creates community hierarchy        │
└─────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────┐
│  5. Recursive Summarization            │
│     - Bottom-up (level 0 → max)         │
│     - LLM-generated summaries           │
│     - Vector embeddings for search       │
└─────────────────────────────────────────┘
```

### Data Flow

1. **Ingestion**
   - Text → GraphIngestor (extraction)
   - KnowledgeGraph → EntityResolver (deduplication)
   - Entities/Edges → NodeRepository/EdgeRepository (storage)

2. **Community Detection**
   - Database → CommunityDetector.load_graph() (paginated)
   - Graph → Leiden algorithm
   - Communities → CommunityRepository (storage)

3. **Querying**
   - Query → Search endpoint
   - PostgreSQL → Vector search (HNSW) + Text search (trigram)
   - Results → API response

## Technology Stack

- **Language:** Python 3.12+
- **Web Framework:** FastAPI
- **Database:** PostgreSQL 15+ with pgvector extension
- **Vector Search:** HNSW index on embeddings (768-dim)
- **Graph Algorithm:** graspologic (Hierarchical Leiden)
- **LLM:** Google GenAI (gemini-2.5-flash-lite) + Local OpenAI-compatible server
- **Embeddings:** Google GenAI (text-embedding-004)
- **Testing:** pytest, pytest-asyncio, pytest-cov
- **Linting:** ruff, mypy
- **Logging:** structlog (JSON format)
- **API Documentation:** OpenAPI (auto-generated by FastAPI)

## Configuration

All configuration is managed via environment variables and Pydantic models:

- `GOOGLE_API_KEY` - Google GenAI API key
- `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASSWORD` - Database connection
- `LLM_MODEL` - LLM model name
- `EMBEDDING_BATCH_SIZE` - Batch size for embeddings (default: 50)
- `SUMMARIZATION_BATCH_SIZE` - Batch size for summarization (default: 5)
- `GRAPH_PAGE_SIZE` - Page size for graph loading (default: 10000)

## Error Handling

Custom exception hierarchy with structured error responses:

```
KnowledgeBaseError (base)
├── DatabaseError
├── LLMError
├── IngestionError
├── ResolutionError
├── ValidationError
├── ConfigurationError
├── CommunityDetectionError
├── SummarizationError
└── DomainError
```

All errors include:
- `error_type`: Error class name
- `message`: Human-readable message
- `details`: Additional context
- `request_id`: UUID for tracking

## Performance Optimizations

1. **Batch Processing**
   - Embeddings: 50 entities per batch (10x faster)
   - Summarization: 5 communities per batch (5x faster)
   - Configurable via environment variables

2. **Paginated Loading**
   - Graph loading: 10,000 nodes/edges per page
   - Reduces memory usage for large graphs

3. **Vector Search**
   - HNSW index for fast similarity search
   - Cosine distance metric
   - Threshold-based filtering

4. **Caching**
   - Domain schemas cached
   - Repository instances reused (singleton pattern)

## Security Considerations

- SQL injection prevention: Parameterized queries
- Input validation: Pydantic models for all inputs
- CORS: Configurable allowed origins
- Environment variables: Secrets not in code
- Request IDs: For tracking and debugging

## Scalability

- Horizontal scaling: Stateless API (except singleton caches)
- Database: Connection pooling (psycopg pool)
- Async I/O: All database operations are async
- Batch processing: Reduces API calls to LLM services
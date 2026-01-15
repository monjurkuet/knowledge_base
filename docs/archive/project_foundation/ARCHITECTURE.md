# Architecture
## Multi-Domain Knowledge Base GraphRAG System

## System Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          Multi-Domain Knowledge Base                         │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │                        Streamlit UI Layer                             │   │
│  │  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐    │   │
│  │  │  Domain     │ │  Ingestion  │ │   Graph     │ │  Analysis   │    │   │
│  │  │  Switcher   │ │    Panel    │ │  Explorer   │ │  Dashboard  │    │   │
│  │  └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘    │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                                    │                                        │
│                                    ▼                                        │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │                          API Gateway (FastAPI)                        │   │
│  │  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐    │   │
│  │  │   Domain    │ │  Ingestion  │ │   Graph     │ │  Analysis   │    │   │
│  │  │  Management │ │   Endpoints │ │  Endpoints  │ │  Endpoints  │    │   │
│  │  └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘    │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                                    │                                        │
│                                    ▼                                        │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │                      GraphRAG Processing Layer                         │   │
│  │                                                                        │   │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  │   │
│  │  │  Ingestion  │  │  Extraction │  │  Resolution │  │  Community  │  │   │
│  │  │   Pipeline  │──▶│   Engine    │──▶│   Engine    │──▶│  Detection  │  │   │
│  │  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘  │   │
│  │       │                  │                  │                  │      │   │
│  │       ▼                  ▼                  ▼                  ▼      │   │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  │   │
│  │  │    File     │  │   LLM       │  │   Vector    │  │   Leiden    │  │   │
│  │  │  Processor  │  │  Extractor  │  │  Matching   │  │  Clustering │  │   │
│  │  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘  │   │
│  │                                                                        │   │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  │   │
│  │  │Summarization│  │  Cross-     │  │   Insight   │  │   Template  │  │   │
│  │  │   Engine    │◀─│   Domain    │◀─│  Generator  │◀─│   Engine    │  │   │
│  │  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘  │   │
│  │                                                                        │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                                    │                                        │
│                                    ▼                                        │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │                       PostgreSQL Database Layer                        │   │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  │   │
│  │  │   Nodes     │  │   Edges     │  │  Domains    │  │  Templates  │  │   │
│  │  │  (Vector)   │  │ (Graph)     │  │  (Schema)   │  │  (Config)   │  │   │
│  │  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘  │   │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  │   │
│  │  │  Events     │  │Communities  │  │ Cross-Domain│  │   Indexes   │  │   │
│ History │  │ ()   │  │ (Hierarchy) │  │   Links     │  │   (HNSW)    │  │   │
│  │  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘  │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │                          External Services                            │   │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  │   │
│  │  │  Google     │  │  Embedding  │  │  File       │  │  Streaming  │  │   │
│  │  │  Gemini     │  │  Service    │  │  Storage    │  │  WebSocket  │  │   │
│  │  │  (LLM)      │  │  (768-dim)  │  │  (Local)    │  │  (Real-time)│  │   │
│  │  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘  │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Component Details

### 1. UI Layer (Streamlit)

#### Component Architecture

```
Streamlit UI
├── Sidebar
│   ├── Domain Switcher (dropdown)
│   ├── Navigation (tabs)
│   └── Settings (gear icon)
├── Main Content Area
│   ├── Ingestion Panel
│   │   ├── File Uploader (drag & drop)
│   │   ├── Manual Input (text area)
│   │   ├── Processing Controls
│   │   └── Progress Indicator
│   ├── Graph Explorer
│   │   ├── Network Visualization (pyvis/d3)
│   │   ├── Entity Search
│   │   ├── Filter Panel
│   │   └── Detail View (expandable)
│   ├── Analysis Dashboard
│   │   ├── Community Overview
│   │   ├── Trend Analysis
│   │   ├── Performance Metrics
│   │   └── Insight Feed
│   └── Cross-Domain View
│       ├── Domain Comparison
│       ├── Connection Map
│       └── Pattern Discovery
└── Status Bar
    ├── Processing Status
    ├── Last Updated
    └── Quick Actions
```

#### Key Features
- **Domain Switcher**: Seamless switching between domains
- **Real-time Updates**: WebSocket integration for live progress
- **Interactive Graph**: Zoom, pan, node highlighting
- **Search & Filter**: Full-text and semantic search
- **Export Options**: CSV, JSON, visualization export

---

### 2. API Layer (FastAPI)

#### Endpoint Organization

```
/api/v1/
├── domains/
│   ├── GET /domains/                      # List all domains
│   ├── POST /domains/                     # Create new domain
│   ├── GET /domains/{id}                  # Get domain details
│   ├── PUT /domains/{id}                  # Update domain
│   ├── DELETE /domains/{id}               # Delete domain
│   ├── POST /domains/{id}/activate        # Activate domain
│   └── POST /domains/{id}/deactivate      # Deactivate domain
│
├── ingestion/
│   ├── POST /ingest/file                  # Ingest file
│   ├── POST /ingest/text                  # Ingest text
│   ├── GET /ingest/status/{job_id}        # Get job status
│   ├── GET /ingest/history                # Get ingestion history
│   └── DELETE /ingest/job/{job_id}        # Cancel/delete job
│
├── graph/
│   ├── GET /graph/nodes                   # List nodes (with filters)
│   ├── GET /graph/nodes/{id}              # Get node details
│   ├── GET /graph/edges                   # List edges
│   ├── GET /graph/edges/{id}              # Get edge details
│   ├── GET /graph/search                  # Semantic search
│   ├── GET /graph/similar/{node_id}       # Find similar nodes
│   ├── GET /graph/path/{source}/{target}  # Find path
│   └── GET /graph/export                  # Export graph data
│
├── entities/
│   ├── GET /entities/                     # List entities
│   ├── GET /entities/{id}                 # Get entity details
│   ├── PUT /entities/{id}                 # Update entity
│   ├── POST /entities/{id}/merge          # Merge entities
│   └── POST /entities/{id}/split          # Split entity
│
├── communities/
│   ├── GET /communities/                  # List communities
│   ├── GET /communities/{id}              # Get community details
│   ├── GET /communities/{id}/members      # Get community members
│   ├── GET /communities/{id}/summary      # Get community summary
│   └── GET /communities/{id}/hierarchy    # Get community hierarchy
│
├── analysis/
│   ├── GET /analysis/trends               # Get trend analysis
│   ├── GET /analysis/gaps                 # Identify knowledge gaps
│   ├── GET /analysis/insights             # Get generated insights
│   └── POST /analysis/run                 # Run analysis
│
├── cross-domain/
│   ├── GET /cross-domain/links            # List cross-domain links
│   ├── GET /cross-domain/links/{id}       # Get link details
│   ├── PUT /cross-domain/links/{id}       # Update link
│   ├── POST /cross-domain/verify          # Verify link
│   └── POST /cross-domain/discover        # Discover new links
│
├── templates/
│   ├── GET /templates/                    # List templates
│   ├── GET /templates/{id}                # Get template
│   ├── POST /templates/                   # Create template
│   ├── PUT /templates/{id}                # Update template
│   └── POST /templates/apply/{domain_id}  # Apply template
│
└── health/
    ├── GET /health                        # Health check
    └── GET /health/ready                  # Readiness check
```

#### Request/Response Models

```python
# Example: Create Domain
class DomainCreate(BaseModel):
    name: str = Field(..., min_length=3, max_length=100)
    display_name: str = Field(..., min_length=3, max_length=200)
    description: Optional[str] = None
    template_config: Optional[Dict[str, Any]] = None

class DomainResponse(BaseModel):
    id: UUID
    name: str
    display_name: str
    description: Optional[str]
    is_active: bool
    node_count: int
    edge_count: int
    created_at: datetime
    updated_at: datetime

# Example: Ingest File
class IngestFileRequest(BaseModel):
    domain_id: UUID
    file_path: str
    metadata: Optional[Dict[str, Any]] = None
    auto_categorize: bool = True

class IngestFileResponse(BaseModel):
    job_id: UUID
    status: str
    estimated_time: int  # seconds
    message: str
```

---

### 3. Processing Layer (GraphRAG)

#### Ingestion Pipeline

```
Input: File/Text
    │
    ▼
┌─────────────────┐
│  File Processor │  Extract text from txt, pdf, md
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Preprocessor    │  Clean, normalize, chunk text
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ LLM Extractor   │  Extract entities + relationships
│  (Gemini)       │  using domain-specific prompts
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Post-Processor  │  Parse LLM output, validate
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Vector Store    │  Generate embeddings for entities
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Resolver        │  Entity resolution & deduplication
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Graph Builder   │  Create nodes and edges
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Community       │  Leiden clustering, hierarchy
│ Detection       │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Summarizer      │  Generate community summaries
└────────┬────────┘
         │
         ▼
Output: Knowledge Graph in DB
```

#### Entity Resolution Flow

```
Raw Entities from LLM
        │
        ▼
┌─────────────────┐
│ Vector Search   │  Find similar existing entities
│ (Cosine Sim)    │  threshold > 0.85
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ LLM Reasoner    │  Decide: MERGE / LINK / KEEP_SEPARATE
│ (Gemini)        │  Provide context + candidates
└────────┬────────┘
         │
         ▼
    ┌────┴────┐
    │         │
    ▼         ▼
┌───────┐  ┌───────────┐
│ MERGE │  │ KEEP_SEP  │
│ (same │  │ (different│
│ entity)│  │ entities) │
└───────┘  └───────────┘
    │
    ▼
┌─────────────────┐
│ Graph Update    │  Create/update nodes & edges
└─────────────────┘
```

---

### 4. Database Schema

#### Core Tables

```sql
-- Domains: Multi-domain support
CREATE TABLE domains (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) UNIQUE NOT NULL,
    display_name VARCHAR(255) NOT NULL,
    description TEXT,
    template_config JSONB NOT NULL DEFAULT '{}',
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Entity Types: Domain-specific types
CREATE TABLE domain_entity_types (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    domain_id UUID REFERENCES domains(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    display_name VARCHAR(255) NOT NULL,
    description TEXT,
    icon VARCHAR(100),
    color VARCHAR(20),
    validation_rules JSONB DEFAULT '{}',
    extraction_prompt TEXT,
    UNIQUE(domain_id, name)
);

-- Relationship Types: Domain-specific relationships
CREATE TABLE domain_relationship_types (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    domain_id UUID REFERENCES domains(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    display_name VARCHAR(255) NOT NULL,
    description TEXT,
    source_entity_type VARCHAR(255),
    target_entity_type VARCHAR(255),
    is_directional BOOLEAN DEFAULT TRUE,
    validation_rules JSONB DEFAULT '{}',
    extraction_prompt TEXT,
    UNIQUE(domain_id, name)
);

-- Nodes: Knowledge graph entities
CREATE TABLE nodes (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(500) NOT NULL,
    description TEXT,
    entity_type VARCHAR(255) NOT NULL,
    domain_id UUID REFERENCES domains(id) ON DELETE CASCADE,
    domain_entity_type_id UUID REFERENCES domain_entity_types(id),
    embedding VECTOR(768),
    domain_attributes JSONB DEFAULT '{}',
    metadata JSONB DEFAULT '{}',
    confidence FLOAT DEFAULT 1.0,
    source_document_ids UUID[],
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Edges: Knowledge graph relationships
CREATE TABLE edges (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    source_node_id UUID REFERENCES nodes(id) ON DELETE CASCADE,
    target_node_id UUID REFERENCES nodes(id) ON DELETE CASCADE,
    relationship_type VARCHAR(255) NOT NULL,
    domain_id UUID REFERENCES domains(id) ON DELETE CASCADE,
    domain_relationship_type_id UUID REFERENCES domain_relationship_types(id),
    embedding VECTOR(768),
    domain_attributes JSONB DEFAULT '{}',
    metadata JSONB DEFAULT '{}',
    confidence FLOAT DEFAULT 1.0,
    weight FLOAT DEFAULT 1.0,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(source_node_id, target_node_id, relationship_type)
);

-- Cross-Domain Links
CREATE TABLE cross_domain_links (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    source_node_id UUID REFERENCES nodes(id) ON DELETE CASCADE,
    target_node_id UUID REFERENCES nodes(id) ON DELETE CASCADE,
    source_domain_id UUID REFERENCES domains(id),
    target_domain_id UUID REFERENCES domains(id),
    link_type VARCHAR(255) NOT NULL,
    confidence FLOAT DEFAULT 0.8,
    verified BOOLEAN DEFAULT FALSE,
    verification_method VARCHAR(50),
    created_at TIMESTAMP DEFAULT NOW()
);
```

#### Indexes

```sql
-- Domain queries
CREATE INDEX idx_nodes_domain ON nodes(domain_id);
CREATE INDEX idx_edges_domain ON edges(domain_id);
CREATE INDEX idx_cross_links_source_domain ON cross_domain_links(source_domain_id);
CREATE INDEX idx_cross_links_target_domain ON cross_domain_links(target_domain_id);

-- Type queries
CREATE INDEX idx_nodes_entity_type ON nodes(entity_type);
CREATE INDEX idx_edges_relationship_type ON edges(relationship_type);

-- Vector similarity
CREATE INDEX idx_nodes_embedding ON nodes USING hnsw(embedding vector_cosine_ops);

-- Source document queries
CREATE INDEX idx_nodes_source_docs ON nodes USING gin(source_document_ids);

-- Text search
CREATE INDEX idx_nodes_name ON nodes USING gin(to_tsvector('english', name));
```

---

### 5. External Services

#### Google Gemini Integration

```python
class GeminiClient:
    def __init__(self, api_key: str, model: str = "gemini-2.5-flash"):
        self.client = genai.Client(api_key=api_key)
        self.model = model

    async def extract_entities(
        self,
        text: str,
        domain_config: DomainConfig
    ) -> ExtractionResult:
        prompt = self._build_extraction_prompt(text, domain_config)
        response = await self.client.aio.models.generate_content(
            model=self.model,
            contents=[prompt],
            config=types.GenerateContentConfig(
                temperature=0.1,
                max_output_tokens=8192,
            )
        )
        return self._parse_response(response)

    async def generate_embedding(self, text: str) -> List[float]:
        response = await self.client.aio.models.embed_content(
            model="text-embedding-004",
            contents=[text],
            config=types.EmbedContentConfig(task_type="SEMANTIC_SIMILARITY")
        )
        return response.values[0]
```

#### WebSocket for Real-time Updates

```python
class WebSocketManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}

    async def connect(self, websocket: WebSocket, client_id: str):
        await websocket.accept()
        self.active_connections[client_id] = websocket

    async def disconnect(self, client_id: str):
        del self.active_connections[client_id]

    async def send_progress(self, client_id: str, progress: ProgressUpdate):
        if client_id in self.active_connections:
            await self.active_connections[client_id].send_json(progress.dict())
```

---

## Data Flow Diagrams

### Ingestion Data Flow

```
User Interface                          Backend                          Database
    │                                      │                                 │
    │ 1. Upload File                       │                                 │
    ├─────────────────────────────────────▶│                                 │
    │                                      │ 2. Save to temp storage         │
    │                                      ├───────────────────────────────▶│
    │                                      │                                 │
    │                                      │ 3. Extract text                │
    │                                      │◀────────────────────────────────┤
    │                                      │                                 │
    │                                      │ 4. Generate chunks             │
    │                                      ├────────┐                        │
    │                                      │        │                        │
    │                                      │◀───────┘                        │
    │                                      │                                 │
    │                                      │ 5. Extract entities (LLM)      │
    │                                      │◀────────────────────────────────┤
    │                                      │                                 │
    │                                      │ 6. Generate embeddings         │
    │                                      │◀────────────────────────────────┤
    │                                      │                                 │
    │                                      │ 7. Resolve entities            │
    │                                      ├───────────────────────────────▶│
    │                                      │                                 │
    │                                      │ 8. Build graph                 │
    │                                      ├───────────────────────────────▶│
    │                                      │                                 │
    │                                      │ 9. Detect communities         │
    │                                      ├───────────────────────────────▶│
    │                                      │                                 │
    │                                      │10. Generate summaries          │
    │                                      ├───────────────────────────────▶│
    │                                      │                                 │
    │ 11. Return Result                    │                                 │
    │◀─────────────────────────────────────│                                 │
```

### Query Data Flow

```
User Interface                          Backend                          Database
    │                                      │                                 │
    │ 1. Search Query                      │                                 │
    ├─────────────────────────────────────▶│                                 │
    │                                      │ 2. Vector search               │
    │                                      ├───────────────────────────────▶│
    │                                      │                                 │
    │                                      │ 3. Get entities                │
    │                                      ├───────────────────────────────▶│
    │                                      │                                 │
    │                                      │ 4. Get relationships           │
    │                                      ├───────────────────────────────▶│
    │                                      │                                 │
    │                                      │ 5. Get communities             │
    │                                      ├───────────────────────────────▶│
    │                                      │                                 │
    │                                      │ 6. Generate insight (LLM)      │
    │                                      │◀────────────────────────────────┤
    │                                      │                                 │
    │ 7. Return Results                    │                                 │
    │◀─────────────────────────────────────│                                 │
```

# Knowledge Base GraphRAG System - Codebase Architecture

## 📁 **Project Structure Overview**

```
knowledge_base/
├── 📄 Core Application Files
├── 🔧 Configuration & Setup
├── 🌐 API Layer
├── 🎨 User Interface
├── 🧪 Testing
├── 📚 Documentation
└── 🗄️ Database
```

---

## 📂 **Detailed Folder Structure**

### **Root Directory (`/`)**
```
knowledge_base/
├── 📁 __pycache__/           # Python bytecode cache (auto-generated)
├── 📁 .ruff_cache/           # Linting cache (auto-generated)
├── 📁 streamlit-ui/          # Web interface application
├── 📁 tests/                 # Testing suite and data
│
├── 📄 Core Python Files:
│   ├── config.py            # Configuration management system
│   ├── pipeline.py          # Main document processing orchestrator
│   ├── ingestor.py          # LLM-powered entity extraction engine
│   ├── resolver.py          # Entity deduplication and resolution
│   ├── community.py         # Hierarchical community detection
│   ├── summarizer.py        # Recursive summarization system
│   ├── visualize.py         # CLI visualization tools
│   ├── api.py               # FastAPI REST endpoints
│   ├── websocket.py         # Real-time communication system
│   └── main_api.py          # API server entry point
│
├── 🔧 Configuration Files:
│   ├── requirements.txt     # Python dependencies
│   ├── .env                 # Environment variables (local)
│   ├── .env.template        # Environment configuration template
│   └── schema.sql           # PostgreSQL database schema
│
└── 📚 Documentation:
    ├── README.md            # Project overview and quick start
    └── docs/                # Documentation directory
        ├── API_DOCUMENTATION.md # Complete API reference
        ├── DEPLOYMENT_GUIDE.md  # Production deployment instructions
        ├── DESIGN.md            # Architecture design decisions
        └── PRODUCTION_READINESS_SUMMARY.md # Production readiness report
```

---

## 🔍 **Core Components Deep Dive**

### **1. Configuration Layer**

#### **`config.py`** - Configuration Management System
```python
# Purpose: Centralized configuration with environment variable support
# Key Features:
# - Pydantic-based type-safe configuration
# - Environment variable integration
# - Validation and defaults
# - Modular config sections (Database, LLM, API, UI, Logging)

class Config:
    database: DatabaseConfig
    llm: LLMConfig
    api: APIConfig
    streamlit: StreamlitConfig
    logging: LoggingConfig
```

**Responsibilities:**
- Load and validate environment variables
- Provide typed configuration objects
- Support different deployment environments
- Centralize all system settings

---

### **2. Processing Pipeline Layer**

#### **`pipeline.py`** - Document Processing Orchestrator
```python
class KnowledgePipeline:
    def __init__(self):
        # Initializes: ingestor, resolver, community_detector

    async def run(self, file_path: str):
        # 1. Extract entities and relationships
        # 2. Resolve and deduplicate entities
        # 3. Store in database
        # 4. Detect communities
        # 5. Generate summaries
```

**Responsibilities:**
- Coordinate the entire document processing workflow
- Manage component initialization and lifecycle
- Handle file I/O and temporary file management
- Orchestrate the 4-stage pipeline (Extract → Resolve → Cluster → Summarize)

#### **`ingestor.py`** - LLM-Powered Extraction Engine
```python
class GraphIngestor:
    def __init__(self, model_name: str):
        # Instructor-based structured output
        # Google Gemini integration

    async def extract(self, text: str) -> KnowledgeGraph:
        # Two-pass extraction strategy
        # Pass 1: Primary entities and relationships
        # Pass 2: Gleaning (missed connections)
        # Return structured KnowledgeGraph
```

**Responsibilities:**
- Interface with LLM APIs (Google Gemini)
- Implement structured output parsing with Instructor
- Perform multi-pass extraction for completeness
- Generate embeddings for semantic similarity

#### **`resolver.py`** - Entity Resolution System
```python
class EntityResolver:
    def __init__(self, db_conn_str: str, model_name: str):
        # Vector similarity search
        # LLM-based cognitive reasoning

    async def resolve_and_insert(self, entity_dict, embedding):
        # Find similar existing entities
        # LLM judge for merge/link/keep decisions
        # Insert or update with resolved IDs
```

**Responsibilities:**
- Prevent entity duplication across documents
- Vector similarity search for candidate matching
- LLM-powered merge/link decision making
- Maintain canonical entity database

#### **`community.py`** - Graph Clustering Engine
```python
class CommunityDetector:
    def __init__(self, db_conn_str: str):
        # NetworkX graph construction
        # Hierarchical Leiden algorithm

    async def load_graph(self) -> nx.Graph:
        # Load entities and relationships from DB
        # Construct NetworkX graph object

    def detect_communities(self, G: nx.Graph):
        # Apply hierarchical Leiden clustering
        # Return community membership assignments
```

**Responsibilities:**
- Load knowledge graph from database
- Apply hierarchical community detection
- Store community memberships
- Support different resolution levels

#### **`summarizer.py`** - Hierarchical Summarization
```python
class CommunitySummarizer:
    def __init__(self, db_conn_str: str, model_name: str):
        # Recursive summarization logic
        # LLM-powered content generation

    async def summarize_all(self):
        # Generate leaf summaries (Level 1 communities)
        # Create parent summaries (Level 2+ communities)
        # Build hierarchical intelligence map
```

**Responsibilities:**
- Generate community intelligence reports
- Implement recursive summarization (child → parent)
- Create searchable summary embeddings
- Maintain hierarchical summary relationships

---

### **3. API Layer**

#### **`api.py`** - REST API Endpoints
```python
# FastAPI application with endpoints:
# GET  /api/stats              # Database statistics
# GET  /api/nodes              # Entity nodes with filtering
# GET  /api/edges              # Relationships
# GET  /api/communities        # Community information
# POST /api/search             # Text search with embeddings
# GET  /api/graph              # Graph data for visualization
# POST /api/ingest/text        # Text content ingestion
# POST /api/ingest/file        # File upload ingestion
# POST /api/community/detect   # Trigger community detection
# POST /api/summarize          # Trigger summarization
```

**Responsibilities:**
- Provide RESTful API for all system operations
- Handle request validation and response formatting
- Manage database connections and queries
- Implement proper error handling and HTTP status codes

#### **`websocket.py`** - Real-Time Communication
```python
class ConnectionManager:
    # WebSocket connection management
    # Message broadcasting to channels
    # Progress tracking for long operations

class ProgressTracker:
    # Track operation progress
    # Send real-time updates
    # Handle operation lifecycle
```

**Responsibilities:**
- Manage WebSocket connections and channels
- Provide real-time progress updates
- Broadcast operation status to clients
- Handle connection lifecycle and cleanup

#### **`main_api.py`** - API Server Entry Point
```python
def main():
    # Configure logging
    # Initialize FastAPI app
    # Add WebSocket routes
    # Start uvicorn server with configuration
```

**Responsibilities:**
- Bootstrap the API server
- Configure logging and middleware
- Handle server lifecycle
- Provide command-line interface

---

### **4. User Interface Layer**

#### **`streamlit-ui/app.py`** - Web Application
```python
def main():
    # Dashboard with statistics
    # Search interface with filters
    # Document ingestion forms
    # Interactive graph visualization
    # Community analysis views
    # Real-time operation feedback
```

**Key Components:**
- **Dashboard Tab**: Database statistics and operations
- **Search Tab**: Full-text and semantic search
- **Ingest Tab**: Text input and file upload
- **Graph Tab**: Interactive network visualization
- **Communities Tab**: Hierarchical community exploration

**Responsibilities:**
- Provide user-friendly web interface
- Connect to API backend for all operations
- Handle real-time updates via WebSocket
- Implement responsive data visualization

---

### **5. Testing & Data Layer**

#### **`tests/master_test.py`** - Integration Testing
```python
# Comprehensive test suite covering:
# - Document ingestion pipeline
# - Entity extraction accuracy
# - Community detection quality
# - Search functionality
# - API endpoint validation
```

#### **`tests/data/`** - Test Datasets
```
doc_1_history.txt    # Historical document for testing
doc_2_conflict.txt   # Conflict scenario document
doc_3_impact.txt     # Impact analysis document
```

#### **`schema.sql`** - Database Schema
```sql
-- PostgreSQL schema with:
-- Tables: nodes, edges, communities, community_membership, events
-- Indexes: Vector (HNSW), Text (GIN), Graph traversal
-- Extensions: vector, pg_trgm, uuid-ossp
-- Constraints and foreign keys
```

---

## 🔄 **Data Flow Architecture**

### **Document Processing Pipeline**
```
Text Document
    ↓
Ingestor (LLM Extraction)
    ↓
Resolver (Deduplication)
    ↓
Database Storage
    ↓
Community Detector
    ↓
Summarizer (Hierarchical)
    ↓
API Endpoints
    ↓
Web Interface
```

### **Search & Query Flow**
```
User Query
    ↓
API Endpoint (/api/search)
    ↓
Vector Similarity Search
    ↓
LLM Reranking (Optional)
    ↓
Result Formatting
    ↓
Web Interface Display
```

### **Real-Time Updates Flow**
```
Long Operation Start
    ↓
ProgressTracker Created
    ↓
WebSocket Broadcasts
    ↓
UI Updates in Real-Time
    ↓
Operation Completion
```

---

## 🗂️ **File Dependencies Map**

### **Core Dependencies**
```
config.py
├── Used by: All Python files
└── Provides: Configuration management

pipeline.py
├── Depends on: config.py, ingestor.py, resolver.py, community.py
├── Used by: api.py
└── Purpose: Orchestrates document processing

ingestor.py
├── Depends on: config.py
├── Used by: pipeline.py
└── Purpose: LLM-powered extraction

resolver.py
├── Depends on: config.py
├── Used by: pipeline.py
└── Purpose: Entity deduplication

community.py
├── Depends on: config.py
├── Used by: pipeline.py
└── Purpose: Graph clustering

summarizer.py
├── Depends on: config.py
├── Used by: pipeline.py
└── Purpose: Hierarchical summarization
```

### **API Layer Dependencies**
```
api.py
├── Depends on: config.py, pipeline.py, websocket.py
├── Uses: All core components via lazy getters
└── Purpose: REST API endpoints

websocket.py
├── Depends on: None (standalone)
├── Used by: api.py, main_api.py
└── Purpose: Real-time communication

main_api.py
├── Depends on: api.py, websocket.py, config.py
├── Uses: uvicorn for server
└── Purpose: Server bootstrap
```

### **UI Dependencies**
```
streamlit-ui/app.py
├── Depends on: requests, plotly, networkx
├── Connects to: API server
└── Purpose: Web interface
```

---

## 🔧 **Configuration & Environment**

### **Environment Variables** (`.env`)
```bash
# Database
DB_USER=knowledge_base_user
DB_PASSWORD=secure_password
DB_HOST=localhost
DB_PORT=5432
DB_NAME=knowledge_base

# LLM
GOOGLE_API_KEY=your_api_key
LLM_MODEL=gemini-2.5-flash

# API Server
API_HOST=0.0.0.0
API_PORT=8000
CORS_ORIGINS=http://localhost:3000,http://localhost:8501

# UI
STREAMLIT_API_URL=http://localhost:8000
STREAMLIT_WS_URL=ws://localhost:8000/ws

# Logging
LOG_LEVEL=INFO
```

### **Configuration Classes** (`config.py`)
- `DatabaseConfig`: PostgreSQL connection settings
- `LLMConfig`: AI model and API configuration
- `APIConfig`: Server and CORS settings
- `StreamlitConfig`: UI connection settings
- `LoggingConfig`: Logging preferences

---

## 🚀 **Deployment Architecture**

### **Development Setup**
```
Local Machine
├── Python 3.10+
├── PostgreSQL 13+
├── API Server (main_api.py)
├── Streamlit UI (streamlit-ui/app.py)
└── Environment (.env)
```

### **Production Setup**
```
Production Server
├── Systemd Services
│   ├── knowledge-base-api.service
│   └── knowledge-base-ui.service
├── PostgreSQL Database
├── Nginx Reverse Proxy (Optional)
├── SSL Certificates
└── Monitoring (Logs, Metrics)
```

### **Container Setup**
```
Docker Compose
├── api-service (FastAPI + Gunicorn)
├── ui-service (Streamlit)
├── db-service (PostgreSQL)
└── Shared volumes and networks
```

---

## 📊 **Database Schema Overview**

### **Core Tables**
- **`nodes`**: Entities with types, descriptions, embeddings
- **`edges`**: Relationships between entities with weights
- **`communities`**: Hierarchical clusters with summaries
- **`community_membership`**: Node-to-community mappings
- **`events`**: Temporal events linked to entities

### **Indexes & Performance**
- **Vector Indexes**: HNSW for embedding similarity search
- **Text Indexes**: GIN for full-text search
- **Graph Indexes**: B-tree for relationship traversal
- **Composite Indexes**: Optimized query patterns

---

## 🔐 **Security Architecture**

### **Authentication & Authorization**
- Environment-based API keys
- Configurable CORS policies
- Input validation with Pydantic
- SQL injection prevention

### **Data Protection**
- Encrypted database connections (optional)
- Secure environment variable handling
- Sanitized error messages
- Audit logging capabilities

---

## 📈 **Scalability Considerations**

### **Horizontal Scaling**
- Stateless API design
- Database connection pooling
- Redis for session management (future)
- Load balancer ready

### **Vertical Scaling**
- Asynchronous processing
- Batch operations support
- Memory-efficient data structures
- Configurable resource limits

### **Performance Optimizations**
- Lazy component loading
- Connection pooling
- Query result caching (future)
- Background job processing

---

## 🧪 **Testing Strategy**

### **Unit Tests** (`tests/`)
- Component isolation testing
- Mock external dependencies
- Edge case validation

### **Integration Tests**
- Full pipeline testing
- API endpoint validation
- Database operation verification

### **Performance Tests**
- Load testing scenarios
- Memory usage monitoring
- Query performance benchmarks

---

## 🔄 **Development Workflow**

### **Local Development**
```bash
# Setup
pip install -r requirements.txt
cp .env.template .env
# Configure .env

# Database
createdb knowledge_base
psql -d knowledge_base -f schema.sql

# Development servers
python main_api.py              # Terminal 1
cd streamlit-ui && streamlit run app.py  # Terminal 2
```

### **Code Organization Principles**
- **Separation of Concerns**: Each file has a single responsibility
- **Dependency Injection**: Configuration passed through constructors
- **Error Handling**: Comprehensive exception management
- **Type Safety**: Full type annotations and validation
- **Documentation**: Inline documentation and docstrings

---

## 🎯 **Key Design Patterns**

### **Factory Pattern**
- Lazy initialization of heavy components
- Configuration-based object creation
- Dependency injection through getters

### **Repository Pattern**
- Database operations abstracted
- Consistent data access interface
- Testable data layer

### **Observer Pattern**
- WebSocket-based real-time updates
- Progress tracking for long operations
- Event-driven UI updates

### **Strategy Pattern**
- Pluggable LLM providers
- Configurable community detection algorithms
- Extensible summarization strategies

---

*This document provides a comprehensive view of the Knowledge Base GraphRAG system's architecture, file organization, and component interactions. Each Python file is designed with clear responsibilities and follows enterprise development practices.*
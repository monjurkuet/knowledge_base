# Knowledge Base GraphRAG System

This directory contains the high-fidelity **Agentic GraphRAG** ingestion and management system. It extends standard RAG by adding structured relationships, hierarchical community summaries, and chronological timelines. The system provides both a REST API and web interface for knowledge graph exploration and management.

## 🎨 **New Modern UI - Bun + SolidJS + Sigma.js**

The system now features a **modern, high-performance web interface** built with:
- **Bun 1.1+** - Ultra-fast JavaScript runtime (4-7x faster than Node.js)
- **SolidJS 1.8+** - Reactive UI framework (85% smaller bundles than React)
- **Sigma.js 2.0+** - WebGL-powered graph visualization (handles 10,000+ nodes)
- **WebSocket Support** - Real-time updates and live ingestion logs

## ✅ **API Migration Completed - Now Using Real OpenAI-Compatible API**

This system now uses **real OpenAI-compatible API calls** instead of mocks, pointing to `http://localhost:8317/v1` with no API key required.

### 🔧 **What Changed:**
- **Mock Calls Replaced**: All instructor-based LLM calls replaced with direct HTTP requests
- **New HTTP Client**: Created `http_client.py` following reference implementation patterns  
- **Configuration Updated**: Default endpoint set to `localhost:8317/v1`
- **Tool Calling**: Full implementation for structured output using OpenAI tool calling format
- **Error Handling**: Proper retry logic with exponential backoff
- **Google Embeddings**: Preserved as requested for embedding operations

### 🌐 **API Configuration:**
```bash
# OpenAI-compatible API
OPENAI_API_BASE=http://localhost:8317/v1
LLM_MODEL=gemini-2.5-flash-lite

# Google API (for embeddings)
GOOGLE_API_KEY=your_google_api_key_here
```

## Features

- **High-Resolution Extraction:** Uses a 2-pass "gleaning" strategy with Google Gemini models to capture subtle entities and relationships.
- **Hybrid Entity Resolution:** Combines vector similarity with LLM-based cognitive reasoning to deduplicate nodes (e.g., merging "Dr. Vance" and "Elena Vance").
- **Hierarchical Clustering:** Uses the **Leiden Algorithm** to cluster nodes into Micro-communities, which are then rolled up into Macro-themes.
- **Recursive Summarization:** Automatically generates "Intelligence Reports" for every community. Parent communities summarize their children, creating a searchable map of knowledge.
- **Temporal Tracking:** Extracts specific events and dates to build structured timelines.
- **REST API:** Complete FastAPI-based REST API for programmatic access.
- **Modern Web Interface:** Bun + SolidJS + Sigma.js UI with real-time graph visualization.
- **Real-time Updates:** WebSocket support for progress tracking during long operations.
- **Production Ready:** Enterprise-grade configuration, logging, and deployment options.

## Architecture

The system consists of three main layers:

### 1. Core Processing Layer
- `pipeline.py`: Main orchestrator for document ingestion and processing
- `ingestor.py`: LLM-powered entity and relationship extraction
- `resolver.py`: Entity deduplication and resolution using embeddings
- `community.py`: Hierarchical community detection using Leiden algorithm
- `summarizer.py`: Recursive summarization of communities

### 2. API Layer
- `api.py`: FastAPI endpoints for all operations
- `websocket.py`: Real-time communication for long-running tasks
- `main_api.py`: API server entry point
- `config.py`: Configuration management system

### 3. User Interface Layer
- `knowledge-base-ui/`: Modern Bun + SolidJS + Sigma.js web interface
- Interactive WebGL-powered graph visualization
- Real-time search, domain management, and content ingestion
- Live WebSocket logs for ingestion progress

### 4. Supporting Components
- `visualize.py`: CLI visualization tools
- `database/schema.sql`: Database schema and indexes
- `config.py`: Centralized configuration management
- `http_client.py`: OpenAI-compatible HTTP client following reference implementation

## Quick Start

### 1. Requirements
Ensure your `.env` file in the root directory has the following:
- `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT`, `DB_NAME`
- `GOOGLE_API_KEY` (for embeddings and LLM operations)
- `OPENAI_API_BASE` (defaults to `http://localhost:8317/v1`)
- `LLM_MODEL` (default: `gemini-2.5-flash-lite`)
- `API_HOST`, `API_PORT` (default: 0.0.0.0:8000)
- `STREAMLIT_API_URL`, `STREAMLIT_WS_URL` (for UI configuration)

### 2. Install Dependencies
```bash
# Install all dependencies
uv sync

# Install with development dependencies
uv sync --dev

# Install with Streamlit UI dependencies
uv sync --all-extras
```

### 3. Ingest Data (CLI)
```bash
uv run kb-pipeline path/to/your/data.txt
# or
uv run python -m knowledge_base.pipeline path/to/your/data.txt
```

### 4. Start the API Server
```bash
uv run kb-server
# or
uv run python -m knowledge_base.main_api
```
The API will be available at `http://localhost:8000` with documentation at `http://localhost:8000/docs`

### 5. Start the Web Interface
```bash
cd knowledge-base-ui
bun install
bun run dev
```
The web interface will be available at `http://localhost:5173`

### 6. Alternative: CLI Visualization
```bash
uv run python -m knowledge_base.visualize
```

### 7. Testing
```bash
# Run all tests
uv run pytest

# Run specific test file
uv run pytest tests/test_pipeline.py

# Run specific test function
uv run pytest tests/test_pipeline.py::test_pipeline_initialization

# Run with verbose output
uv run pytest -v

# Run with coverage
uv run pytest --cov=knowledge_base --cov-report=html
```

### 8. Code Quality
```bash
# Lint code
uv run ruff check .

# Auto-fix linting issues
uv run ruff check --fix .

# Format code
uv run ruff format .

# Check both lint and format
uv run ruff check . && uv run ruff format .
```

## API Endpoints

The system provides a REST API for programmatic access.

### Core Endpoints
- `GET /api/stats` - Get database statistics
- `GET /api/nodes` - Retrieve knowledge graph nodes
- `GET /api/edges` - Retrieve knowledge graph edges
- `GET /api/communities` - Get community information
- `GET /api/graph` - Get graph data for visualization
- `POST /api/search` - Search nodes by text query

### Ingestion Endpoints
- `POST /api/ingest/text` - Ingest text content directly
- `POST /api/ingest/file` - Upload and ingest text files

### Management Endpoints
- `POST /api/community/detect` - Run community detection
- `POST /api/summarize` - Run recursive summarization

### WebSocket Endpoints
- `WS /ws` - Real-time updates for operations
- `WS /ws/{channel}` - Channel-specific updates

## Database Schema
The system uses PostgreSQL with `pgvector`. See `schema.sql` for table definitions (`nodes`, `edges`, `communities`, `community_membership`, `community_hierarchy`, `events`).

## Web Interface

The modern Bun + SolidJS + Sigma.js web interface provides:

### Dashboard
- Real-time database statistics (nodes, edges, communities, events)
- Live updates every 5 seconds

### Graph Visualization
- WebGL-powered interactive graph (handles 10,000+ nodes)
- Multiple layout options (Circular, Random, Force Atlas)
- Node filtering by type (entities, concepts, events, relations)
- Zoom, pan, and click interactions

### Search
- Full-text search with scoring
- Type-colored results
- Direct access to entity details

### Domains
- View and manage domain schemas
- Schema field definitions
- Node and edge counts per domain

### Content Ingestion
- Direct text input with real-time processing
- Live WebSocket logs showing pipeline progress
- Connection status indicators
- Processing stage tracking

## Documentation

- **[API Documentation](docs/API.md)** - Complete API reference with endpoints, request/response formats, and examples
- **[Architecture Guide](docs/ARCHITECTURE.md)** - System architecture and component design
- **[UI Setup Guide](knowledge-base-ui/README.md)** - Bun + SolidJS UI installation and usage
- **[Environment Configuration](.env.template)** - Template for environment variables
- **[Database Schema](database/schema.sql)** - PostgreSQL schema with pgvector extensions

## Technology Stack

- **Language**: Python 3.12+
- **Package Manager**: uv (Python), bun (JavaScript)
- **Backend**: FastAPI with uvicorn
- **Database**: PostgreSQL with pgvector extension
- **LLM**: OpenAI-compatible API (http://localhost:8317/v1)
- **Embeddings**: Google text-embedding-004 model via Google Generative AI
- **Frontend**: Bun + SolidJS + Sigma.js (WebGL graph visualization)
- **Testing**: pytest with pytest-asyncio
- **Linting**: Ruff (Python), TypeScript (JavaScript)

## Code Style Guidelines

### Import Order
1. Standard library imports
2. Third-party imports
3. Local imports (from `knowledge_base.module`)

### Naming Conventions
- **Variables/Functions**: snake_case (e.g., `graph_data`, `resolve_entity`)
- **Classes**: PascalCase (e.g., `GraphIngestor`, `KnowledgePipeline`)
- **Constants**: UPPER_CASE (e.g., `MAX_RETRIES`, `DEFAULT_MODEL`)
- **Private Methods**: Leading underscore (e.g., `_get_embedding`, `_store_graph`)

### Type Hints
- **Required**: All function parameters and return types must have type hints
- **Module**: Use `typing` module for generic types (`List`, `Dict`, `Optional`, `Any`, `Tuple`)
- **Examples**:
  ```python
  async def ingest(text: str) -> KnowledgeGraph:
      pass
  entities: List[Entity] = []
  conn_str: Optional[str] = None
  ```

### Async/Await Patterns
- **Database**: Always use `psycopg.AsyncConnection` with `async with` context managers
- **HTTP**: Use `httpx.AsyncClient` for async HTTP operations
- **LLM**: Use `instructor` with `AsyncOpenAI` for async LLM calls
- **Example**:
  ```python
  async with AsyncConnection.connect(conn_str) as conn:
      async with conn.cursor() as cur:
          await cur.execute("SELECT * FROM nodes")
          async for row in cur:
              process(row)
  ```

### Pydantic Models
- **Base Classes**: Always inherit from `BaseModel` for data structures
- **Validation**: Use `Field()` for constraints and descriptions
- **Optional Fields**: Use `Optional[T] = None` for nullable fields
- **Example**:
  ```python
  class Entity(BaseModel):
      name: str = Field(..., description="Entity name.")
      type: str = Field(..., description="Entity type.")
      description: Optional[str] = None
  ```

### Logging
- **Configuration**: Load from `config.get_config()` for consistent settings
- **Format**: `%(asctime)s - %(name)s - %(levelname)s - %(message)s`
- **Levels**: INFO (normal), WARNING (recoverable), ERROR (failures)
- **Example**:
  ```python
  import logging
  from knowledge_base.config import get_config
  
  config = get_config()
  logging.basicConfig(
      level=getattr(logging, config.logging.level), 
      format=config.logging.format
  )
  logger = logging.getLogger(__name__)
  logger.info(f"Processing file: {file_path}")
  ```

### Error Handling
- **API Errors**: Raise `HTTPException` from FastAPI
- **Database Errors**: Log with `exc_info=True` for full traceback
- **LLM Errors**: Retry with exponential backoff, log failures
- **Example**:
  ```python
  try:
      result = await risky_operation()
  except Exception as e:
      logging.error(f"Operation failed: {e}", exc_info=True)
      raise HTTPException(status_code=500, detail="Internal server error")
  ```

### String Formatting
- **Preferred**: F-strings for all interpolation (e.g., `f"Error: {error}"`)
- **Avoid**: `.format()` and `%` formatting
- **Example**:
  ```python
  name = "Alice"
  count = 5
  print(f"User {name} has {count} messages")  # Good
  print("User {} has {} messages".format(name, count))  # Bad
  ```

## Database Configuration
- **Host**: localhost
- **User**: agentzero
- **Database**: knowledge_base
- **Connection String**: `postgresql://{user}:{password}@{host}:{port}/{name}`
- **Extensions**: pgvector, pg_trgm, uuid-ossp
- **Tables**: nodes, edges, communities, community_membership, community_hierarchy, events
- **Always Use**: `psycopg.AsyncConnection` for async database operations

## Testing Strategy
- **New Tests**: Use pytest with `@pytest.mark.asyncio` decorator for async tests
- **Fixtures**: Use fixtures in `tests/conftest.py` for common setup
- **Test Data**: Located in `tests/data/` directory
- **CI/CD**: Run `uv run pytest` before deploying
- **Coverage**: Run `uv run pytest --cov=knowledge_base --cov-report=html`
- **Agentic Test Manager**: Run `uv run kb-test` for intelligent test orchestration
- **Evolutionary Approach**: Tests improve and adapt over time based on historical patterns

## API Integration

### 🔄 **Real API vs Mocks**
The system now uses **real OpenAI-compatible API calls** to `http://localhost:8317/v1`:

- **Chat Completions**: Direct HTTP requests using httpx
- **Tool Calling**: Structured output via OpenAI tool calling format
- **Error Handling**: Retry logic with exponential backoff
- **Streaming Support**: Server-sent events for real-time responses
- **No API Key Required**: Local server authentication optional

### 🌐 **HTTP Client Implementation**
```python
# New http_client.py follows reference implementation
from knowledge_base.http_client import HTTPClient, ChatMessage, ChatCompletionRequest

client = HTTPClient()
request = ChatCompletionRequest(
    model="gemini-2.5-flash-lite",
    messages=[ChatMessage(role="user", content="Hello")],
    tools=[...],  # Tool definitions
    tool_choice="auto"
)

response = await client.chat_completion(request)
```

### 🔧 **Configuration Management**
```python
# config.py with real API defaults
class LLMConfig(BaseModel):
    openai_api_base: str = Field(default="http://localhost:8317/v1")
    model_name: str = Field(default="gemini-2.5-flash-lite")
    api_key: str | None = Field(default="not-required")

config = get_config()
# Uses: config.llm.openai_api_base, config.llm.model_name, config.llm.api_key
```

---

## 🚀 **Ready for Production**

Start your local API server at `localhost:8317` and enjoy the complete GraphRAG system with real OpenAI-compatible API integration!

**Current Status**: ✅ All mock LLM calls successfully replaced with real API calls
**API Endpoint**: `http://localhost:8317/v1`
**Default Model**: `gemini-2.5-flash-lite`
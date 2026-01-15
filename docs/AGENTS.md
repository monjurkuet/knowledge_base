# Knowledge Base GraphRAG System - AI Agent Instructions

## Project Overview
Agentic GraphRAG system for knowledge ingestion, entity resolution, hierarchical community detection, and recursive summarization. Built with FastAPI, PostgreSQL with pgvector, and Google Gemini LLMs.

## Tech Stack
- **Language**: Python 3.12+
- **Package Manager**: uv (always use `uv` for dependency management)
- **Backend**: FastAPI with uvicorn
- **Database**: PostgreSQL with pgvector extension (user: agentzero, host: localhost)
- **LLM**: Google Gemini (gemini-2.5-flash by default)
- **Frontend**: Streamlit (optional dependency)
- **Testing**: pytest with pytest-asyncio
- **Linting**: Ruff (replaces flake8, black, isort)

## Quick Start Commands

### Installation
```bash
# Install all dependencies
uv sync

# Install with development dependencies
uv sync --dev

# Install with Streamlit UI dependencies
uv sync --all-extras
```

### Running the Application
```bash
# Run API server
uv run kb-server

# Run document ingestion pipeline
uv run kb-pipeline path/to/file.txt

# Run Streamlit UI (cd into streamlit-ui first)
cd streamlit-ui && uv run streamlit run app.py

# Alternative: run Python modules directly
uv run python -m knowledge_base.main_api
uv run python -m knowledge_base.pipeline path/to/file.txt
```

### Testing
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

# Run agentic test manager (2026 system)
uv run kb-test

# Run agentic test manager with analysis only
uv run kb-test --analyze-only

# Suggest tests for specific module
uv run kb-test --suggest pipeline

# Generate report from history
uv run kb-test --report-only
```

### Code Quality
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

## Database Configuration
- **Host**: localhost
- **User**: agentzero
- **Database**: knowledge_base
- **Connection String Format**: `postgresql://{user}:{password}@{host}:{port}/{name}`
- **Extensions**: pgvector, pg_trgm, uuid-ossp
- **Tables**: nodes, edges, communities, community_membership, community_hierarchy, events
- **Always Use**: `psycopg.AsyncConnection` for async database operations

## Code Style Guidelines

### Import Order
1. Standard library imports
2. Third-party imports
3. Local imports (from `knowledge_base.module`)
4. One import per line preferred

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
  async def ingest(text: str, model: str) -> KnowledgeGraph:
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
  from pydantic import BaseModel, Field

  class Entity(BaseModel):
      name: str = Field(..., description="Entity name")
      type: str = Field(..., description="Entity type")
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
  from fastapi import HTTPException
  import logging

  try:
      result = await risky_operation()
  except Exception as e:
      logging.error(f"Operation failed: {e}", exc_info=True)
      raise HTTPException(status_code=500, detail="Internal server error")
  ```

### String Formatting
- **Preferred**: F-strings for all interpolation (e.g., `f"Error: {error}"`)
- **Avoid**: `.format()` and `%` formatting

## Architecture Notes

### Core Components
- **config.py**: Centralized configuration using Pydantic models (never import `.env` directly)
- **pipeline.py**: Orchestrates full GraphRAG workflow (extraction → resolution → communities → summarization)
- **ingestor.py**: LLM-powered entity and relationship extraction using Google Gemini
- **resolver.py**: Hybrid entity resolution combining vector similarity + LLM reasoning
- **community.py**: Hierarchical community detection using Leiden algorithm (graspologic)
- **summarizer.py**: Recursive summarization of community hierarchies
- **api.py**: FastAPI endpoints for all operations
- **websocket.py**: Real-time updates for long-running operations

### Data Flow
1. **Ingestion**: Text → LLM extraction → Entity/Relationship/Event objects
2. **Resolution**: Generate embeddings → Vector search → LLM reasoning → Merge/LINK/KEEP_SEPARATE
3. **Community Detection**: Load graph → NetworkX → Leiden clustering → Save hierarchy
4. **Summarization**: Leaf communities → Generate summaries → Roll up to parents → Recursive

### Testing Strategy
- **New Tests**: Use pytest with `@pytest.mark.asyncio` decorator for async tests
- **Fixtures**: Use fixtures in `tests/conftest.py` for common setup
- **Legacy Tests**: Keep existing `master_test.py` for now (gradual migration)
- **Test Data**: Located in `tests/data/` directory
- **CI/CD**: Run `uv run pytest` before deploying
- **Agentic Test Manager (2026)**: Run `uv run kb-test` for intelligent test orchestration
  - Tracks test execution history in `tests/test_history.json`
  - Analyzes patterns and suggests improvements
  - Identifies flaky tests and regression trends
  - Auto-generates test reports with coverage insights
  - Provides AI-powered suggestions for missing tests
  - Evolutionary approach: Tests improve and adapt over time based on historical patterns

### LLM Configuration
- **Provider**: Google (via `google-generativeai`)
- **Default Model**: gemini-2.5-flash
- **Embedding Dimension**: 768 (Google text-embedding-004)
- **Configuration**: Set via `LLM_MODEL` environment variable

### Vector Operations
- **Embedding**: 768-dimensional vectors for entities and communities
- **Index**: HNSW index for cosine similarity search
- **Search**: Use `pgvector` for semantic search in PostgreSQL

## Important Constraints
- **Never commit** `.env` files (use `.env.template` as reference)
- **Always use** `uv` for dependency management (never pip)
- **Database**: Always use async connections (`AsyncConnection`)
- **LLM Models**: Use configured model from `config.llm.model_name`
- **Error Handling**: Log all errors with context, never expose secrets
- **Type Safety**: All functions must have type hints
- **Async Patterns**: Use async/await consistently throughout codebase
- **Test Evolution**: Use `test_agent.py` for intelligent test management and tracking
  - Run `uv run kb-test` before committing to track test evolution
  - Review generated reports in `test_report.md` for insights
  - Check `tests/test_history.json` for historical patterns and flaky test detection

## Streamlit UI Integration
- **Location**: `streamlit-ui/app.py`
- **Dependencies**: Install via `uv sync --extra streamlit`
- **API Connection**: Uses `STREAMLIT_API_URL` and `STREAMLIT_WS_URL` from config
- **Development**: Run from `streamlit-ui/` directory with `uv run streamlit run app.py`

## Environment Variables Reference
See `.env.template` for all available variables. Key variables:
- `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT`, `DB_NAME`
- `GOOGLE_API_KEY` (required for LLM operations)
- `LLM_MODEL` (default: gemini-2.5-flash)
- `API_HOST`, `API_PORT` (default: 0.0.0.0:8000)
- `LOG_LEVEL` (default: INFO)
- `STREAMLIT_API_URL`, `STREAMLIT_WS_URL`

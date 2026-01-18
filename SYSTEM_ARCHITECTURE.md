# Knowledge Base GraphRAG System - Architecture Documentation

## Overview

The Knowledge Base GraphRAG system is a sophisticated AI-powered knowledge management platform featuring multi-domain support, entity resolution, hierarchical community detection, and recursive summarization. The system follows a modern microservices architecture with real-time updates, robust error handling, and production readiness.

## System Components

### API Layer (FastAPI)
- Complete REST API endpoints for knowledge graph operations
- WebSocket support for real-time updates and progress tracking
- Health, readiness, and liveness probes for container orchestration
- Prometheus metrics endpoint for monitoring

### Background Processing
- Full pipeline implementation with background task support
- Asynchronous processing for ingestion, community detection, and summarization
- Real-time progress reporting via WebSockets

### Multi-Domain Architecture
- AI-powered domain detection and auto-creation
- Rich schema templates with entity/relationship definitions
- Domain-specific configurations and extraction prompts

### Graph Processing Pipeline
- Entity and relationship extraction using LLMs
- Entity resolution and deduplication
- Community detection with Leiden algorithm
- Recursive summarization of communities

### Error Handling & Resilience
- Circuit breaker implementation for external API calls
- Comprehensive exception hierarchy
- Proper logging and error propagation

### UI Layer (Streamlit)
- Interactive knowledge graph visualization
- Real-time log streaming
- Search and query capabilities
- Domain management interface

### Database Layer
- Complete PostgreSQL schema with pgvector support
- Multi-domain support with proper relationships
- Vector indexing for semantic search
- Hierarchical community structures

## API Endpoints

### Core Endpoints
- `GET /` - Root endpoint
- `GET /health`, `GET /ready`, `GET /live` - Health check endpoints
- `GET /metrics` - Prometheus metrics endpoint

### Ingestion Endpoints
- `POST /api/ingest/text` - Ingest text content (returns status: "started")
- `POST /api/ingest/file` - Upload and ingest files (returns status: "started")

### Graph Endpoints
- `GET /api/nodes` - Retrieve knowledge graph nodes
- `GET /api/edges` - Retrieve knowledge graph edges
- `GET /api/communities` - Get detected communities
- `GET /api/graph` - Get graph visualization data

### Processing Endpoints
- `POST /api/community/detect` - Run community detection
- `POST /api/summarize` - Run recursive summarization
- `POST /api/search` - Vector similarity search

### Domain Management
- `GET /api/domains` - List all domains
- `GET /api/domains/{domain_id}` - Get specific domain
- `GET /api/domains/{domain_id}/schema` - Get domain schema

## Background Task Functions

- `run_pipeline_background` - Runs the knowledge pipeline in the background
- `run_summarization_background` - Executes recursive summarization of communities
- `run_community_detection_background` - Performs community detection using Leiden algorithm

## Google GenAI Integration

The system uses the modern `google-genai` library with:
- `from google import genai` - Correct import pattern per Google's documentation
- `genai.Client(api_key=api_key).models.embed_content()` - For text embedding generation
- Embedding caching for performance optimization

## Response Formats

### Ingestion Responses
```json
{
  "status": "started",
  "message": "Started ingestion of text content to domain",
  "task_id": "uuid",
  "background": true
}
```

### Search Results
```json
{
  "results": [
    {
      "id": "node_id",
      "name": "entity_name",
      "type": "entity_type",
      "description": "entity_description",
      "similarity": 0.85
    }
  ],
  "count": 10
}
```

### Statistics Response
```json
{
  "nodes_count": 150,
  "edges_count": 42,
  "communities_count": 8,
  "events_count": 23
}
```

## Testing

The system includes comprehensive test coverage with:
- API endpoint tests
- Domain management tests
- Ingestion functionality tests
- Graph operations tests
- WebSocket integration tests

## Production Features

- Health checks and monitoring
- Real-time WebSocket communication
- Circuit breaker protection
- Embedding caching
- Multi-domain support
- Hierarchical community detection
- Recursive summarization

## Error Handling

Comprehensive error handling throughout the system with:
- Proper HTTP status codes
- Meaningful error messages
- Graceful degradation
- Circuit breaker patterns
- Retry logic with exponential backoff

## Security & Monitoring

- API rate limiting considerations
- Structured logging with correlation IDs
- Distributed tracing (OpenTelemetry)
- Performance monitoring dashboards
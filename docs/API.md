# Knowledge Base API Documentation

## Overview

The Knowledge Base API is a GraphRAG (Graph Retrieval Augmented Generation) system for extracting, storing, and querying knowledge from text documents.

**Base URL:** `http://localhost:8000`
**API Version:** 1.0.0

## Authentication

Currently, the API does not require authentication. This will be added in a future update.

## Endpoints

### Health & Status

#### GET /health
Check overall API health status.

**Response:**
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "uptime_seconds": 123.45,
  "database": "healthy",
  "timestamp": "2024-01-20T12:00:00Z"
}
```

#### GET /health/db
Check database connection health.

**Response:**
```json
{
  "status": "healthy",
  "connection_time_ms": 12.5,
  "error": null
}
```

#### GET /metrics
Get application metrics.

**Response:**
```json
{
  "uptime_seconds": 123.45,
  "memory_usage_mb": 125.3,
  "cpu_percent": 5.2,
  "thread_count": 8,
  "timestamp": "2024-01-20T12:00:00Z"
}
```

### Domains

#### GET /api/domains
List all domains.

**Response:**
```json
[
  {
    "id": "uuid",
    "name": "general_knowledge",
    "display_name": "General Knowledge",
    "description": "Default domain for general knowledge",
    "is_active": true,
    "created_at": "2024-01-01T00:00:00Z",
    "updated_at": "2024-01-01T00:00:00Z"
  }
]
```

#### GET /api/domains/{domain_id}
Get a specific domain by ID.

#### GET /api/domains/{domain_id}/schema
Get domain schema (entity and relationship types).

**Response:**
```json
{
  "entities": [
    {
      "id": "uuid",
      "name": "person",
      "display_name": "Person",
      "description": "A person entity"
    }
  ],
  "relationships": [
    {
      "id": "uuid",
      "name": "works_for",
      "display_name": "Works For",
      "description": "Employment relationship"
    }
  ]
}
```

### Ingestion

#### POST /api/ingest/text
Ingest text content into the knowledge base.

**Request Body:**
```json
{
  "text": "TechCorp is a technology company...",
  "filename": "techcorp.txt",
  "channel_id": "optional-channel-id",
  "domain_id": "optional-domain-id"
}
```

**Response:**
```json
{
  "status": "success",
  "message": "Successfully ingested 1338 characters"
}
```

#### POST /api/ingest/file
Upload and ingest a text file.

**Request:** `multipart/form-data` with file field `file`

**Response:**
```json
{
  "status": "success",
  "message": "Successfully ingested file techcorp.txt"
}
```

### Search

#### POST /api/search
Search nodes by text query.

**Request Body:**
```json
{
  "query": "TechCorp",
  "limit": 10
}
```

**Response:**
```json
{
  "results": [
    {
      "id": "uuid",
      "name": "TechCorp",
      "type": "company",
      "description": "Leading technology company"
    }
  ],
  "count": 1
}
```

### Graph

#### GET /api/nodes
Get nodes from the knowledge graph.

**Query Parameters:**
- `offset` (default: 0)
- `limit` (default: 100)
- `node_type` (optional) - Filter by node type

**Response:**
```json
{
  "nodes": [
    {
      "id": "uuid",
      "name": "Alice Chen",
      "type": "person",
      "description": "Software engineer"
    }
  ],
  "total": 29,
  "limit": 100,
  "offset": 0
}
```

#### GET /api/edges
Get edges from the knowledge graph.

**Query Parameters:**
- `offset` (default: 0)
- `limit` (default: 100)

**Response:**
```json
{
  "edges": [
    {
      "source_id": "uuid",
      "target_id": "uuid",
      "type": "works_for",
      "description": "Alice works at TechCorp",
      "weight": 1.0
    }
  ],
  "total": 38,
  "limit": 100,
  "offset": 0
}
```

#### GET /api/graph
Get graph data for visualization.

**Query Parameters:**
- `limit` (default: 500) - Maximum nodes/edges to return

**Response:**
```json
{
  "nodes": [
    {
      "id": "uuid",
      "name": "TechCorp",
      "type": "company",
      "description": "Technology company"
    }
  ],
  "edges": [
    {
      "source": "uuid",
      "target": "uuid",
      "type": "works_for",
      "description": "Employment",
      "weight": 1.0
    }
  ]
}
```

### Communities

#### GET /api/community
Get community information.

**Response:**
```json
[
  {
    "id": "uuid",
    "title": "TechCorp: AI Innovation",
    "summary": "Analysis of AI innovation at TechCorp",
    "node_count": 8
  }
]
```

#### POST /api/community/detect
Run community detection on the graph.

**Query Parameters:**
- `channel_id` (optional) - WebSocket channel for progress updates

**Response:**
```json
{
  "status": "success",
  "message": "Detected communities for 29 nodes"
}
```

#### POST /api/community/summarize
Run recursive summarization on communities.

**Response:**
```json
{
  "status": "success",
  "message": "Summarization completed"
}
```

### Statistics

#### GET /api/stats
Get database statistics.

**Response:**
```json
{
  "nodes_count": 29,
  "edges_count": 38,
  "communities_count": 4,
  "events_count": 0
}
```

### WebSocket

#### WS /api/ws
WebSocket endpoint for real-time updates.

#### WS /api/ws/{channel}
WebSocket endpoint for channel-specific updates.

## Error Responses

All errors follow this structure:

```json
{
  "error": "ErrorType",
  "message": "Human-readable error message",
  "details": {
    "additional": "context",
    "request_id": "uuid"
  },
  "request_id": "uuid"
}
```

**Common HTTP Status Codes:**
- `200 OK` - Success
- `400 Bad Request` - Invalid request
- `422 Unprocessable Entity` - Validation error
- `500 Internal Server Error` - Server error
- `503 Service Unavailable` - LLM API error

## Example Usage

### Ingest Text

```bash
curl -X POST http://localhost:8000/api/ingest/text \
  -H "Content-Type: application/json" \
  -d '{
    "text": "TechCorp is a technology company founded in 2010.",
    "filename": "techcorp.txt"
  }'
```

### Search

```bash
curl -X POST http://localhost:8000/api/search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "TechCorp",
    "limit": 5
  }'
```

### Get Statistics

```bash
curl http://localhost:8000/api/stats
```

### Health Check

```bash
curl http://localhost:8000/api/health
```
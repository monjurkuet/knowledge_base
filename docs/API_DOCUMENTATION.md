# Knowledge Base API Documentation

## Overview

The Knowledge Base API provides RESTful endpoints for interacting with the GraphRAG system, enabling ingestion, querying, and analysis of knowledge graphs extracted from text documents.

## Base URL
```
http://localhost:8000
```

## Authentication
Currently, no authentication is required. For production deployment, implement appropriate authentication mechanisms.

## Endpoints

### Root

#### GET /
Get API information and status.

**Response:**
```json
{
  "message": "Knowledge Base API",
  "version": "1.0.0"
}
```

### Statistics

#### GET /api/stats
Get database statistics including counts of nodes, edges, communities, and events.

**Response:**
```json
{
  "nodes_count": 31,
  "edges_count": 51,
  "communities_count": 6,
  "events_count": 34
}
```

### Nodes

#### GET /api/nodes
Retrieve nodes from the knowledge graph.

**Query Parameters:**
- `limit` (integer, optional): Maximum number of nodes to return (default: 100)
- `node_type` (string, optional): Filter by node type (e.g., "Person", "Organization")

**Response:**
```json
[
  {
    "id": "uuid-string",
    "name": "Entity Name",
    "type": "Entity Type",
    "description": "Entity description"
  }
]
```

### Edges

#### GET /api/edges
Retrieve edges from the knowledge graph.

**Query Parameters:**
- `limit` (integer, optional): Maximum number of edges to return (default: 500)

**Response:**
```json
[
  {
    "source_id": "uuid-string",
    "target_id": "uuid-string",
    "type": "RELATIONSHIP_TYPE",
    "description": "Relationship description",
    "weight": 1.0
  }
]
```

### Communities

#### GET /api/communities
Get information about detected communities.

**Response:**
```json
[
  {
    "id": "uuid-string",
    "title": "Community Title",
    "summary": "Community summary",
    "node_count": 10
  }
]
```

### Search

#### POST /api/search
Search nodes using text queries.

**Request Body:**
```json
{
  "query": "search term",
  "limit": 10
}
```

**Response:**
```json
{
  "results": [
    {
      "id": "uuid-string",
      "name": "Entity Name",
      "type": "Entity Type",
      "description": "Entity description"
    }
  ],
  "count": 1
}
```

### Graph Data

#### GET /api/graph
Get graph data for visualization.

**Query Parameters:**
- `limit` (integer, optional): Maximum nodes/edges to return (default: 500)

**Response:**
```json
{
  "nodes": [
    {
      "id": "uuid-string",
      "name": "Entity Name",
      "type": "Entity Type",
      "description": "Entity description"
    }
  ],
  "edges": [
    {
      "source": "uuid-string",
      "target": "uuid-string",
      "type": "RELATIONSHIP_TYPE",
      "description": "Relationship description",
      "weight": 1.0
    }
  ]
}
```

### Ingestion

#### POST /api/ingest/text
Ingest text content directly.

**Request Body:**
```json
{
  "text": "Text content to ingest",
  "filename": "optional_filename.txt"
}
```

**Response:**
```json
{
  "status": "success",
  "message": "Successfully ingested 123 characters"
}
```

#### POST /api/ingest/file
Upload and ingest a text file.

**Form Data:**
- `file`: Text file to upload

**Response:**
```json
{
  "status": "success",
  "message": "Successfully ingested file example.txt"
}
```

### Operations

#### POST /api/community/detect
Run community detection on the current graph.

**Response:**
```json
{
  "status": "success",
  "message": "Detected communities for 31 nodes"
}
```

#### POST /api/summarize
Run recursive summarization on communities.

**Response:**
```json
{
  "status": "success",
  "message": "Summarization completed"
}
```

## WebSocket Endpoints

### WS /ws
Real-time updates for general operations.

### WS /ws/{channel}
Real-time updates for specific channels.

**Message Format:**
```json
{
  "type": "progress|status|error",
  "operation": "operation_name",
  "progress": 0.5,
  "message": "Progress message",
  "timestamp": 1234567890.123
}
```

## Error Handling

All endpoints return appropriate HTTP status codes:
- `200`: Success
- `400`: Bad Request
- `404`: Not Found
- `500`: Internal Server Error

Error responses include a `detail` field with error information.

## Rate Limiting

Currently no rate limiting is implemented. For production deployment, implement appropriate rate limiting based on usage patterns.

## Data Types

### Node Types
- `Person`: Individuals mentioned in the text
- `Organization`: Companies, institutions, groups
- `Project`: Initiatives, programs, research projects
- `Concept`: Abstract ideas, technologies, methodologies
- `Location`: Geographic locations
- `Event`: Temporal events

### Relationship Types
- `WORKS_AT`: Employment relationships
- `AUTHORED`: Authorship relationships
- `LEADS`: Leadership relationships
- `PART_OF`: Hierarchical relationships
- `FUNDED_BY`: Funding relationships
- Custom types based on extracted content

## Performance Considerations

- Graph queries can be resource-intensive for large datasets
- Consider implementing pagination for large result sets
- Community detection and summarization are computationally expensive operations
- WebSocket connections should be managed efficiently for real-time updates
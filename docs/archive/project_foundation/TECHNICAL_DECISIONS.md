# Technical Decisions
## Multi-Domain Knowledge Base GraphRAG System

## Schema Design

### Multi-Domain Support

#### New Tables

**domains**
```sql
CREATE TABLE domains (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) UNIQUE NOT NULL,
    display_name VARCHAR(255) NOT NULL,
    description TEXT,
    template_config JSONB NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    is_active BOOLEAN DEFAULT TRUE
);
```

**Rationale:**
- UUID for scalability and distributed systems
- JSONB template_config stores flexible domain-specific configuration
- is_active allows soft deletion and versioning

---

**domain_entity_types**
```sql
CREATE TABLE domain_entity_types (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    domain_id UUID REFERENCES domains(id),
    name VARCHAR(255) NOT NULL,
    display_name VARCHAR(255) NOT NULL,
    description TEXT,
    icon VARCHAR(100),
    color VARCHAR(20),
    validation_rules JSONB,
    extraction_prompt TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(domain_id, name)
);
```

**Rationale:**
- Each domain defines its own entity types
- icon/color for UI visualization
- validation_rules for data integrity
- extraction_prompt for LLM domain-specific extraction

---

**domain_relationship_types**
```sql
CREATE TABLE domain_relationship_types (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    domain_id UUID REFERENCES domains(id),
    name VARCHAR(255) NOT NULL,
    display_name VARCHAR(255) NOT NULL,
    description TEXT,
    source_entity_type VARCHAR(255),
    target_entity_type VARCHAR(255),
    is_directional BOOLEAN DEFAULT TRUE,
    validation_rules JSONB,
    extraction_prompt TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(domain_id, name)
);
```

**Rationale:**
- Each domain defines relationship types between its entities
- source/target entity types enforce type constraints
- is_directional supports both directed and undirected relationships

---

**Enhanced nodes table**
```sql
ALTER TABLE nodes
ADD COLUMN domain_id UUID REFERENCES domains(id),
ADD COLUMN domain_entity_type_id UUID REFERENCES domain_entity_types(id),
ADD COLUMN domain_attributes JSONB DEFAULT '{}',
ADD COLUMN confidence FLOAT DEFAULT 1.0;
```

**Rationale:**
- domain_id enables multi-domain separation
- domain_entity_type_id links to domain-specific type
- domain_attributes stores domain-specific metadata
- confidence tracks extraction accuracy

---

**Enhanced edges table**
```sql
ALTER TABLE edges
ADD COLUMN domain_id UUID REFERENCES domains(id),
ADD COLUMN domain_relationship_type_id UUID REFERENCES domain_relationship_types(id),
ADD COLUMN domain_attributes JSONB DEFAULT '{}',
ADD COLUMN confidence FLOAT DEFAULT 1.0;
```

**Rationale:**
- Mirrors nodes table structure
- Enables domain-specific relationship typing

---

**cross_domain_links**
```sql
CREATE TABLE cross_domain_links (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    source_node_id UUID REFERENCES nodes(id),
    target_node_id UUID REFERENCES nodes(id),
    source_domain_id UUID REFERENCES domains(id),
    target_domain_id UUID REFERENCES domains(id),
    link_type VARCHAR(255) NOT NULL,
    confidence FLOAT DEFAULT 0.8,
    verified BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(source_node_id, target_node_id, link_type)
);
```

**Rationale:**
- Separate table for cross-domain connections
- High confidence threshold (0.8) to reduce false positives
- verified flag for manual confirmation
- link_type describes the connection nature

---

### Indexes for Performance

```sql
-- Domain-based queries
CREATE INDEX idx_nodes_domain ON nodes(domain_id);
CREATE INDEX idx_edges_domain ON edges(domain_id);

-- Type-based queries
CREATE INDEX idx_nodes_entity_type ON nodes(domain_entity_type_id);
CREATE INDEX idx_edges_relationship_type ON edges(domain_relationship_type_id);

-- Cross-domain lookups
CREATE INDEX idx_cross_links_source ON cross_domain_links(source_node_id);
CREATE INDEX idx_cross_links_target ON cross_domain_links(target_node_id);

-- Vector similarity search
CREATE INDEX idx_nodes_vector ON nodes USING hnsw(embedding vector_cosine_ops);
```

**Rationale:**
- B-tree indexes for exact match queries (domain, type)
- HNSW index for vector similarity search
- Composite indexes for common join patterns

---

## Template System Architecture

### Template Structure

```python
@dataclass
class DomainTemplate:
    id: str
    name: str
    display_name: str
    description: str
    entity_types: List[EntityTypeTemplate]
    relationship_types: List[RelationshipTypeTemplate]
    extraction_config: ExtractionConfig
    analysis_config: AnalysisConfig
    ui_config: UIConfig
```

### EntityTypeTemplate

```python
@dataclass
class EntityTypeTemplate:
    name: str
    display_name: str
    description: str
    icon: str
    color: str
    validation_rules: Dict[str, Any]
    extraction_prompt: str
    example_patterns: List[str]
    required_fields: List[str]
    optional_fields: List[str]
```

### RelationshipTypeTemplate

```python
@dataclass
class RelationshipTypeTemplate:
    name: str
    display_name: str
    description: str
    source_entity_types: List[str]
    target_entity_types: List[str]
    is_directional: bool
    validation_rules: Dict[str, Any]
    extraction_prompt: str
    example_patterns: List[str]
```

### ExtractionConfig

```python
@dataclass
class ExtractionConfig:
    llm_model: str
    temperature: float
    max_tokens: int
    system_prompt: str
    entity_prompt_template: str
    relationship_prompt_template: str
    post_processing_rules: List[str]
    confidence_threshold: float
```

### AnalysisConfig

```python
@dataclass
class AnalysisConfig:
    community_detection: CommunityConfig
    summarization: SummarizationConfig
    trend_analysis: TrendConfig
    insight_generation: InsightConfig
```

### UIConfig

```python
@dataclass
class UIConfig:
    color_scheme: Dict[str, str]
    layout: str
    default_views: List[str]
    visualization_settings: Dict[str, Any]
```

---

## Cross-Domain Linking Strategy

### Linking Methods

#### 1. Semantic Similarity (Vector-Based)
- Compare entity embeddings across domains
- Threshold: cosine similarity > 0.85
- Use for: same entity appearing in multiple domains

**Implementation:**
```python
async def find_semantic_links(
    entity_id: UUID,
    source_domain: str,
    target_domains: List[str],
    threshold: float = 0.85
) -> List[CrossDomainLink]:
    source_embedding = await get_entity_embedding(entity_id)
    candidates = await vector_search(
        source_embedding,
        domains=target_domains,
        limit=20
    )
    return [
        CrossDomainLink(
            source=entity_id,
            target=c.id,
            similarity=c.similarity
        )
        for c in candidates
        if c.similarity > threshold and c.domain != source_domain
    ]
```

#### 2. Name/Attribute Matching (Rule-Based)
- Exact or fuzzy match on entity names
- Match on shared attributes (e.g., URLs, identifiers)
- Threshold: Levenshtein distance < 2 or exact match

**Implementation:**
```python
async def find_attribute_links(
    entity: Entity,
    target_domains: List[str]
) -> List[CrossDomainLink]:
    links = []
    for domain in target_domains:
        matching_entities = await query_entities_by_attributes(
            domain=domain,
            attributes=entity.domain_attributes
        )
        links.extend([
            CrossDomainLink(
                source=entity.id,
                target=me.id,
                link_type="attribute_match"
            )
            for me in matching_entities
        ])
    return links
```

#### 3. Contextual Co-occurrence (Pattern-Based)
- Entities that frequently appear together in documents
- Requires document-level metadata tracking
- Threshold: co-occurrence count > 3

**Implementation:**
```python
async def find_cooccurrence_links(
    entity_id: UUID,
    min_cooccurrence: int = 3
) -> List[CrossDomainLink]:
    documents = await get_entity_documents(entity_id)
    cooccurrences = await count_entity_cooccurrences(documents)
    return [
        CrossDomainLink(
            source=entity_id,
            target=entity,
            link_type="cooccurrence",
            count=count
        )
        for entity, count in cooccurrences.items()
        if count >= min_cooccurrence
    ]
```

#### 4. LLM-Based Reasoning (Intelligent)
- Use LLM to determine if entities represent the same concept
- Provides explanation and confidence
- Threshold: LLM confidence > 0.7

**Implementation:**
```python
async def find_llm_links(
    source_entity: Entity,
    target_entity: Entity
) -> Optional[CrossDomainLink]:
    prompt = f"""
    Compare these two entities and determine if they represent the same concept:

    Entity 1: {source_entity.name} ({source_entity.description})
    Domain: {source_entity.domain}

    Entity 2: {target_entity.name} ({target_entity.description})
    Domain: {target_entity.domain}

    Respond with:
    - same_concept: true/false
    - confidence: 0.0-1.0
    - explanation: brief explanation
    """
    result = await llm_analyze(prompt)
    if result.same_concept and result.confidence > 0.7:
        return CrossDomainLink(
            source=source_entity.id,
            target=target_entity.id,
            link_type="llm_reasoning",
            confidence=result.confidence,
            explanation=result.explanation
        )
```

---

### Link Validation Workflow

```python
async def validate_cross_domain_links(
    links: List[CrossDomainLink]
) -> List[CrossDomainLink]:
    validated = []
    for link in links:
        # High confidence: auto-approve
        if link.confidence >= 0.9:
            link.verified = True
            validated.append(link)
        # Medium confidence: LLM verification
        elif link.confidence >= 0.7:
            verification = await llm_verify_link(link)
            if verification.is_valid:
                link.verified = True
                link.confidence = verification.confidence
                validated.append(link)
        # Low confidence: manual review required
        else:
            link.verified = False
            validated.append(link)
    return validated
```

---

## Trade-offs and Alternatives

### Decision 1: Single vs. Separate Tables per Domain

**Chosen Approach:** Single nodes/edges tables with domain columns

**Alternatives Considered:**
1. Separate tables per domain (ai_engineering_nodes, crypto_nodes, etc.)
2. Document-oriented (NoSQL) approach

**Trade-offs:**

| Aspect | Chosen Approach | Separate Tables | NoSQL |
|--------|-----------------|-----------------|-------|
| Cross-domain queries | Easy | Requires UNION | Easy |
| Schema flexibility | Medium | High | Very High |
| Performance | Good | Excellent | Variable |
| Migration complexity | Low | High | Low |
| Type safety | Good | Excellent | Poor |
| Maintenance | Simple | Complex | Medium |

**Rationale:**
- Single tables simplify cross-domain analysis
- Schema versioning handles flexibility needs
- PostgreSQL performance is sufficient for expected scale
- Type safety and maintainability are critical

---

### Decision 2: Template System Complexity

**Chosen Approach:** Config-based templates with code validation

**Alternatives Considered:**
1. Full DSL (Domain Specific Language)
2. Code-only approach (Python classes)
3. No templates (hard-coded domains)

**Trade-offs:**

| Aspect | Config + Code | DSL | Code-only | No Templates |
|--------|--------------|-----|-----------|--------------|
| Flexibility | High | Very High | Medium | None |
| Learning curve | Low | High | Medium | N/A |
| Performance | Good | Variable | Excellent | Excellent |
| Maintainability | Good | Poor | Good | Poor |
| Validation | Excellent | Good | Excellent | N/A |

**Rationale:**
- JSON config provides readability and ease of editing
- Python validation ensures correctness
- Lower learning curve than full DSL
- Balance between flexibility and maintainability

---

### Decision 3: Cross-Domain Linking Strategy

**Chosen Approach:** Multi-method approach with confidence scoring

**Alternatives Considered:**
1. Vector similarity only
2. LLM reasoning only
3. Manual linking only

**Trade-offs:**

| Aspect | Multi-method | Vector Only | LLM Only | Manual Only |
|--------|--------------|-------------|----------|-------------|
| Accuracy | High | Medium | High | Very High |
| Scalability | Good | Excellent | Poor | Poor |
| Cost | Medium | Low | High | Very High |
| Speed | Good | Excellent | Poor | N/A |
| False positives | Low | High | Medium | None |

**Rationale:**
- Multiple methods provide complementary strengths
- Confidence scoring allows quality control
- Balances accuracy, cost, and scalability
- Can tune method weighting based on use case

---

### Decision 4: Entity Resolution Granularity

**Chosen Approach:** Domain-aware resolution with cross-domain linking

**Alternatives Considered:**
1. Global resolution (all entities together)
2. Strict domain isolation
3. Hierarchical resolution (within domain first, then cross-domain)

**Trade-offs:**

| Aspect | Chosen Approach | Global | Isolation | Hierarchical |
|--------|-----------------|--------|-----------|--------------|
| Domain semantics | Preserved | Lost | Preserved | Preserved |
| Cross-domain insights | Enabled | Automatic | None | Available |
| Resolution accuracy | High | Medium | High | High |
| Complexity | Medium | Low | Very Low | High |
| Performance | Good | Variable | Excellent | Good |

**Rationale:**
- Preserves domain-specific semantics
- Enables cross-domain discovery
- More accurate than global resolution
- Simpler than full hierarchical approach

---

## Performance Considerations

### Vector Search Optimization
- Use HNSW index for similarity search
- Set ef_construction=200 for good recall/accuracy balance
- Cache frequent queries
- Batch similarity calculations when possible

### Database Connection Pooling
- Use async connection pool (psycopg_pool)
- Min pool size: 5, Max: 20
- Connection timeout: 30s
- Query timeout: 60s

### LLM API Rate Limiting
- Implement exponential backoff
- Batch requests when possible
- Cache extraction results
- Use streaming for long responses

### Memory Management
- Process large documents in chunks
- Limit graph size for display (pagination)
- Clear caches periodically
- Monitor memory usage in production

---

## Security Considerations

### Input Validation
- Validate all user inputs using Pydantic models
- Sanitize SQL queries (parameterized queries only)
- Limit file upload sizes (max 50MB per document)
- Validate file types (txt, pdf, md only)

### API Security
- Implement API key authentication
- Rate limiting per user
- HTTPS only in production
- CORS configuration

### Data Privacy
- Encrypt sensitive data at rest
- Log audit trails for sensitive operations
- Anonymize user data for analytics
- Implement data retention policies

---

## Future Extensibility

### Adding New Domains
1. Create domain template (JSON config)
2. Define entity and relationship types
3. Configure extraction prompts
4. Set up analysis modules
5. Test with sample data
6. Deploy via API

### New Data Sources
1. Implement source-specific connector
2. Map source data to domain schema
3. Add validation rules
4. Test extraction quality
5. Add to ingestion pipeline

### New Analysis Modules
1. Define module interface (Abstract Base Class)
2. Implement domain-specific logic
3. Register in analysis config
4. Add tests
5. Update UI to display results

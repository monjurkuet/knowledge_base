-- ================================================================
-- KNOWLEDGE BASE SCHEMA (High-Fidelity GraphRAG) v2.0
-- ================================================================
-- Multi-Domain Knowledge Base with:
-- 1. Hybrid Search (Vector + Graph)
-- 2. Hierarchical Community Detection (Leiden)
-- 3. Recursive Summarization
-- 4. Multi-Domain Support
-- ================================================================

-- Extensions
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS pg_trgm;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ================================================================
-- 0. DOMAINS (Multi-Domain Support)
-- ================================================================

CREATE TABLE domains (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) UNIQUE NOT NULL,
    display_name VARCHAR(255) NOT NULL,
    description TEXT,
    template_config JSONB NOT NULL DEFAULT '{}',
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_domains_active ON domains(is_active) WHERE is_active = TRUE;
CREATE INDEX idx_domains_name ON domains(name);

COMMENT ON TABLE domains IS 'Stores domain configurations for multi-domain knowledge base support';
COMMENT ON COLUMN domains.name IS 'Unique internal name (snake_case)';
COMMENT ON COLUMN domains.display_name IS 'Human-readable name';
COMMENT ON COLUMN domains.template_config IS 'JSON configuration for domain-specific settings';

-- ================================================================
-- 0. DOMAIN ENTITY TYPES
-- ================================================================

CREATE TABLE domain_entity_types (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    domain_id UUID NOT NULL REFERENCES domains(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    display_name VARCHAR(255) NOT NULL,
    description TEXT,
    icon VARCHAR(100),
    color VARCHAR(20),
    validation_rules JSONB DEFAULT '{}',
    extraction_prompt TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(domain_id, name)
);

CREATE INDEX idx_domain_entity_types_domain ON domain_entity_types(domain_id);

COMMENT ON TABLE domain_entity_types IS 'Domain-specific entity type definitions';

-- ================================================================
-- 0. DOMAIN RELATIONSHIP TYPES
-- ================================================================

CREATE TABLE domain_relationship_types (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    domain_id UUID NOT NULL REFERENCES domains(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    display_name VARCHAR(255) NOT NULL,
    description TEXT,
    source_entity_type VARCHAR(255),
    target_entity_type VARCHAR(255),
    is_directional BOOLEAN DEFAULT TRUE,
    validation_rules JSONB DEFAULT '{}',
    extraction_prompt TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(domain_id, name)
);

CREATE INDEX idx_domain_relationship_types_domain ON domain_relationship_types(domain_id);

COMMENT ON TABLE domain_relationship_types IS 'Domain-specific relationship type definitions';

-- ================================================================
-- 1. CORE GRAPH (Nodes & Edges) - Updated with Domain Support
-- ================================================================

CREATE TABLE nodes (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name TEXT NOT NULL,
    type TEXT NOT NULL,
    description TEXT,
    
    -- Domain Support
    domain_id UUID REFERENCES domains(id) ON DELETE SET NULL,
    domain_entity_type_id UUID REFERENCES domain_entity_types(id) ON DELETE SET NULL,
    domain_attributes JSONB DEFAULT '{}',
    confidence FLOAT DEFAULT 1.0,
    source_document_ids UUID[] DEFAULT ARRAY[]::UUID[],
    
    -- Metadata
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    
    -- Vectors
    embedding vector(768),
    
    -- Constraints
    CONSTRAINT uq_nodes_name_type_domain UNIQUE (name, type, domain_id)
);

CREATE TABLE edges (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    source_id UUID NOT NULL REFERENCES nodes(id) ON DELETE CASCADE,
    target_id UUID NOT NULL REFERENCES nodes(id) ON DELETE CASCADE,
    type TEXT NOT NULL,
    description TEXT,
    
    -- Domain Support
    domain_id UUID REFERENCES domains(id) ON DELETE SET NULL,
    domain_relationship_type_id UUID REFERENCES domain_relationship_types(id) ON DELETE SET NULL,
    domain_attributes JSONB DEFAULT '{}',
    confidence FLOAT DEFAULT 1.0,
    
    -- Metadata
    weight FLOAT DEFAULT 1.0,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    
    -- Constraints
    CONSTRAINT uq_edges_source_target_type_domain UNIQUE (source_id, target_id, type, domain_id)
);

-- ================================================================
-- 2. CROSS-DOMAIN LINKS
-- ================================================================

CREATE TABLE cross_domain_links (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    source_node_id UUID NOT NULL REFERENCES nodes(id) ON DELETE CASCADE,
    target_node_id UUID NOT NULL REFERENCES nodes(id) ON DELETE CASCADE,
    source_domain_id UUID NOT NULL REFERENCES domains(id) ON DELETE CASCADE,
    target_domain_id UUID NOT NULL REFERENCES domains(id) ON DELETE CASCADE,
    link_type VARCHAR(255) NOT NULL,
    confidence FLOAT DEFAULT 0.8,
    verified BOOLEAN DEFAULT FALSE,
    verification_method VARCHAR(50),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(source_node_id, target_node_id, link_type)
);

CREATE INDEX idx_cross_links_source ON cross_domain_links(source_node_id);
CREATE INDEX idx_cross_links_target ON cross_domain_links(target_node_id);
CREATE INDEX idx_cross_links_verified ON cross_domain_links(verified) WHERE verified = FALSE;

COMMENT ON TABLE cross_domain_links IS 'Explicit links between entities in different domains';

-- ================================================================
-- 3. HIERARCHICAL COMMUNITIES (The "GraphRAG" Layer)
-- ================================================================

CREATE TABLE communities (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    level INTEGER NOT NULL,
    title TEXT NOT NULL,
    summary TEXT,
    full_content TEXT,
    
    -- Domain Support
    domain_id UUID REFERENCES domains(id) ON DELETE SET NULL,
    
    -- Vectors
    embedding vector(768),
    
    -- Metadata
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Mapping Nodes to Communities (Many-to-Many)
CREATE TABLE community_membership (
    community_id UUID NOT NULL REFERENCES communities(id) ON DELETE CASCADE,
    node_id UUID NOT NULL REFERENCES nodes(id) ON DELETE CASCADE,
    rank FLOAT DEFAULT 0.0,
    
    PRIMARY KEY (community_id, node_id)
);

-- Hierarchy (Community -> Parent Community)
CREATE TABLE community_hierarchy (
    child_id UUID NOT NULL REFERENCES communities(id) ON DELETE CASCADE,
    parent_id UUID NOT NULL REFERENCES communities(id) ON DELETE CASCADE,
    
    PRIMARY KEY (child_id, parent_id)
);

-- ================================================================
-- 4. TEMPORAL DATA (Events & Timelines)
-- ================================================================

CREATE TABLE events (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    node_id UUID REFERENCES nodes(id) ON DELETE CASCADE,
    description TEXT NOT NULL,
    timestamp TIMESTAMPTZ,
    raw_time_desc TEXT,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ================================================================
-- 5. INDEXES
-- ================================================================

-- Text Search (Trigram)
CREATE INDEX idx_nodes_name_trgm ON nodes USING GIN (name gin_trgm_ops);
CREATE INDEX idx_nodes_desc_fts ON nodes USING GIN (to_tsvector('english', description));
CREATE INDEX idx_communities_title_trgm ON communities USING GIN (title gin_trgm_ops);

-- Vector Search (HNSW)
CREATE INDEX idx_nodes_embedding ON nodes USING hnsw (embedding vector_cosine_ops);
CREATE INDEX idx_communities_embedding ON communities USING hnsw (embedding vector_cosine_ops);

-- Graph Traversal
CREATE INDEX idx_edges_source ON edges(source_id);
CREATE INDEX idx_edges_target ON edges(target_id);
CREATE INDEX idx_community_mem_node ON community_membership(node_id);
CREATE INDEX idx_community_mem_comm ON community_membership(community_id);

-- Domain Queries
CREATE INDEX idx_nodes_domain ON nodes(domain_id);
CREATE INDEX idx_edges_domain ON edges(domain_id);
CREATE INDEX idx_communities_domain ON communities(domain_id);
CREATE INDEX idx_nodes_domain_type ON nodes(domain_id, type);
CREATE INDEX idx_edges_domain_type ON edges(domain_id, type);
CREATE INDEX idx_nodes_source_docs ON nodes USING GIN(source_document_ids);

-- ================================================================
-- 6. UTILITY FUNCTIONS
-- ================================================================

-- Update timestamp
CREATE OR REPLACE FUNCTION update_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_nodes_modtime
    BEFORE UPDATE ON nodes
    FOR EACH ROW EXECUTE FUNCTION update_timestamp();

CREATE TRIGGER update_communities_modtime
    BEFORE UPDATE ON communities
    FOR EACH ROW EXECUTE FUNCTION update_timestamp();

CREATE TRIGGER update_domains_modtime
    BEFORE UPDATE ON domains
    FOR EACH ROW EXECUTE FUNCTION update_timestamp();

-- ================================================================
-- 7. DEFAULT DATA
-- ================================================================

-- Insert default AI Engineering Research domain
INSERT INTO domains (name, display_name, description, template_config, is_active)
VALUES (
    'ai_engineering_research',
    'AI Engineering Research',
    'Comprehensive knowledge base for AI engineering topics including LLM optimization, context engineering, autonomous agents, and performance benchmarking.',
    '{
        "entity_types": ["research_paper", "model_architecture", "technique", "benchmark", "hyperparameter", "dataset", "experiment", "tool_framework"],
        "relationship_types": ["cites", "proposes", "evaluates_on", "uses", "compares_with", "extends", "achieves"],
        "extraction_config": {
            "llm_model": "gemini-2.5-flash",
            "temperature": 0.1,
            "confidence_threshold": 0.7
        }
    }',
    TRUE
) ON CONFLICT (name) DO NOTHING;

-- Insert AI Engineering entity types
DO $$
DECLARE
    domain_uuid UUID;
BEGIN
    SELECT id INTO domain_uuid FROM domains WHERE name = 'ai_engineering_research';
    
    INSERT INTO domain_entity_types (domain_id, name, display_name, description, icon, color, extraction_prompt)
    VALUES
        (domain_uuid, 'research_paper', 'Research Paper', 'Academic or technical research paper on AI engineering topics', 'article', '#4285F4', 'Extract research paper details including title, all authors, publication date, abstract, arXiv ID, GitHub URL, and publication venue.'),
        (domain_uuid, 'model_architecture', 'Model Architecture', 'Neural network architecture or model design for AI systems', 'architecture', '#34A853', 'Extract AI model architecture details including name, type, parameters, layers, context length, and training data.'),
        (domain_uuid, 'technique', 'Technique', 'Machine learning or AI engineering technique, method, or algorithm', 'psychology', '#FBBC05', 'Extract ML/AI techniques including name, category, description, advantages, and limitations.'),
        (domain_uuid, 'benchmark', 'Benchmark', 'Evaluation benchmark, dataset, or performance metric', 'speed', '#EA4335', 'Extract benchmark details including name, metric type, task category, and evaluation methodology.'),
        (domain_uuid, 'hyperparameter', 'Hyperparameter', 'Training or inference hyperparameter for AI models', 'tuning', '#9334E6', 'Extract hyperparameters including name, typical value, context, and impact on performance.'),
        (domain_uuid, 'dataset', 'Dataset', 'Training, evaluation, or fine-tuning dataset', 'dataset', '#00BCD4', 'Extract dataset details including name, size, type, source, and license.'),
        (domain_uuid, 'experiment', 'Experiment', 'Experimental setup, configuration, or result from research', 'science', '#FF6D01', 'Extract experimental details including name, objective, setup, results, and conclusions.'),
        (domain_uuid, 'tool_framework', 'Tool or Framework', 'Software tool, library, or framework for AI development', 'code', '#7B1FA2', 'Extract tool/framework details including name, type, version, description, and use cases.')
    ON CONFLICT (domain_id, name) DO NOTHING;
END $$;

-- Insert AI Engineering relationship types
DO $$
DECLARE
    domain_uuid UUID;
BEGIN
    SELECT id INTO domain_uuid FROM domains WHERE name = 'ai_engineering_research';
    
    INSERT INTO domain_relationship_types (domain_id, name, display_name, description, source_entity_type, target_entity_type, is_directional, extraction_prompt)
    VALUES
        (domain_uuid, 'cites', 'Cites', 'Paper A cites Paper B in its references', 'research_paper', 'research_paper', TRUE, 'Identify citation relationships between research papers.'),
        (domain_uuid, 'proposes', 'Proposes', 'Paper A proposes or introduces Technique/Architecture/Model', 'research_paper', 'model_architecture', TRUE, 'Identify when a paper proposes new techniques or architectures.'),
        (domain_uuid, 'evaluates_on', 'Evaluates On', 'Model/Technique is evaluated on Benchmark/Dataset', 'model_architecture', 'benchmark', TRUE, 'Identify evaluation relationships between models and benchmarks.'),
        (domain_uuid, 'uses', 'Uses', 'Model/Technique uses/incorporates other Technique/Dataset/Tool', 'model_architecture', 'technique', TRUE, 'Identify usage relationships where a model incorporates other components.'),
        (domain_uuid, 'compares_with', 'Compares With', 'Model/Technique is compared with another', 'model_architecture', 'model_architecture', FALSE, 'Identify comparative relationships between models.'),
        (domain_uuid, 'extends', 'Extends', 'Model/Technique extends or builds upon another', 'model_architecture', 'model_architecture', TRUE, 'Identify extension relationships where one builds on another.'),
        (domain_uuid, 'achieves', 'Achieves', 'Experiment/Model achieves performance on Benchmark', 'experiment', 'benchmark', TRUE, 'Identify performance achievements.')
    ON CONFLICT (domain_id, name) DO NOTHING;
END $$;

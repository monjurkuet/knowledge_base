-- ================================================================
-- MULTI-DOMAIN EXTENSION MIGRATION
-- Add multi-domain support to existing Knowledge Base schema
-- Migration: v1.0 → v2.0
-- ================================================================
-- This migration adds:
-- 1. Domains table for multi-domain support
-- 2. Domain-specific entity and relationship type tables
-- 3. Domain columns to existing nodes and edges tables
-- 4. Cross-domain linking table
-- 5. Indexes for domain-based queries
-- ================================================================

BEGIN;

-- ================================================================
-- 1. DOMAINS TABLE
-- Stores domain configurations for multi-domain support
-- ================================================================

CREATE TABLE IF NOT EXISTS domains (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) UNIQUE NOT NULL,
    display_name VARCHAR(255) NOT NULL,
    description TEXT,
    template_config JSONB NOT NULL DEFAULT '{}',
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Index for active domain lookups
CREATE INDEX IF NOT EXISTS idx_domains_active ON domains(is_active) WHERE is_active = TRUE;

-- Index for name lookups
CREATE INDEX IF NOT EXISTS idx_domains_name ON domains(name);

COMMENT ON TABLE domains IS 'Stores domain configurations for multi-domain knowledge base support';
COMMENT ON COLUMN domains.name IS 'Unique internal name (snake_case)';
COMMENT ON COLUMN domains.display_name IS 'Human-readable name';
COMMENT ON COLUMN domains.template_config IS 'JSON configuration for domain-specific settings';
COMMENT ON COLUMN domains.is_active IS 'Soft delete flag for domain versioning';

-- ================================================================
-- 2. DOMAIN ENTITY TYPES
-- Domain-specific entity type definitions
-- ================================================================

CREATE TABLE IF NOT EXISTS domain_entity_types (
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

-- Index for domain-based entity type lookups
CREATE INDEX IF NOT EXISTS idx_domain_entity_types_domain ON domain_entity_types(domain_id);

COMMENT ON TABLE domain_entity_types IS 'Domain-specific entity type definitions';
COMMENT ON COLUMN domain_entity_types.domain_id IS 'Reference to parent domain';
COMMENT ON COLUMN domain_entity_types.name IS 'Internal name (snake_case)';
COMMENT ON COLUMN domain_entity_types.icon IS 'UI icon identifier';
COMMENT ON COLUMN domain_entity_types.color IS 'UI color hex code';
COMMENT ON COLUMN domain_entity_types.validation_rules IS 'Pydantic validation rules in JSON';
COMMENT ON COLUMN domain_entity_types.extraction_prompt IS 'LLM prompt for extracting this entity type';

-- ================================================================
-- 3. DOMAIN RELATIONSHIP TYPES
-- Domain-specific relationship type definitions
-- ================================================================

CREATE TABLE IF NOT EXISTS domain_relationship_types (
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

-- Index for domain-based relationship type lookups
CREATE INDEX IF NOT EXISTS idx_domain_relationship_types_domain ON domain_relationship_types(domain_id);

COMMENT ON TABLE domain_relationship_types IS 'Domain-specific relationship type definitions';
COMMENT ON COLUMN domain_relationship_types.domain_id IS 'Reference to parent domain';
COMMENT ON COLUMN domain_relationship_types.name IS 'Internal name (snake_case)';
COMMENT ON COLUMN domain_relationship_types.source_entity_type IS 'Allowed source entity type name';
COMMENT ON COLUMN domain_relationship_types.target_entity_type IS 'Allowed target entity type name';
COMMENT ON COLUMN domain_relationship_types.is_directional IS 'Whether relationship has direction';

-- ================================================================
-- 4. ADD DOMAIN COLUMNS TO NODES TABLE
-- Enable nodes to belong to specific domains
-- ================================================================

-- Add domain_id column if not exists
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'nodes' AND column_name = 'domain_id'
    ) THEN
        ALTER TABLE nodes ADD COLUMN domain_id UUID REFERENCES domains(id) ON DELETE SET NULL;
    END IF;
END $$;

-- Add domain_entity_type_id column if not exists
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'nodes' AND column_name = 'domain_entity_type_id'
    ) THEN
        ALTER TABLE nodes ADD COLUMN domain_entity_type_id UUID REFERENCES domain_entity_types(id) ON DELETE SET NULL;
    END IF;
END $$;

-- Add domain_attributes column if not exists
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'nodes' AND column_name = 'domain_attributes'
    ) THEN
        ALTER TABLE nodes ADD COLUMN domain_attributes JSONB DEFAULT '{}';
    END IF;
END $$;

-- Add confidence column if not exists (for extraction quality tracking)
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'nodes' AND column_name = 'confidence'
    ) THEN
        ALTER TABLE nodes ADD COLUMN confidence FLOAT DEFAULT 1.0;
    END IF;
END $$;

-- Add source_document_ids column if not exists
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'nodes' AND column_name = 'source_document_ids'
    ) THEN
        ALTER TABLE nodes ADD COLUMN source_document_ids UUID[] DEFAULT ARRAY[]::UUID[];
    END IF;
END $$;

COMMENT ON COLUMN nodes.domain_id IS 'Domain this node belongs to';
COMMENT ON COLUMN nodes.domain_entity_type_id IS 'Domain-specific entity type';
COMMENT ON COLUMN nodes.domain_attributes IS 'Domain-specific metadata';
COMMENT ON COLUMN nodes.confidence IS 'Extraction confidence score (0-1)';
COMMENT ON COLUMN nodes.source_document_ids IS 'Array of source document IDs';

-- ================================================================
-- 5. ADD DOMAIN COLUMNS TO EDGES TABLE
-- Enable edges to belong to specific domains
-- ================================================================

-- Add domain_id column if not exists
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'edges' AND column_name = 'domain_id'
    ) THEN
        ALTER TABLE edges ADD COLUMN domain_id UUID REFERENCES domains(id) ON DELETE SET NULL;
    END IF;
END $$;

-- Add domain_relationship_type_id column if not exists
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'edges' AND column_name = 'domain_relationship_type_id'
    ) THEN
        ALTER TABLE edges ADD COLUMN domain_relationship_type_id UUID REFERENCES domain_relationship_types(id) ON DELETE SET NULL;
    END IF;
END $$;

-- Add domain_attributes column if not exists
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'edges' AND column_name = 'domain_attributes'
    ) THEN
        ALTER TABLE edges ADD COLUMN domain_attributes JSONB DEFAULT '{}';
    END IF;
END $$;

-- Add confidence column if not exists
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'edges' AND column_name = 'confidence'
    ) THEN
        ALTER TABLE edges ADD COLUMN confidence FLOAT DEFAULT 1.0;
    END IF;
END $$;

COMMENT ON COLUMN edges.domain_id IS 'Domain this edge belongs to';
COMMENT ON COLUMN edges.domain_relationship_type_id IS 'Domain-specific relationship type';
COMMENT ON COLUMN edges.domain_attributes IS 'Domain-specific metadata';
COMMENT ON COLUMN edges.confidence IS 'Extraction confidence score (0-1)';

-- ================================================================
-- 6. CROSS-DOMAIN LINKS TABLE
-- Explicit connections between entities in different domains
-- ================================================================

CREATE TABLE IF NOT EXISTS cross_domain_links (
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

-- Indexes for cross-domain queries
CREATE INDEX IF NOT EXISTS idx_cross_links_source ON cross_domain_links(source_node_id);
CREATE INDEX IF NOT EXISTS idx_cross_links_target ON cross_domain_links(target_node_id);
CREATE INDEX IF NOT EXISTS idx_cross_links_source_domain ON cross_domain_links(source_domain_id);
CREATE INDEX IF NOT EXISTS idx_cross_links_target_domain ON cross_domain_links(target_domain_id);
CREATE INDEX IF NOT EXISTS idx_cross_links_verified ON cross_domain_links(verified) WHERE verified = FALSE;

COMMENT ON TABLE cross_domain_links IS 'Explicit links between entities in different domains';
COMMENT ON COLUMN cross_domain_links.link_type IS 'Type of cross-domain connection';
COMMENT ON COLUMN cross_domain_links.confidence IS 'Confidence score for the link (0-1)';
COMMENT ON COLUMN cross_domain_links.verified IS 'Whether link has been manually verified';
COMMENT ON COLUMN cross_domain_links.verification_method IS 'Method used to discover link (vector, llm, manual)';

-- ================================================================
-- 7. INDEXES FOR DOMAIN QUERIES
-- Optimize common domain-based query patterns
-- ================================================================

-- Domain-based node queries
CREATE INDEX IF NOT EXISTS idx_nodes_domain ON nodes(domain_id);
CREATE INDEX IF NOT EXISTS idx_nodes_domain_type ON nodes(domain_id, type);
CREATE INDEX IF NOT EXISTS idx_nodes_domain_entity_type ON nodes(domain_id, domain_entity_type_id);

-- Domain-based edge queries
CREATE INDEX IF NOT EXISTS idx_edges_domain ON edges(domain_id);
CREATE INDEX IF NOT EXISTS idx_edges_domain_type ON edges(domain_id, type);

-- Source document lookups
CREATE INDEX IF NOT EXISTS idx_nodes_source_docs ON nodes USING GIN(source_document_ids);

-- Vector similarity search for domain-specific queries
-- Note: This uses the existing HNSW index but enables domain filtering
--CREATE INDEX IF NOT EXISTS idx_nodes_embedding_domain ON nodes USING hnsw (embedding vector_cosine_ops) WHERE domain_id IS NOT NULL;

COMMENT ON INDEX idx_nodes_domain IS 'Optimize queries filtering by domain';
COMMENT ON INDEX idx_nodes_source_docs IS 'Optimize document-to-node lookups';

-- ================================================================
-- 8. UPDATE FUNCTIONS AND TRIGGERS
-- ================================================================

-- Updated timestamp function (already exists, but ensure it covers new tables)
CREATE OR REPLACE FUNCTION update_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply to new domain tables
DROP TRIGGER IF EXISTS update_domains_modtime ON domains;
CREATE TRIGGER update_domains_modtime
    BEFORE UPDATE ON domains
    FOR EACH ROW EXECUTE FUNCTION update_timestamp();

DROP TRIGGER IF EXISTS update_domain_entity_types_modtime ON domain_entity_types;
CREATE TRIGGER update_domain_entity_types_modtime
    BEFORE UPDATE ON domain_entity_types
    FOR EACH ROW EXECUTE FUNCTION update_timestamp();

DROP TRIGGER IF EXISTS update_domain_relationship_types_modtime ON domain_relationship_types;
CREATE TRIGGER update_domain_relationship_types_modtime
    BEFORE UPDATE ON domain_relationship_types
    FOR EACH ROW EXECUTE FUNCTION update_timestamp();

-- ================================================================
-- 9. DEFAULT DOMAINS
-- Insert default domain configurations
-- ================================================================

-- Insert default AI Engineering Research domain if not exists
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
        },
        "ui_config": {
            "color_scheme": {
                "primary": "#4285F4",
                "background": "#FFFFFF"
            }
        }
    }',
    TRUE
) ON CONFLICT (name) DO NOTHING;

-- Get the domain ID for entity type insertion
DO $$
DECLARE
    domain_uuid UUID;
BEGIN
    SELECT id INTO domain_uuid FROM domains WHERE name = 'ai_engineering_research';
    
    IF domain_uuid IS NOT NULL THEN
        -- Insert AI Engineering entity types
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

        -- Insert AI Engineering relationship types
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
    END IF;
END $$;

COMMIT;

-- ================================================================
-- VERIFICATION QUERIES
-- Run these to verify the migration was successful
-- ================================================================

-- Check domains table
-- SELECT * FROM domains;

-- Check entity types for AI Engineering domain
-- SELECT * FROM domain_entity_types WHERE domain_id = (SELECT id FROM domains WHERE name = 'ai_engineering_research');

-- Check relationship types for AI Engineering domain
-- SELECT * FROM domain_relationship_types WHERE domain_id = (SELECT id FROM domains WHERE name = 'ai_engineering_research');

-- Verify new columns on nodes table
-- SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'nodes' ORDER BY ordinal_position;

-- Verify new columns on edges table
-- SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'edges' ORDER BY ordinal_position;

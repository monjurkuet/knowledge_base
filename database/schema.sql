-- ================================================================
-- KNOWLEDGE BASE SCHEMA (High-Fidelity GraphRAG) v2.0
-- ================================================================
-- Multi-Domain Knowledge Base with:
-- 1. Hybrid Search (Vector + Graph)
-- 2. Hierarchical Community Detection (Leiden)
-- 3. Recursive Summarization
-- 4. AI-Managed Multi-Domain Support
-- ================================================================

-- Extensions
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS pg_trgm;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ================================================================
-- 0. DOMAINS (AI-Managed Multi-Domain Support)
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

COMMENT ON TABLE domains IS 'Stores domain configurations for AI-managed multi-domain knowledge base support';
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
    synonyms JSONB DEFAULT '[]'::jsonb,
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
    synonyms JSONB DEFAULT '[]'::jsonb,
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
    created_at TIMESTAMPTZ DEFAULT NOW(),
    CONSTRAINT uq_events_unique UNIQUE (node_id, description, raw_time_desc)
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

-- Insert default General Knowledge domain (AI-managed, not hardcoded to specific topic)
INSERT INTO domains (name, display_name, description, template_config, is_active)
VALUES (
    'general_knowledge',
    'General Knowledge',
    'Default domain for general knowledge base content. AI will automatically create specialized domains based on content analysis.',
    '{
        "entity_types": ["person", "organization", "location", "concept", "event", "publication", "project", "technology"],
        "relationship_types": ["works_at", "located_in", "related_to", "part_of", "causes", "influences", "collaborates_with", "competes_with"],
        "extraction_config": {
            "llm_model": "gemini-2.5-flash",
            "temperature": 0.1,
            "confidence_threshold": 0.7
        }
    }',
    TRUE
) ON CONFLICT (name) DO NOTHING;

-- Insert General Knowledge entity types
DO $$
DECLARE
    domain_uuid UUID;
BEGIN
    SELECT id INTO domain_uuid FROM domains WHERE name = 'general_knowledge';
    
    INSERT INTO domain_entity_types (domain_id, name, display_name, description, icon, color, extraction_prompt)
    VALUES
        (domain_uuid, 'person', 'Person', 'Individual person or character', 'person', '#4285F4', 'Extract person details including full name, role, organization, and key attributes.'),
        (domain_uuid, 'organization', 'Organization', 'Company, institution, or group', 'business', '#34A853', 'Extract organization details including name, type, industry, and key characteristics.'),
        (domain_uuid, 'location', 'Location', 'Geographic location, city, or place', 'location_on', '#FBBC05', 'Extract location details including name, type, country, and relevant context.'),
        (domain_uuid, 'concept', 'Concept', 'Abstract idea, theory, or methodology', 'lightbulb', '#EA4335', 'Extract concept details including name, definition, applications, and related concepts.'),
        (domain_uuid, 'event', 'Event', 'Occurrence, meeting, or happening', 'event', '#9334E6', 'Extract event details including name, date, participants, and significance.'),
        (domain_uuid, 'publication', 'Publication', 'Book, paper, article, or report', 'article', '#00BCD4', 'Extract publication details including title, authors, date, and key findings.'),
        (domain_uuid, 'project', 'Project', 'Initiative, program, or development effort', 'work', '#FF6D01', 'Extract project details including name, objectives, timeline, and outcomes.'),
        (domain_uuid, 'technology', 'Technology', 'Tool, system, or technical innovation', 'build', '#7B1FA2', 'Extract technology details including name, purpose, features, and applications.')
    ON CONFLICT (domain_id, name) DO NOTHING;
END $$;

-- Insert General Knowledge relationship types
DO $$
DECLARE
    domain_uuid UUID;
BEGIN
    SELECT id INTO domain_uuid FROM domains WHERE name = 'general_knowledge';
    
    INSERT INTO domain_relationship_types (domain_id, name, display_name, description, source_entity_type, target_entity_type, is_directional, extraction_prompt)
    VALUES
        (domain_uuid, 'works_at', 'Works At', 'Person works at Organization', 'person', 'organization', TRUE, 'Identify employment relationships between people and organizations.'),
        (domain_uuid, 'located_in', 'Located In', 'Entity is located in Location', 'organization', 'location', TRUE, 'Identify geographic locations of organizations or entities.'),
        (domain_uuid, 'related_to', 'Related To', 'General relationship between entities', NULL, NULL, FALSE, 'Identify general relationships between any entities.'),
        (domain_uuid, 'part_of', 'Part Of', 'Entity is part of another entity', NULL, NULL, TRUE, 'Identify hierarchical or compositional relationships.'),
        (domain_uuid, 'causes', 'Causes', 'One entity causes another', NULL, NULL, TRUE, 'Identify causal relationships between events or concepts.'),
        (domain_uuid, 'influences', 'Influences', 'One entity influences another', NULL, NULL, TRUE, 'Identify influence relationships between entities.'),
        (domain_uuid, 'collaborates_with', 'Collaborates With', 'Entities collaborate or work together', NULL, NULL, FALSE, 'Identify collaboration relationships between people or organizations.'),
        (domain_uuid, 'competes_with', 'Competes With', 'Entities are competitors', 'organization', 'organization', FALSE, 'Identify competitive relationships between organizations.')
    ON CONFLICT (domain_id, name) DO NOTHING;
END $$;

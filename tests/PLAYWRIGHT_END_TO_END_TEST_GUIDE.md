# Playwright End-to-End Testing Guide for Knowledge Base GraphRAG System

## Overview
This guide provides a comprehensive end-to-end testing procedure using Playwright to verify all core features of the Knowledge Base GraphRAG system. The test validates the complete pipeline from database cleanup through data ingestion, visualization, search, and community analysis.

## Prerequisites
- Streamlit UI running on port 8505: `uv run streamlit run app.py --server.port=8505`
- API server running on port 8000: `uv run kb-server`
- PostgreSQL database with `agentzero` superuser access
- Playwright browser automation capabilities enabled

## Test Procedure

### Step 1: Database Cleanup
Before starting any test, ensure the database is clean:

```bash
# Clean all tables and reset sequences
psql -U agentzero -d knowledge_base -c "TRUNCATE TABLE nodes, edges, communities, community_membership, events, community_hierarchy RESTART IDENTITY CASCADE;"

# Verify empty state
psql -U agentzero -d knowledge_base -c "SELECT COUNT(*) FROM nodes; SELECT COUNT(*) FROM edges; SELECT COUNT(*) FROM communities;"
```

Expected result: All counts should be 0.

### Step 2: Create Comprehensive Test Data
Create a test document that covers all entity types and relationships to thoroughly validate the system:

```text
# [YOUR COMPREHENSIVE TEST DOCUMENT]
Include diverse entities:
- People (with name variations for resolution testing)
- Organizations (companies, universities, institutions)
- Locations (cities, countries, facilities)
- Concepts (technical terms, methodologies, theories)
- Events (temporal occurrences with dates)
- Publications (journals, papers, reports)
- Projects (initiatives, programs, research projects)

Include relationships:
- Employment relationships (WORKS_AT)
- Authorship relationships (AUTHORED)
- Leadership relationships (LEADS)
- Hierarchical relationships (PART_OF)
- Funding relationships (FUNDED_BY)
- Collaboration relationships (COLLABORATES_WITH)

Include temporal events:
- Specific dates and time periods
- Sequential events showing progression
- Future planned events

Include community themes:
- Multiple overlapping topics
- Cross-domain relationships
- Hierarchical structures (micro → macro communities)

Include rich contextual descriptions:
- Detailed role descriptions
- Technical specifications
- Strategic context
- Historical background
- Future implications
```

### Step 3: Playwright Browser Setup
Configure Playwright to run in non-headless mode for visual verification:

```python
# Ensure browser is visible for manual inspection
# Use browser_snapshot() frequently to verify page state
# Take screenshots at key milestones for documentation
```

### Step 4: Navigate to Streamlit UI
- Navigate to `http://localhost:8505`
- Verify page loads with title "Knowledge Base Explorer"
- Confirm dashboard shows all statistics as 0 (empty database state)

### Step 5: Ingest Test Data
1. **Navigate to Ingest tab**
   - Click "📄 Ingest" tab
   - Verify file upload interface is visible

2. **Upload test file**
   - Click "Browse files" button
   - Upload your comprehensive test document
   - Verify file appears in upload list

3. **Start ingestion process**
   - Click "🚀 Ingest Content" button
   - Verify WebSocket connection establishes successfully
   - Monitor real-time log messages for pipeline progress

4. **Monitor pipeline stages**
   - Stage 1: Entity and relationship extraction
   - Stage 2: Event extraction
   - Stage 3: Hybrid entity resolution and storage
   - Stage 4: Community detection
   - Stage 5: Recursive summarization
   - Final confirmation: "✅ === Pipeline Complete ==="

### Step 6: Verify Dashboard Statistics
After ingestion completes:
- Refresh the page or navigate back to Dashboard
- Verify statistics match expected counts:
  - Nodes: [expected count]
  - Edges: [expected count] 
  - Communities: [expected count]
  - Events: [expected count]

### Step 7: Test Knowledge Graph Visualization
1. **Navigate to Knowledge Graph tab**
   - Verify interactive Plotly graph renders
   - Confirm all nodes are displayed with proper labels and types

2. **Verify node type coloring**
   - People: Red nodes
   - Organizations: Green nodes  
   - Locations: Blue nodes
   - Concepts: Yellow nodes
   - Events: Orange nodes
   - Publications: Purple nodes
   - Projects: Green nodes

3. **Test graph controls**
   - Zoom in/out functionality
   - Pan functionality
   - Reset axes
   - Fullscreen mode
   - Download PNG capability

4. **Test community expanders**
   - Click each community to expand
   - Verify intelligent, context-rich summaries
   - Confirm node counts match expectations
   - Check that summaries capture community essence

### Step 8: Test Semantic Search
1. **Navigate to Search tab**
   - Verify search input field is functional

2. **Perform multiple search queries**
   - Broad terms: "quantum", "research", "technology"
   - Specific entities: "Dr. Elena Vance", "TechCorp", "Nature Quantum Physics"
   - Relationship-based: "collaboration", "funding", "leadership"
   - Temporal: "2026", "January", "future"

3. **Verify search results**
   - Correct number of results found
   - Type-based emoji indicators (👤, 🏢, 📋, 💡, 📚, 📍, 📅)
   - Rich contextual descriptions extracted from source
   - Proper entity type classification
   - Relevant results ranked appropriately

### Step 9: Test Additional Features
1. **Dashboard filters**
   - Test "Max Nodes to Display" slider
   - Test "Filter by Node Type" functionality
   - Verify "Show Node Labels" checkbox works

2. **Real-time updates**
   - Perform second ingestion while monitoring
   - Verify WebSocket updates refresh statistics automatically
   - Confirm no page reload required

3. **Error handling**
   - Test invalid file uploads
   - Test empty text ingestion
   - Verify graceful error messages

### Step 10: Validation Checklist
Ensure all these features work correctly:

#### ✅ Core Pipeline
- [ ] Entity extraction accuracy
- [ ] Entity resolution (deduplication) working
- [ ] Relationship extraction completeness
- [ ] Event extraction with temporal context
- [ ] Community detection quality
- [ ] Recursive summarization intelligence

#### ✅ UI/UX Features
- [ ] Interactive graph visualization
- [ ] Responsive design across tabs
- [ ] Real-time progress feedback
- [ ] Intuitive navigation
- [ ] Clear error messaging
- [ ] Professional appearance

#### ✅ Search Capabilities
- [ ] Semantic search relevance
- [ ] Rich result descriptions
- [ ] Type-based categorization
- [ ] Emoji indicators working
- [ ] Query flexibility

#### ✅ Data Integrity
- [ ] No data loss during ingestion
- [ ] Proper UUID generation
- [ ] Consistent entity linking
- [ ] Accurate relationship mapping
- [ ] Valid community memberships

#### ✅ Performance
- [ ] Reasonable ingestion time
- [ ] Responsive UI during operations
- [ ] Efficient graph rendering
- [ ] Fast search responses
- [ ] Smooth WebSocket communication

## Expected Test Data Structure
Your test document should include these elements for comprehensive validation:

### Entity Types Coverage
- **People**: 3-5 individuals with role descriptions
- **Organizations**: 3-5 companies/institutions with context
- **Locations**: 1-2 geographic locations
- **Concepts**: 3-5 technical concepts or methodologies
- **Events**: 2-3 temporal events with dates
- **Publications**: 1-2 academic or industry publications
- **Projects**: 1-2 research or development initiatives

### Relationship Patterns
- **Hierarchical**: Parent-child organizational relationships
- **Collaborative**: Partnership and collaboration relationships  
- **Employment**: Person-to-organization employment
- **Authorship**: Person-to-publication authorship
- **Funding**: Organization-to-project funding
- **Temporal**: Event-to-entity chronological relationships

### Community Complexity
- **Overlapping themes**: Entities appearing in multiple contexts
- **Cross-domain connections**: Links between different entity types
- **Hierarchical structure**: Micro-communities within macro-themes
- **Strategic narratives**: Communities that tell coherent stories

## Common Issues to Watch For
- **Entity resolution failures**: Duplicate entities not properly merged
- **Missing relationships**: Extracted entities without proper connections
- **Community fragmentation**: Related entities split into separate communities
- **Poor summarization**: Generic or inaccurate community summaries
- **Search relevance issues**: Irrelevant results or missing relevant ones
- **Performance bottlenecks**: Slow ingestion or unresponsive UI
- **WebSocket disconnections**: Lost real-time updates during long operations

## Success Criteria
The test passes when:
1. **Database cleanup** completes successfully
2. **Ingestion pipeline** runs without errors and completes all stages
3. **All expected entities** are extracted and stored correctly
4. **Knowledge graph** displays all nodes with proper types and relationships
5. **Communities** are detected intelligently with meaningful summaries
6. **Search functionality** returns relevant, well-described results
7. **UI remains responsive** throughout the entire process
8. **Real-time updates** work correctly via WebSocket
9. **All statistics** match expected counts
10. **No data corruption** or integrity issues detected

## Automation Notes
- Use `browser_snapshot()` frequently to capture page state
- Take screenshots at key milestones for visual verification
- Monitor console messages for JavaScript errors
- Check network requests for API call failures
- Verify WebSocket connection stability during long operations
- Test both file upload and direct text ingestion methods

## Enhancement Opportunities
Consider adding these improvements to future tests:
- **Multi-document ingestion**: Test incremental updates and cross-document entity resolution
- **Large dataset testing**: Validate performance with 1000+ entities
- **Edge case scenarios**: Test with malformed text, special characters, very long documents
- **Mobile responsiveness**: Test UI on different screen sizes
- **Accessibility testing**: Verify screen reader compatibility
- **Internationalization**: Test with non-English content
- **Security testing**: Validate input sanitization and error handling
- **Load testing**: Simulate multiple concurrent users
- **Recovery testing**: Test system behavior after interruptions

## Sample Test Document Template
Use this template structure for consistent testing:

```text
# [Domain/Industry] Research at [Organization]

## Executive Summary
[Brief overview highlighting key achievements and personnel]

## Key Personnel
- **[Full Name]**: [Role] at [Organization] (formerly known as [Alias])
- **[Full Name]**: [Role], previously worked at [Previous Organization]
- **[Full Name]**: [Role], joined from [Institution]

## Major Achievements
On [Date], [Organization] announced [Achievement]. This breakthrough was published in [Publication] and represents a significant milestone.

## Technical Details
[Detailed technical description with specific methodologies, tools, and approaches]

## Strategic Partnerships
[Organization] has established partnerships with [Partners] for [Purpose].

## Competitive Landscape
[Competitors] recently announced [Their Achievement], but [Your Organization]'s approach is superior due to [Reasons].

## Future Outlook
[Organization] plans to [Future Goals] by [Timeline].

## Funding and Investment
[Organization] has committed [$Amount] in additional funding for [Period].

## Publication References
- [Citation 1]
- [Citation 2]  
- [Citation 3]
```

This comprehensive testing guide ensures thorough validation of your Knowledge Base GraphRAG system's end-to-end functionality.
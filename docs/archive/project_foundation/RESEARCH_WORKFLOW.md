# Research Workflow
## Multi-Domain Knowledge Base GraphRAG System

## Overview

This document defines the manual research paper ingestion workflow for the AI Engineering Research domain. The workflow prioritizes quality over quantity, allowing researchers to build a curated, high-value knowledge base.

---

## Folder Structure

### Recommended Organization

```
knowledge_base/
├── research_papers/
│   ├── ai_engineering/
│   │   ├── llm_optimization/
│   │   │   ├── scaling_laws/
│   │   │   │   ├── papers/
│   │   │   │   ├── notes/
│   │   │   │   └── summary.md
│   │   │   ├── context_engineering/
│   │   │   │   ├── papers/
│   │   │   │   ├── notes/
│   │   │   │   └── summary.md
│   │   │   └── efficiency/
│   │   │       ├── papers/
│   │   │       ├── notes/
│   │   │       └── summary.md
│   │   ├── autonomous_agents/
│   │   │   ├── reasoning/
│   │   │   ├── planning/
│   │   │   └── tool_use/
│   │   └── benchmarks/
│   │       ├── evaluation/
│   │       └── performance/
│   └── personal/
│       ├── notes/
│       ├── drafts/
│       └── ideas/
└── docs/
    ├── project_foundation/
    │   ├── PROJECT_VISION.md
    │   ├── IMPLEMENTATION_PLAN.md
    │   ├── TECHNICAL_DECISIONS.md
    │   ├── DOMAIN_TEMPLATES.md
    │   ├── ARCHITECTURE.md
    │   ├── REASONING.md
    │   └── RESEARCH_WORKFLOW.md
    └── guides/
        ├── ingestion_guide.md
        └── analysis_guide.md
```

---

## Research Paper Ingestion Workflow

### Phase 1: Paper Selection

#### Criteria for Inclusion

1. **Relevance**: Directly relates to AI Engineering Research topics
2. **Quality**: Published in reputable venue or from trusted source
3. **Novelty**: Introduces new technique, analysis, or insight
4. **Impact**: Cited by other relevant work or shows strong results
5. **Personal Value**: Addresses specific research questions

#### Paper Categories

**Category A - Core Papers** (Must Ingest)
- Foundational papers in topic area
- Papers that define key concepts
- Highly cited influential work

**Category B - Important Papers** (Should Ingest)
- Significant experimental results
- Novel techniques or approaches
- Comparative analysis with other methods

**Category C - Supporting Papers** (Optional)
- Background and context
- Related work for comparison
- Technical details for implementation

#### Selection Checklist

```
□ Is this paper relevant to current research goals?
□ Is the source reputable (arXiv, top conference, trusted lab)?
□ Does it introduce new concepts or techniques?
□ Does it provide valuable experimental results?
□ Have I already covered similar content?
□ Is the paper readable and well-structured?
```

---

### Phase 2: Document Preparation

#### File Naming Convention

```
{paper_type}_{author_year}_{short_title}.{extension}
```

**Examples:**
- `core_vaswani_2017_attention_is_all_you_need.pdf`
- `imp_brown_2020_language_models_few_shot.pdf`
- `sup_hochreiter_1997_lstm.pdf`

**Paper Type Prefix:**
- `core_` - Core paper (Category A)
- `imp_` - Important paper (Category B)
- `sup_` - Supporting paper (Category C)
- `pers_` - Personal note or draft

#### File Format Requirements

**Supported Formats:**
- `.txt` - Plain text
- `.md` - Markdown
- `.pdf` - PDF (requires text extraction)
- `.html` - HTML documents

**PDF Processing:**
- Extract text content
- Preserve headings and structure
- Extract metadata (title, authors, year)

#### Metadata Preparation

Create a companion metadata file:

```
filename: core_vaswani_2017_attention_is_all_you_need.pdf
title: Attention Is All You Need
authors: Ashish Vaswani, Noam Shazeer, Niki Parmar, Jakob Uszkoreit,
         Llion Jones, Aidan N. Gomez, Lukasz Kaiser, Illia Polosukhin
year: 2017
venue: NeurIPS
category: core
topics: [transformer, attention, seq2seq]
abstract: |
  The dominant sequence transduction models are based on complex
  recurrent or convolutional neural networks that include an
  encoder and a decoder. The best performing models also connect
  the encoder and the decoder through an attention mechanism.
  We propose a new simple network architecture, the Transformer,
  based solely on attention mechanisms...
notes: |
  Key contributions:
  - Introduces self-attention mechanism
  - Removes recurrence entirely
  - Enables better parallelization
  - SOTA results on translation tasks
```

---

### Phase 3: Ingestion Process

#### Step 1: Upload to Knowledge Base

```bash
# Via CLI
uv run kb-pipeline research_papers/ai_engineering/llm_optimization/scaling_laws/core_kaplan_2021_scaling_laws.pdf

# Via API
POST /api/v1/ingest/file
{
  "file_path": "research_papers/ai_engineering/llm_optimization/scaling_laws/core_kaplan_2021_scaling_laws.pdf",
  "domain_id": "ai_engineering_research",
  "auto_categorize": true,
  "metadata": {
    "category": "core",
    "topics": ["scaling_laws", "compute_optimal"]
  }
}
```

#### Step 2: Processing Pipeline

```
File Upload
    │
    ▼
Text Extraction (if PDF)
    │
    ▼
Preprocessing (chunking, cleaning)
    │
    ▼
Domain Classification (auto or manual)
    │
    ▼
Entity Extraction (LLM)
    │
    ▼
Entity Resolution (deduplication)
    │
    ▼
Relationship Extraction
    │
    ▼
Graph Building
    │
    ▼
Community Detection
    │
    ▼
Summary Generation
```

#### Step 3: Review and Validate

**Automated Checks:**
- ✅ All required fields extracted
- ✅ No duplicate entities
- ✅ Valid entity types
- ✅ Reasonable confidence scores

**Manual Review Points:**
- [ ] Entity names are correct and consistent
- [ ] Relationships make sense
- [ ] No obvious extraction errors
- [ ] Paper is properly categorized

**Correction Interface:**

```
┌─────────────────────────────────────────────────┐
│  Extraction Review                              │
├─────────────────────────────────────────────────┤
│  Paper: Attention Is All You Need               │
│                                                 │
│  Extracted Entities:                            │
│  ┌─────────────────────────────────────────┐   │
│  │ ✓ Transformer [model_architecture]      │   │
│  │   Confidence: 0.95                       │   │
│  │   [Edit] [Merge] [Delete]               │   │
│  └─────────────────────────────────────────┘   │
│  ┌─────────────────────────────────────────┐   │
│  │ ✓ Self-Attention [technique]            │   │
│  │   Confidence: 0.92                       │   │
│  │   [Edit] [Merge] [Delete]               │   │
│  └─────────────────────────────────────────┘   │
│  ┌─────────────────────────────────────────┐   │
│  │ ⚠ Multi-Head Attention [technique]      │   │
│  │   Confidence: 0.67                       │   │
│  │   [Edit] [Merge] [Delete] [Confirm]     │   │
│  └─────────────────────────────────────────┘   │
│                                                 │
│  [Submit Corrections] [Approve as-is]           │
└─────────────────────────────────────────────────┘
```

---

### Phase 4: Annotation and Tagging

#### Manual Tags

Add tags to support organization and retrieval:

**Topic Tags:**
```
llm_optimization
context_engineering
autonomous_agents
performance_benchmarking
model_architecture
training_efficiency
inference_optimization
```

**Method Tags:**
```
transformer
attention_mechanism
moe
rlhf
cot
few_shot
scaling_laws
```

**Status Tags:**
```
#read
#to-read
#reading
#reference
#important
#follow-up
```

#### Annotation Examples

**In-Text Annotation:**

```markdown
# Paper Notes: Attention Is All You Need

## Key Insights

The Transformer architecture [[transformer]] represents a paradigm shift
from recurrent models. The key innovation is the self-attention mechanism
[[self_attention]] which allows modeling long-range dependencies.

## Critical Contributions

1. **Self-Attention**: Replaces recurrence with attention
   - Computation is parallelizable
   - Path length between any two positions is O(1)

2. **Multi-Head Attention**: Parallel attention layers
   - Each head learns different aspects
   - Combined for richer representation

## Connections to Other Work

- Related to [[attention_is_all_you_need]] by Bahdanau et al.
- Foundation for [[bert]] and [[gpt]] architectures
- Basis for [[vision_transformer]] extension

## Questions for Further Research

- How does this scale to extremely long sequences?
- Can we reduce the quadratic complexity?
```

#### Personal Notes Integration

Add researcher insights and connections:

```markdown
# Personal Notes

## Why This Paper Matters

This is the foundational paper that started the Transformer revolution.
Every major LLM today (GPT, Claude, Llama) is based on this architecture.

## Connections to My Work

Relevant to my research on efficient attention mechanisms.
Consider applying similar principles to [[efficient_attention]] techniques.

## Action Items

- [ ] Implement simplified Transformer
- [ ] Compare with LSTM baseline
- [ ] Test scaling behavior
```

---

### Phase 5: Quality Assurance

#### Quality Checklist

**Completeness:**
- [ ] Abstract extracted
- [ ] All authors captured
- [ ] Publication venue identified
- [ ] Key entities extracted
- [ ] Main relationships captured

**Accuracy:**
- [ ] Entity names are correct
- [ ] Relationships are valid
- [ ] No hallucinated information
- [ ] Confidence scores reasonable

**Consistency:**
- [ ] Naming conventions followed
- [ ] Entity types consistent
- [ ] No duplicate entities
- [ ] Proper cross-references

#### Quality Metrics

**Track Over Time:**
- Extraction accuracy (vs. manual)
- Entity coverage (percent of paper covered)
- Relationship density (edges per entity)
- Community quality (modularity score)

**Quality Thresholds:**
- Entity extraction accuracy: >85%
- Relationship extraction accuracy: >80%
- Entity coverage: >70% of paper content
- Duplicate rate: <5%

---

## Analysis Workflow

### Regular Analysis Sessions

#### Weekly Review

1. **New Papers Summary**
   - List newly ingested papers
   - Highlight key entities discovered
   - Note any important relationships

2. **Community Updates**
   - Review new communities formed
   - Check community assignments
   - Verify community summaries

3. **Insight Review**
   - Review generated insights
   - Mark as relevant/irrelevant
   - Add notes to valuable insights

#### Monthly Deep Analysis

1. **Trend Analysis**
   - Identify emerging topics
   - Track research evolution
   - Find gaps in coverage

2. **Cross-Paper Synthesis**
   - Find connections between papers
   - Identify conflicting findings
   - Build comprehensive topic summaries

3. **Research Roadmap**
   - Identify papers to add
   - Prioritize topics for deeper coverage
   - Set research directions

### Visualization and Reporting

#### Knowledge Graph View

```
Network Visualization Controls:
┌────────────────────────────────────────┐
│  [Zoom In] [Zoom Out] [Fit] [Export]  │
├────────────────────────────────────────┤
│  Filter by Type:                       │
│  ☑ Research Paper                      │
│  ☑ Model Architecture                  │
│  ☑ Technique                           │
│  ☑ Benchmark                           │
├────────────────────────────────────────┤
│  Filter by Time:                       │
│  [2024] [2023] [2022] [2021] [Older]   │
├────────────────────────────────────────┤
│  Highlight:                            │
│  ○ Selected Node                       │
│  ○ Connected Nodes                     │
│  ○ Same Type                           │
└────────────────────────────────────────┘
```

#### Analysis Dashboard

```
┌──────────────────────────────────────────────────────────────┐
│                    Research Dashboard                        │
├──────────────────────────────────────────────────────────────┤
│  Overview                                                      │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐       │
│  │   47     │ │   234    │ │   892    │ │   12     │       │
│  │ Papers   │ │ Entities │ │Relations │ │Communities│      │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘       │
│                                                               │
│  Recent Insights                                              │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ 🔥 Scaling laws show diminishing returns below       │   │
│  │    optimal compute allocation (Kaplan et al., 2021)  │   │
│  │    [View Details]                                    │   │
│  ├──────────────────────────────────────────────────────┤   │
│  │ 💡 New trend: mixture of experts architectures       │   │
│  │    showing promise for efficient scaling             │   │
│  │    [View Details]                                    │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                               │
│  Topic Distribution                                           │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ Transformer  ████████████████████  35%               │   │
│  │ Attention    ████████████████  28%                   │   │
│  │ Training     ████████████  22%                       │   │
│  │ Benchmarks   ████████  15%                           │   │
│  └──────────────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────────────┘
```

---

## Best Practices

### Research Workflow Tips

1. **Start with Core Papers**
   - Build foundation before expanding
   - Ensure good coverage of fundamental concepts
   - Quality over quantity

2. **Use Consistent Tagging**
   - Develop a personal tagging system
   - Apply tags consistently
   - Review and refine tags periodically

3. **Make Connections Explicit**
   - Link papers that cite each other
   - Note conceptual connections
   - Highlight conflicting findings

4. **Regular Review Sessions**
   - Schedule weekly review time
   - Update notes and annotations
   - Track research progress

5. **Document Insights Immediately**
   - Capture insights when discovered
   - Note the source and context
   - Return to insights for deeper analysis

### Common Workflow Patterns

#### Pattern 1: Deep Dive on Topic

```
1. Identify topic of interest
2. Find all papers on topic (ingest if new)
3. Tag with topic label
4. Run topic-specific analysis
5. Generate topic summary
6. Document gaps and questions
7. Search for additional papers
8. Iterate until satisfied
```

#### Pattern 2: Paper Comparison

```
1. Select 2-3 related papers
2. Ingest all papers
3. Compare entity extraction
4. Map relationship differences
5. Identify conflicting claims
6. Document comparison findings
7. Add to comparative analysis
```

#### Pattern 3: Trend Tracking

```
1. Set up time-based filter
2. Review papers by time period
3. Track entity emergence
4. Monitor relationship evolution
5. Generate trend visualization
6. Document observations
7. Project future directions
```

---

## Troubleshooting

### Common Issues

#### Issue: Poor Extraction Quality

**Symptoms:**
- Entities missing from paper
- Incorrect entity types
- Low confidence scores

**Solutions:**
1. Check PDF text extraction quality
2. Review domain configuration
3. Add manual corrections
4. Update extraction prompts

#### Issue: Duplicate Entities

**Symptoms:**
- Same concept appears multiple times
- Low deduplication rate

**Solutions:**
1. Check entity resolution thresholds
2. Review merge decisions
3. Manually merge duplicates
4. Update name normalization

#### Issue: Community Detection Issues

**Symptoms:**
- Unrelated entities grouped together
- Related entities in separate communities

**Solutions:**
1. Adjust resolution parameter
2. Check relationship weights
3. Review edge confidence scores
4. Manually adjust community assignments

#### Issue: Missing Cross-Domain Links

**Symptoms:**
- Related entities in different domains not connected

**Solutions:**
1. Run cross-domain discovery
2. Adjust confidence thresholds
3. Check entity attributes for matching
4. Add manual links

---

## Integration with Development

### Using Research in Development

The knowledge base can inform development decisions:

1. **Architecture Decisions**: Reference papers on techniques
2. **Performance Benchmarks**: Use benchmark results from papers
3. **Error Resolution**: Find papers on similar issues
4. **Optimization**: Apply techniques from research

### Documenting Research Applications

```markdown
# Research Application Notes

## Application: Attention Mechanism Implementation

**Research Basis:**
- [[attention_is_all_you_need]] - Original Transformer paper
- [[attention_bahdanau]] - Attention before Transformers

**Implementation Approach:**
- Multi-head attention as described in original paper
- Scaled dot-product attention for efficiency
- Positional encoding using RoPE

**Deviations from Research:**
- Simplified implementation for edge deployment
- Reduced number of heads for performance
- Trade-offs documented in code comments

**Results:**
- 15% improvement over baseline
- Details in [PR #123]
```

---

## Automation Opportunities

### Future Automation

While the current workflow is manual, these automations could be added:

1. **Auto-Tagging**: Use LLM to suggest tags based on content
2. **Related Paper Discovery**: Find similar papers based on entities
3. **Citation Tracking**: Monitor citations to ingested papers
4. **New Paper Alerts**: RSS or API integration for new publications
5. **Summary Generation**: Auto-generate paper summaries

### Recommended Manual Steps

Some steps should remain manual:

1. **Paper Selection**: Critical for quality control
2. **Final Review**: Human judgment for accuracy
3. **Insight Validation**: Expert verification needed
4. **Research Direction**: Strategic decisions by researcher

# Domain Templates
## Multi-Domain Knowledge Base GraphRAG System

## AI Engineering Research Domain Template

### Domain Configuration

```json
{
  "id": "ai_engineering_research",
  "name": "ai_engineering_research",
  "display_name": "AI Engineering Research",
  "description": "Comprehensive knowledge base for AI engineering topics including LLM optimization, context engineering, autonomous agents, and performance benchmarking. Supports research paper analysis, technique tracking, and cross-paper relationship discovery.",
  "entity_types": [],
  "relationship_types": [],
  "extraction_config": {},
  "analysis_config": {},
  "ui_config": {}
}
```

---

### Entity Types

#### 1. Research Paper
```json
{
  "name": "research_paper",
  "display_name": "Research Paper",
  "description": "Academic or technical research paper on AI engineering topics",
  "icon": "article",
  "color": "#4285F4",
  "validation_rules": {
    "required_fields": ["title", "authors", "publication_date"],
    "optional_fields": ["abstract", "arxiv_id", "github_url", "venue", "citation_count"]
  },
  "extraction_prompt": "Extract research paper details including title, all authors, publication date, abstract, arXiv ID (if available), GitHub repository URL (if available), and publication venue or conference name. Format as structured data.",
  "example_patterns": [
    "Attention Is All You Need (Vaswani et al., 2017)",
    "GPT-4 Technical Report (OpenAI, 2023)",
    "Llama 2: Open Foundation and Fine-Tuned Chat Models (Touvron et al., 2023)"
  ]
}
```

#### 2. Model Architecture
```json
{
  "name": "model_architecture",
  "display_name": "Model Architecture",
  "description": "Neural network architecture or model design for AI systems",
  "icon": "architecture",
  "color": "#34A853",
  "validation_rules": {
    "required_fields": ["name", "type"],
    "optional_fields": ["parameters", "layers", "context_length", "training_data"]
  },
  "extraction_prompt": "Extract AI model architecture details including architecture name, type (e.g., transformer, diffusion, mixture of experts), number of parameters, number of layers, maximum context length, and training data specifications. Include variants and notable configurations.",
  "example_patterns": [
    "Transformer architecture with 175B parameters",
    "Mixture of Experts with 8B active parameters",
    "Vision Transformer (ViT) with patch size 16x16"
  ]
}
```

#### 3. Technique
```json
{
  "name": "technique",
  "display_name": "Technique",
  "description": "Machine learning or AI engineering technique, method, or algorithm",
  "icon": "psychology",
  "color": "#FBBC05",
  "validation_rules": {
    "required_fields": ["name", "category"],
    "optional_fields": ["description", "advantages", "limitations", "complexity"]
  },
  "extraction_prompt": "Extract ML/AI techniques including the technique name, category (e.g., attention mechanism, regularization, optimization), brief description, key advantages, known limitations, and computational complexity. Distinguish between novel techniques and standard methods.",
  "example_patterns": [
    "RoPE (Rotary Position Embedding)",
    "Flash Attention for memory-efficient training",
    "Chain-of-Thought prompting"
  ]
}
```

#### 4. Benchmark
```json
{
  "name": "benchmark",
  "display_name": "Benchmark",
  "description": "Evaluation benchmark, dataset, or performance metric for AI systems",
  "icon": "speed",
  "color": "#EA4335",
  "validation_rules": {
    "required_fields": ["name", "metric_type"],
    "optional_fields": ["description", "task_type", "evaluation_method"]
  },
  "extraction_prompt": "Extract benchmark details including benchmark name, metric type (e.g., accuracy, F1, perplexity), task category (e.g., NLP, vision, reasoning), evaluation methodology, and any specific configurations or versions. Note which models have been evaluated on this benchmark.",
  "example_patterns": [
    "MMLU (Massive Multitask Language Understanding)",
    "HELM (Holistic Evaluation of Language Models)",
    "GPQA (Graduate-Level Google-Proof Q&A Benchmark)"
  ]
}
```

#### 5. Hyperparameter
```json
{
  "name": "hyperparameter",
  "display_name": "Hyperparameter",
  "description": "Training or inference hyperparameter for AI models",
  "icon": "tuning",
  "color": "#9334E6",
  "validation_rules": {
    "required_fields": ["name", "value", "context"],
    "optional_fields": ["range", "description", "impact"]
  },
  "extraction_prompt": "Extract hyperparameters including parameter name, typical or optimal value, the context/model it's used for, valid range or search space, brief description of what it controls, and impact on model performance. Note if values differ between training and inference.",
  "example_patterns": [
    "learning_rate=3e-4 for AdamW optimizer",
    "temperature=0.7 for text generation",
    "top_p=0.95 for nucleus sampling"
  ]
}
```

#### 6. Dataset
```json
{
  "name": "dataset",
  "display_name": "Dataset",
  "description": "Training, evaluation, or fine-tuning dataset",
  "icon": "dataset",
  "color": "#00BCD4",
  "validation_rules": {
    "required_fields": ["name", "size"],
    "optional_fields": ["description", "type", "source", "license"]
  },
  "extraction_prompt": "Extract dataset details including dataset name, size (number of tokens, samples, or files), type (training, validation, test, fine-tuning), data source or origin, license or access restrictions, and any preprocessing applied. Note if the dataset is publicly available.",
  "example_patterns": [
    "Common Crawl with 10TB of web data",
    "OpenAssistant conversations with 161K messages",
    "CodeParrot Python code dataset"
  ]
}
```

#### 7. Experiment
```json
{
  "name": "experiment",
  "display_name": "Experiment",
  "description": "Experimental setup, configuration, or result from research",
  "icon": "science",
  "color": "#FF6D01",
  "validation_rules": {
    "required_fields": ["name", "objective"],
    "optional_fields": ["setup", "results", "conclusions"]
  },
  "extraction_prompt": "Extract experimental details including experiment name, research objective or hypothesis, experimental setup and methodology, key results and metrics, main conclusions or findings, and any ablation studies performed. Note significant or surprising findings.",
  "example_patterns": [
    "Scaling laws for compute-optimal training",
    "Ablation study on attention head count",
    "Few-shot learning evaluation on novel tasks"
  ]
}
```

#### 8. Tool/Framework
```json
{
  "name": "tool_framework",
  "display_name": "Tool or Framework",
  "description": "Software tool, library, or framework for AI development",
  "icon": "code",
  "color": "#7B1FA2",
  "validation_rules": {
    "required_fields": ["name", "type"],
    "optional_fields": ["version", "description", "use_cases"]
  },
  "extraction_prompt": "Extract tool/framework details including name, type (e.g., training framework, inference library, evaluation tool), version if specified, description of purpose and capabilities, common use cases, and notable features or limitations. Include both research and production tools.",
  "example_patterns": [
    "Hugging Face Transformers library",
    "vLLM for high-throughput inference",
    "Weights & Biases for experiment tracking"
  ]
}
```

---

### Relationship Types

#### 1. CITES
```json
{
  "name": "cites",
  "display_name": "Cites",
  "description": "Paper A cites Paper B in its references",
  "source_entity_types": ["research_paper"],
  "target_entity_types": ["research_paper"],
  "is_directional": true,
  "validation_rules": {},
  "extraction_prompt": "Identify citation relationships between research papers. Note when one paper references another, including the context of the citation (e.g., background, methodology, comparison).",
  "example_patterns": [
    "Vaswani et al. (2017) introduced the attention mechanism",
    "Building on the work of Brown et al. (2020)",
    "We extend prior approaches (Smith et al., 2019)"
  ]
}
```

#### 2. PROPOSES
```json
{
  "name": "proposes",
  "display_name": "Proposes",
  "description": "Paper A proposes or introduces Technique/Architecture/Model",
  "source_entity_types": ["research_paper"],
  "target_entity_types": ["model_architecture", "technique", "experiment"],
  "is_directional": true,
  "validation_rules": {},
  "extraction_prompt": "Identify when a research paper proposes, introduces, or develops new techniques, architectures, models, or experimental approaches. Note the novelty claims made by the authors.",
  "example_patterns": [
    "This paper proposes the Transformer architecture",
    "We introduce a new technique called LoRA",
    "We propose scaling to 175B parameters"
  ]
}

#### 3. EVALUATES_ON
```json
{
  "name": "evaluates_on",
  "display_name": "Evaluates On",
  "description": "Model/Technique A is evaluated on Benchmark/Dataset",
  "source_entity_types": ["model_architecture", "technique", "experiment"],
  "target_entity_types": ["benchmark", "dataset"],
  "is_directional": true,
  "validation_rules": {},
  "extraction_prompt": "Identify evaluation relationships. Note which models or techniques are evaluated on which benchmarks, the specific metrics achieved, and any notable performance claims.",
  "example_patterns": [
    "GPT-4 achieves 90.1% on MMLU",
    "Evaluated on 57 tasks including HellaSwag",
    "Testing on Common Crawl-based evaluations"
  ]
}
```

#### 4. USES
```json
{
  "name": "uses",
  "display_name": "Uses",
  "description": "Model/Technique A uses/incorporates Technique/Dataset/Tool",
  "source_entity_types": ["model_architecture", "technique", "experiment"],
  "target_entity_types": ["technique", "dataset", "tool_framework"],
  "is_directional": true,
  "validation_rules": {},
  "extraction_prompt": "Identify usage relationships where a model, technique, or experiment incorporates or utilizes other components. Note how the component is used and any modifications made.",
  "example_patterns": [
    "LLaMA uses RoPE position embeddings",
    "Training uses the Pile dataset",
    "Implemented using the DeepSpeed library"
  ]
}
```

#### 5. COMPARES_WITH
```json
{
  "name": "compares_with",
  "display_name": "Compares With",
  "description": "Model/Technique A is compared with Model/Technique B in experiments",
  "source_entity_types": ["model_architecture", "technique", "experiment"],
  "target_entity_types": ["model_architecture", "technique", "experiment"],
  "is_directional": false,
  "validation_rules": {},
  "extraction_prompt": "Identify comparative relationships between models, techniques, or experiments. Note the basis of comparison and which performs better in which scenarios.",
  "example_patterns": [
    "Compared against GPT-3.5 on reasoning tasks",
    "Outperforms prior methods by 15%",
    "Competitive with Claude on code generation"
  ]
}
```

#### 6. EXTENDS
```json
{
  "name": "extends",
  "display_name": "Extends",
  "description": "Model/Technique A extends or builds upon Model/Technique B",
  "source_entity_types": ["model_architecture", "technique"],
  "target_entity_types": ["model_architecture", "technique"],
  "is_directional": true,
  "validation_rules": {},
  "extraction_prompt": "Identify extension relationships where one model or technique is explicitly based on or extends another. Note the nature of improvements or modifications.",
  "example_patterns": [
    "LLaMA extends the Transformer architecture",
    "Building upon Flash Attention",
    "An extension of the original attention mechanism"
  ]
}
```

#### 7. ACHIEVES
```json
{
  "name": "achieves",
  "display_name": "Achieves",
  "description": "Experiment/Model achieves performance metric on Benchmark",
  "source_entity_types": ["experiment", "model_architecture"],
  "target_entity_types": ["benchmark"],
  "is_directional": true,
  "validation_rules": {},
  "extraction_prompt": "Identify performance achievements including specific metrics achieved, the benchmark or evaluation task, and any notable achievements (e.g., state-of-the-art, human-level performance).",
  "example_patterns": [
    "Achieves 89.4% accuracy on GSM8K",
    "Reaches human-level performance on MNIST",
    "Sets new state-of-the-art on ImageNet"
  ]
}
```

---

## Template System Architecture

### Template Loading

```python
class TemplateLoader:
    async def load_template(self, template_path: str) -> DomainTemplate:
        with open(template_path) as f:
            config = json.load(f)
        return self.parse_template(config)

    async def load_from_database(self, domain_id: UUID) -> DomainTemplate:
        domain = await get_domain(domain_id)
        return self.reconstruct_template(domain)
```

### Template Validation

```python
class TemplateValidator:
    def validate_entity_type(self, entity_type: EntityTypeTemplate) -> List[str]:
        errors = []
        if not entity_type.name:
            errors.append("Entity type name is required")
        if not entity_type.display_name:
            errors.append("Entity type display_name is required")
        if not entity_type.extraction_prompt:
            errors.append("Entity type extraction_prompt is required")
        for pattern in entity_type.example_patterns:
            if len(pattern) < 5:
                errors.append(f"Pattern too short: {pattern}")
        return errors

    def validate_relationship_type(self, rel_type: RelationshipTypeTemplate) -> List[str]:
        errors = []
        if not rel_type.name:
            errors.append("Relationship type name is required")
        if not rel_type.source_entity_types:
            errors.append("At least one source entity type is required")
        if not rel_type.target_entity_types:
            errors.append("At least one target entity type is required")
        return errors
```

---

## Creating New Domain Templates

### Step 1: Define Domain Metadata

```json
{
  "id": "new_domain",
  "name": "new_domain",
  "display_name": "New Domain",
  "description": "Description of the domain..."
}
```

### Step 2: Define Entity Types

Create entity types relevant to the domain:
- Use consistent naming convention (snake_case)
- Define clear validation rules
- Write detailed extraction prompts
- Provide representative example patterns

### Step 3: Define Relationship Types

Define how entities relate to each other:
- Specify source and target entity types
- Consider bidirectional relationships
- Define extraction context
- Set validation rules

### Step 4: Configure Analysis Modules

```json
{
  "analysis_config": {
    "community_detection": {
      "algorithm": "leiden",
      "resolution_parameter": 1.0
    },
    "summarization": {
      "max_summary_length": 500,
      "include_entities": true
    },
    "trend_analysis": {
      "enabled": true,
      "time_window": "1y"
    }
  }
}
```

### Step 5: Configure UI Settings

```json
{
  "ui_config": {
    "color_scheme": {
      "primary": "#4285F4",
      "background": "#FFFFFF"
    },
    "layout": "default",
    "default_views": ["graph", "list", "timeline"]
  }
}
```

### Step 6: Test Template

```python
async def test_template(template: DomainTemplate):
    # Test entity extraction
    test_text = "Example text with entity mentions"
    entities = await extract_entities(test_text, template)
    assert len(entities) > 0

    # Test relationship extraction
    relationships = await extract_relationships(test_text, template)
    assert len(relationships) > 0

    # Validate schema
    errors = TemplateValidator().validate_template(template)
    assert len(errors) == 0
```

---

## Template Best Practices

### Naming Conventions
- Use snake_case for internal names
- Use Title Case for display names
- Keep names short but descriptive
- Avoid special characters except underscores

### Extraction Prompts
- Be specific about what to extract
- Include format examples
- Specify edge cases
- Define confidence indicators

### Validation Rules
- Set appropriate constraints
- Balance strictness with flexibility
- Include field descriptions
- Define allowed values/ranges

### Example Patterns
- Include 3-5 representative examples
- Cover different phrasing styles
- Show context variations
- Include edge cases

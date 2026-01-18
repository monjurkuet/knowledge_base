# Adaptive Schema Upgrade Plan

## 1. Prompt Strategy

We need to upgrade the `DomainDetectionPrompt` in `src/knowledge_base/domain_detector.py` to extract a **rich schema** instead of just lists of strings.

### New Prompt Structure
The prompt will request a JSON response with the following structure:

```json
{
  "domain_name": "clinical_trials",
  "display_name": "Clinical Trials",
  "description": "...",
  "entity_types": [
    {
      "name": "medication",
      "display_name": "Medication",
      "description": "A substance used for medical treatment...",
      "synonyms": ["drug", "pharmaceutical", "medicine"],
      "attributes": [
        {"name": "dosage", "type": "string", "description": "Amount of medication"}
      ]
    }
  ],
  "relationship_types": [
    {
      "name": "treats",
      "display_name": "Treats",
      "source": "medication",
      "target": "condition",
      "description": "Indicates a medication is used for a condition"
    }
  ],
  "confidence": 0.95
}
```

### Key Changes to `detect_domain_from_text`:
1.  **Rich Schema Extraction**: Ask for descriptions, synonyms, and attributes for entities.
2.  **Relationship Constraints**: Ask for source/target constraints for relationships.
3.  **Validation Rules**: Ask for simple validation rules (e.g., "dosage must contain a number").

## 2. Schema Synchronization Logic

We will introduce a new method `sync_domain_schema` in `DomainManager` (or a new `SchemaManager` class) to handle the merging of the **Proposed Schema** (from LLM) with the **Existing Schema** (from DB).

### Algorithm: `merge_schemas(proposed, existing)`

1.  **Load Existing Schema**: Fetch all `domain_entity_types` and `domain_relationship_types` for the target domain.
2.  **Entity Merging**:
    *   Iterate through `proposed.entity_types`.
    *   **Exact Match**: If `proposed.name` == `existing.name`, update description/attributes if the new one is richer.
    *   **Synonym Match**: Check if `proposed.name` is in `existing.synonyms` OR if `existing.name` is in `proposed.synonyms`. If match, treat as the *same* entity. Use the canonical name from DB.
    *   **Semantic Match (Optional/Advanced)**: Use embeddings or a lightweight LLM call to check if "Medication" is semantically identical to "Drug".
    *   **New Type**: If no match, mark for INSERT.
3.  **Relationship Merging**:
    *   Similar logic. Check `name`, `source`, and `target`.
    *   If `treats(Drug -> Disease)` exists, and we propose `cures(Medication -> Illness)`, and we mapped `Medication->Drug` and `Illness->Disease`, then check if `cures` is a synonym for `treats`.
4.  **Database Updates**:
    *   Execute batch INSERTs for new types.
    *   Execute UPDATEs for enriched definitions.

## 3. Data Flow (New Pipeline)

The `KnowledgePipeline.run` method in `src/knowledge_base/pipeline.py` will be updated:

1.  **Input**: Raw Text.
2.  **Step 1: Domain & Schema Detection** (LLM)
    *   Call `domain_detector.detect_domain_and_schema(text)`.
    *   Returns `ProposedDomain` object with full schema.
3.  **Step 2: Domain Resolution**
    *   Check if domain exists (by name).
    *   If not, create domain.
4.  **Step 3: Schema Synchronization** (Critical New Step)
    *   Call `domain_manager.sync_schema(domain_id, proposed_schema)`.
    *   This performs the "Merge" logic defined above.
    *   Returns the `FinalSchema` (IDs and Names of the actual DB types).
5.  **Step 4: Ingestion**
    *   Call `ingestor.extract(text, schema=FinalSchema)`.
    *   **Crucial**: The ingestor must use the *canonical* names from `FinalSchema` to ensure the graph is built correctly.
6.  **Step 5**: Storage, Community Detection, etc. (Unchanged).

## 4. Database Changes

We need to ensure the database supports the richer schema metadata.

1.  **`domain_entity_types` table**:
    *   Add `synonyms` column (JSONB array) - *Useful for matching*.
    *   `validation_rules` already exists (JSONB).
    *   `extraction_prompt` already exists.

2.  **`domain_relationship_types` table**:
    *   Add `synonyms` column (JSONB array).

**SQL Update:**
```sql
ALTER TABLE domain_entity_types ADD COLUMN IF NOT EXISTS synonyms JSONB DEFAULT '[]';
ALTER TABLE domain_relationship_types ADD COLUMN IF NOT EXISTS synonyms JSONB DEFAULT '[]';
```

## 5. Implementation Steps

1.  **Modify `DomainDetectionPrompt`**: Update the system prompt to output the rich JSON structure.
2.  **Update `DomainTemplate` Pydantic Models**: Ensure they match the new rich structure (add `synonyms`, `attributes`).
3.  **Implement `SchemaMerger`**: Create the logic to compare and merge schemas.
4.  **Update `DomainManager`**: Add methods to save the merged schema (handling the `synonyms` column).
5.  **Update `KnowledgePipeline`**: Integrate the detection -> sync -> ingest flow.

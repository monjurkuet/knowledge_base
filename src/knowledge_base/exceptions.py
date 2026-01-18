"""
Custom exceptions for the Knowledge Base GraphRAG system
"""


class KnowledgeBaseError(Exception):
    """Base exception for all Knowledge Base errors"""

    pass


class LLMError(KnowledgeBaseError):
    """Exception raised for errors related to LLM operations"""

    pass


class EmbeddingError(KnowledgeBaseError):
    """Exception raised for errors related to embeddings generation"""

    pass


class DatabaseError(KnowledgeBaseError):
    """Exception raised for errors related to database operations"""

    pass


class PipelineError(KnowledgeBaseError):
    """Exception raised for errors in the processing pipeline"""

    pass


class IngestionError(KnowledgeBaseError):
    """Exception raised for errors during content ingestion"""

    pass


class ExtractionError(KnowledgeBaseError):
    """Exception raised for errors during entity/relationship extraction"""

    pass


class ResolutionError(KnowledgeBaseError):
    """Exception raised for errors during entity resolution"""

    pass


class CommunityDetectionError(KnowledgeBaseError):
    """Exception raised for errors during community detection"""

    pass


class SummarizationError(KnowledgeBaseError):
    """Exception raised for errors during community summarization"""

    pass


class ConfigurationError(KnowledgeBaseError):
    """Exception raised for errors in configuration"""

    pass


class ValidationError(KnowledgeBaseError):
    """Exception raised for validation errors"""

    pass

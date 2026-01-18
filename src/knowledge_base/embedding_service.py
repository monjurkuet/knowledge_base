"""
Embedding service following consistent patterns with HTTPClient
"""

import logging
from typing import Any

import httpx
from google import genai

from knowledge_base.circuit_breaker import CircuitBreaker
from knowledge_base.config import get_config
from knowledge_base.embedding_cache import embedding_cache

logger = logging.getLogger(__name__)


class EmbeddingError(Exception):
    """Base embedding exception following HTTPClient patterns"""


class EmbeddingRateLimitError(EmbeddingError):
    """Rate limit specific error"""


class EmbeddingCacheError(EmbeddingError):
    """Cache-related errors"""


class GoogleEmbeddingService:
    """
    Google GenAI embedding service following consistent patterns with HTTPClient
    """

    MAX_RETRIES = 2
    RETRY_DELAY = 3.0
    TIMEOUT_SECONDS = 30

    def __init__(
        self, api_key: str | None = None, model_name: str = "text-embedding-004"
    ):
        config = get_config()
        self.model_name = model_name
        self.api_key = api_key or config.llm.google_api_key
        if not self.api_key:
            raise ValueError("GOOGLE_API_KEY is required for embedding operations")

        self.timeout = httpx.Timeout(self.TIMEOUT_SECONDS)
        # Separate circuit breaker for embeddings to avoid cross-contamination
        self.circuit_breaker = CircuitBreaker(
            failure_threshold=10,  # Higher threshold for embeddings
            recovery_timeout=30.0,  # Different timeout for embeddings
            name="embedding_api_circuit_breaker",
        )

    async def embed_content(
        self, text: str, task_type: str | None = None, dimensions: int | None = None
    ) -> list[float]:
        """
        Generate embedding for text with consistent patterns following HTTPClient

        Args:
            text: Text to embed
            task_type: Type of task for optimization (e.g., "RETRIEVAL_DOCUMENT", "SEMANTIC_SIMILARITY")
            dimensions: Output dimensionality (optional)

        Returns:
            List of embedding values

        Raises:
            EmbeddingError: If embedding generation fails
        """
        # Check cache first to avoid circuit breaker impact on cached items
        cached_embedding = embedding_cache.get(text)
        if cached_embedding:
            logger.debug(f"Embedding cache hit for text of length {len(text)}")
            return cached_embedding

        if not self.api_key:
            raise EmbeddingError(
                "GOOGLE_API_KEY is missing. Cannot generate embeddings."
            )

        async def _make_embedding_request():
            try:
                client = genai.Client(api_key=self.api_key)

                result = client.models.embed_content(
                    model=self.model_name,
                    contents=text,
                )

                if (
                    not result
                    or not hasattr(result, "embeddings")
                    or not result.embeddings
                ):
                    raise RuntimeError("API response is invalid or missing embeddings.")

                embedding_obj = result.embeddings[0] if result.embeddings else None

                if embedding_obj is None:
                    raise EmbeddingError("Embedding values are None.")

                # Extract the actual values from the embedding object
                embedding = (
                    embedding_obj.values if hasattr(embedding_obj, "values") else None
                )

                if embedding is None:
                    raise EmbeddingError("Embedding values are None.")

                # Cache the result
                embedding_cache.set(text, embedding)

                return embedding
            except Exception as e:
                logger.error(f"Embedding API request failed: {e}")
                if "rate" in str(e).lower() or "quota" in str(e).lower():
                    raise EmbeddingRateLimitError(f"Rate limit exceeded: {e}") from e
                raise EmbeddingError(f"Embedding API request failed: {e}") from e

        try:
            result = await self.circuit_breaker.call(_make_embedding_request)
            return result
        except Exception as e:
            # If circuit breaker is open, try to return cached version as fallback
            cached_fallback = embedding_cache.get(text)
            if cached_fallback:
                logger.warning(
                    "Circuit breaker is open, returning cached embedding as fallback"
                )
                return cached_fallback
            logger.error(f"Embedding request failed after circuit breaker: {e}")
            raise

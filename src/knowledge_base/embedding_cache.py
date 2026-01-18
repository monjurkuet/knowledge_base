"""
Simple in-memory embedding cache to avoid redundant API calls
"""

import hashlib
from threading import Lock


class EmbeddingCache:
    def __init__(self, max_size: int = 10000):
        self._cache: dict[str, list[float]] = {}
        self._max_size = max_size
        self._lock = Lock()

    def _get_key(self, text: str) -> str:
        """Generate a hash key for the text"""
        return hashlib.sha256(text.encode("utf-8")).hexdigest()

    def get(self, text: str) -> list[float] | None:
        """Get embedding from cache"""
        key = self._get_key(text)
        with self._lock:
            return self._cache.get(key)

    def set(self, text: str, embedding: list[float]) -> None:
        """Set embedding in cache"""
        key = self._get_key(text)
        with self._lock:
            # If cache is full, remove oldest entries (simple approach)
            if len(self._cache) >= self._max_size:
                # Remove first few items to make space
                items_to_remove = min(100, len(self._cache) // 4)
                keys_to_remove = list(self._cache.keys())[:items_to_remove]
                for k in keys_to_remove:
                    del self._cache[k]

            self._cache[key] = embedding

    def clear(self) -> None:
        """Clear the cache"""
        with self._lock:
            self._cache.clear()

    @property
    def size(self) -> int:
        """Get current cache size"""
        with self._lock:
            return len(self._cache)


# Global cache instance
embedding_cache = EmbeddingCache()

"""
Base repository class for all repositories.
"""

from typing import Any

from ..utils.db import BaseRepository as BaseRepositoryBase


class BaseRepository(BaseRepositoryBase):
    """Base repository with common database operations."""

    async def find_by_id(self, table: str, id_value: str) -> dict[str, Any] | None:
        """Find a record by ID."""
        query = f"SELECT * FROM {table} WHERE id = %s"
        results = await self._execute_query(query, (id_value,))
        return results[0] if results else None

    async def find_all(
        self,
        table: str,
        limit: int = 100,
        offset: int = 0,
        where_clause: str | None = None,
        params: tuple[Any, ...] | None = None,
    ) -> list[dict[str, Any]]:
        """Find all records with optional filtering and pagination."""
        query = f"SELECT * FROM {table}"
        query_params: list[Any] = []

        if where_clause:
            query += f" WHERE {where_clause}"
            if params:
                query_params.extend(params)

        query += " LIMIT %s OFFSET %s"
        query_params.extend([limit, offset])

        results = await self._execute_query(query, tuple(query_params))
        return results or []

    async def count(
        self,
        table: str,
        where_clause: str | None = None,
        params: tuple[Any, ...] | None = None,
    ) -> int:
        """Count records in table."""
        query = f"SELECT COUNT(*) FROM {table}"
        query_params: list[Any] = []

        if where_clause:
            query += f" WHERE {where_clause}"
            if params:
                query_params.extend(params)

        results = await self._execute_query(query, tuple(query_params))
        return results[0][0] if results else 0

    async def delete_by_id(self, table: str, id_value: str) -> bool:
        """Delete a record by ID."""
        query = f"DELETE FROM {table} WHERE id = %s"
        await self._execute_query(query, (id_value,), fetch=False, commit=True)
        return True

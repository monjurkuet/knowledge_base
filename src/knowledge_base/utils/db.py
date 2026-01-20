"""
Database utilities and base repository class.
Provides common database operations and connection management.
"""

import logging
from typing import Any

from psycopg import AsyncConnection

logger = logging.getLogger(__name__)


class DatabaseConnection:
    """Context manager for database connections."""

    def __init__(self, db_conn_str: str):
        self.db_conn_str = db_conn_str
        self._conn: AsyncConnection | None = None

    async def __aenter__(self) -> AsyncConnection:
        """Enter context and return connection."""
        self._conn = await AsyncConnection.connect(self.db_conn_str)
        return self._conn

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Exit context and close connection."""
        if self._conn:
            await self._conn.close()


class BaseRepository:
    """Base repository class with common database operations."""

    def __init__(self, db_conn_str: str):
        self.db_conn_str = db_conn_str

    async def _execute_query(
        self,
        query: str,
        params: tuple[Any, ...] | None = None,
        fetch: bool = True,
        commit: bool = False,
    ) -> Any:
        """
        Execute a database query.

        Args:
            query: SQL query string
            params: Query parameters
            fetch: Whether to fetch results
            commit: Whether to commit the transaction

        Returns:
            Query results or row count

        Raises:
            DatabaseError: If query execution fails
        """
        try:
            async with await AsyncConnection.connect(self.db_conn_str) as conn:
                async with conn.cursor() as cur:
                    await cur.execute(query, params or ())

                    if fetch:
                        results = await cur.fetchall()
                        if commit:
                            await conn.commit()
                        return results

                    if commit:
                        await conn.commit()
                        return cur.rowcount

                    return None

        except Exception as e:
            logger.error(f"Database query failed: {e}\nQuery: {query}")
            raise


class QueryBuilder:
    """Builder for constructing database queries."""

    def __init__(self, table: str):
        self.table = table
        self._select = ["*"]
        self._where: list[str] = []
        self._params: list[Any] = []
        self._order_by: list[str] = []
        self._limit: int | None = None
        self._offset: int | None = None

    def select(self, *columns: str) -> "QueryBuilder":
        """Set columns to select."""
        if columns:
            self._select = list(columns)
        return self

    def where(self, condition: str, *params: Any) -> "QueryBuilder":
        """Add WHERE condition."""
        self._where.append(condition)
        self._params.extend(params)
        return self

    def order_by(self, column: str, ascending: bool = True) -> "QueryBuilder":
        """Add ORDER BY clause."""
        direction = "ASC" if ascending else "DESC"
        self._order_by.append(f"{column} {direction}")
        return self

    def limit(self, limit: int) -> "QueryBuilder":
        """Set LIMIT."""
        self._limit = limit
        return self

    def offset(self, offset: int) -> "QueryBuilder":
        """Set OFFSET."""
        self._offset = offset
        return self

    def build(self) -> tuple[str, tuple[Any, ...]]:
        """Build and return query and parameters."""
        query_parts = [f"SELECT {', '.join(self._select)} FROM {self.table}"]

        if self._where:
            query_parts.append("WHERE " + " AND ".join(self._where))

        if self._order_by:
            query_parts.append("ORDER BY " + ", ".join(self._order_by))

        if self._limit is not None:
            query_parts.append(f"LIMIT {self._limit}")

        if self._offset is not None:
            query_parts.append(f"OFFSET {self._offset}")

        query = " ".join(query_parts)
        return query, tuple(self._params)


async def execute_transaction(
    db_conn_str: str, operations: list[tuple[str, tuple[Any, ...] | None]]
) -> list[Any]:
    """
    Execute multiple operations in a single transaction.

    Args:
        db_conn_str: Database connection string
        operations: List of (query, params) tuples

    Returns:
        List of results from each operation

    Raises:
        DatabaseError: If transaction fails
    """
    try:
        async with await AsyncConnection.connect(db_conn_str) as conn:
            async with conn.cursor() as cur:
                results = []
                for query, params in operations:
                    await cur.execute(query, params or ())
                    results.append(await cur.fetchall())
                await conn.commit()
                return results

    except Exception as e:
        logger.error(f"Transaction failed: {e}")
        raise


def escape_like_pattern(pattern: str) -> str:
    """
    Escape special characters for LIKE queries.

    Args:
        pattern: The pattern to escape

    Returns:
        Escaped pattern
    """
    escape_char = "\\"
    escaped = pattern.replace(escape_char, escape_char * 2)
    escaped = escaped.replace("%", f"{escape_char}%")
    escaped = escaped.replace("_", f"{escape_char}_")
    return escaped

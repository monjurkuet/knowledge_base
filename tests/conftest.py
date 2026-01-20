"""
Test configuration and fixtures
"""

import asyncio
import os
from typing import AsyncGenerator, Generator

import pytest
from fastapi.testclient import TestClient

os.environ["GOOGLE_API_KEY"] = "test_key"
os.environ["DB_HOST"] = "localhost"
os.environ["DB_PORT"] = "5432"
os.environ["DB_NAME"] = "test_knowledge_base"
os.environ["DB_USER"] = "agentzero"


@pytest.fixture
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session", autouse=True)
async def setup_test_database():
    """Create and initialize test database"""
    import psycopg

    print("\n=== Setting up test database ===")

    conn = await psycopg.AsyncConnection.connect(
        "postgresql://agentzero@localhost:5432/postgres", autocommit=True
    )

    try:
        await conn.execute("DROP DATABASE IF EXISTS test_knowledge_base WITH (FORCE)")
        await conn.execute("CREATE DATABASE test_knowledge_base")
        print("✓ Test database created")
    except Exception as e:
        print(f"Error creating database: {e}")
        await conn.close()
        raise
    finally:
        await conn.close()

    conn = await psycopg.AsyncConnection.connect(
        "postgresql://agentzero@localhost:5432/test_knowledge_base"
    )
    try:
        schema_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "database",
            "schema.sql",
        )
        with open(schema_path) as f:
            await conn.execute(f.read())
        await conn.commit()
        print("✓ Schema initialized")
    except Exception as e:
        print(f"Error initializing schema: {e}")
        await conn.close()
        raise
    finally:
        await conn.close()


@pytest.fixture
async def db_transaction():
    """Wrap each test in a transaction for isolation"""
    import psycopg
    from knowledge_base.config import get_config

    config = get_config()
    conn = await psycopg.AsyncConnection.connect(config.database.connection_string)

    try:
        await conn.execute("BEGIN")
        yield conn
    finally:
        await conn.execute("ROLLBACK")
        await conn.close()


@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    """Create a test client for the FastAPI app."""
    from knowledge_base.api import app

    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
async def db_connection() -> AsyncGenerator:
    """Create a database connection for testing."""
    import psycopg
    from knowledge_base.config import get_config

    config = get_config()
    conn = await psycopg.AsyncConnection.connect(config.database.connection_string)
    yield conn
    await conn.close()


@pytest.fixture
def sample_text() -> str:
    """Sample text for ingestion tests."""
    return """
    TechCorp is a technology company founded in 2010.
    Alice Chen is a Senior Software Engineer at TechCorp.
    Bob Smith is the Product Manager.
    Project Alpha is their AI research initiative.
    """


@pytest.fixture
def sample_graph_data():
    """Sample graph data for testing."""
    return {
        "entities": [
            {
                "name": "Test Company",
                "type": "organization",
                "description": "A test company",
            },
            {"name": "John Doe", "type": "person", "description": "A test person"},
        ],
        "relationships": [
            {
                "source": "John Doe",
                "target": "Test Company",
                "type": "WORKS_FOR",
                "description": "John works at Test Company",
                "weight": 1.0,
            }
        ],
        "events": [],
    }

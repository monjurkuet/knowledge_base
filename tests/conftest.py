from contextlib import asynccontextmanager
from pathlib import Path

import numpy as np
import pytest
from psycopg import AsyncConnection, sql
from rich.console import Console

from knowledge_base.community import CommunityDetector
from knowledge_base.config import get_config
from knowledge_base.ingestor import GraphIngestor
from knowledge_base.pipeline import KnowledgePipeline
from knowledge_base.resolver import EntityResolver
from knowledge_base.summarizer import CommunitySummarizer

config = get_config()
console = Console()


@asynccontextmanager
async def get_live_db_connection():
    """Get a live database connection for integration tests"""
    conn = await AsyncConnection.connect(config.database.connection_string)
    try:
        yield conn
    finally:
        await conn.close()


@pytest.fixture
async def db_conn():
    """Provide async database connection for tests"""
    conn = await AsyncConnection.connect(config.database.connection_string)
    yield conn
    await conn.close()


config = get_config()
console = Console()

ROOT_DIR = Path(__file__).parent.parent


@pytest.fixture(scope="session")
async def setup_database():
    """Session-scoped fixture to set up the database schema once."""
    conn = await AsyncConnection.connect(config.database.connection_string)
    async with conn.cursor() as cur:
        # Drop all tables to start fresh
        await cur.execute("""
            DO $$ DECLARE
                r RECORD;
            BEGIN
                FOR r IN (SELECT tablename FROM pg_tables WHERE schemaname = 'public') LOOP
                    EXECUTE 'DROP TABLE IF EXISTS ' || quote_ident(r.tablename) || ' CASCADE';
                END LOOP;
            END $$;
        """)

        # Read and execute schema files
        schema_path = ROOT_DIR / "database/schema.sql"
        migration_path = ROOT_DIR / "database/schema_migration_001_multi_domain.sql"

        with open(schema_path, "r") as f:
            await cur.execute(f.read())  # type: ignore[arg-type]

        # The migration script might have issues if run on a fresh schema,
        # but we include it for completeness. It's idempotent.
        with open(migration_path, "r") as f:
            await cur.execute(f.read())  # type: ignore[arg-type]

        await conn.commit()
    await conn.close()


@pytest.fixture
async def live_db(setup_database):
    """Provide live database connection with automatic cleanup, ensuring schema exists."""
    conn = await AsyncConnection.connect(config.database.connection_string)
    async with conn.cursor() as cur:
        # Truncate tables before the test runs for a clean slate
        await cur.execute(
            "TRUNCATE domains, nodes, edges, communities, community_membership, community_hierarchy, events CASCADE"
        )
        await conn.commit()
    yield conn
    # The connection is closed automatically by the test function's teardown
    await conn.close()


@pytest.fixture
async def seeded_db(live_db):
    """Provide a database with sample test data"""
    async with live_db.cursor() as cur:
        # Add a default domain for fk constraints
        await cur.execute(
            "INSERT INTO domains (id, name, display_name, description) VALUES (%s, %s, %s, %s)",
            (
                "11111111-1111-1111-1111-111111111111",
                "Default Domain",
                "Default Domain",
                "A domain for testing",
            ),
        )

        embedding_1 = np.random.rand(768).tolist()
        embedding_2 = np.random.rand(768).tolist()
        embedding_3 = np.random.rand(768).tolist()

        await cur.execute(
            "INSERT INTO nodes (id, name, type, description, embedding, domain_id) VALUES (%s, %s, %s, %s, %s, %s), (%s, %s, %s, %s, %s, %s), (%s, %s, %s, %s, %s, %s)",
            (
                "11111111-1111-1111-1111-111111111111",
                "Test Entity 1",
                "Person",
                "A test person",
                embedding_1,
                "11111111-1111-1111-1111-111111111111",
                "22222222-2222-2222-2222-222222222222",
                "Test Entity 2",
                "Organization",
                "A test company",
                embedding_2,
                "11111111-1111-1111-1111-111111111111",
                "33333333-3333-3333-3333-333333333333",
                "Test Entity 3",
                "Concept",
                "A test idea",
                embedding_3,
                "11111111-1111-1111-1111-111111111111",
            ),
        )
        await live_db.commit()
    yield live_db


@pytest.fixture
async def pipeline():
    """Provide KnowledgePipeline instance for tests"""
    return KnowledgePipeline()


@pytest.fixture
async def ingestor():
    """Provide GraphIngestor instance for tests"""
    return GraphIngestor(model_name=config.llm.model_name)


@pytest.fixture
async def resolver():
    """Provide EntityResolver instance for tests"""
    return EntityResolver(
        db_conn_str=config.database.connection_string,
        model_name=config.llm.model_name,
    )


@pytest.fixture
async def community_detector():
    """Provide CommunityDetector instance for tests"""
    return CommunityDetector(db_conn_str=config.database.connection_string)


@pytest.fixture
async def summarizer():
    """Provide CommunitySummarizer instance for tests"""
    return CommunitySummarizer(
        config.database.connection_string, model_name=config.llm.model_name
    )


@pytest.fixture(scope="session")
def test_data_dir():
    """Path to test data directory"""
    return Path(__file__).parent / "data"

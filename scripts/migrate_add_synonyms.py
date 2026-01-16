import asyncio
import logging
import sys
import os

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), "../src"))

from knowledge_base.config import get_config
from psycopg import AsyncConnection

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def migrate():
    config = get_config()
    conn_str = config.database.connection_string

    logger.info(f"Connecting to database...")

    async with await AsyncConnection.connect(conn_str) as conn:
        async with conn.cursor() as cur:
            # Add synonyms to domain_entity_types
            logger.info("Checking domain_entity_types...")
            await cur.execute("""
                ALTER TABLE domain_entity_types 
                ADD COLUMN IF NOT EXISTS synonyms JSONB DEFAULT '[]'::jsonb;
            """)

            # Add synonyms to domain_relationship_types
            logger.info("Checking domain_relationship_types...")
            await cur.execute("""
                ALTER TABLE domain_relationship_types 
                ADD COLUMN IF NOT EXISTS synonyms JSONB DEFAULT '[]'::jsonb;
            """)

            await conn.commit()
            logger.info("Migration completed successfully.")


if __name__ == "__main__":
    asyncio.run(migrate())

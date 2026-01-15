"""Application lifecycle events."""

import logging

from app.db.base import engine

logger = logging.getLogger(__name__)


async def connect_to_db() -> None:
    """Initialize database connections on startup."""
    logger.info("Connecting to database...")
    try:
        # Test database connection
        async with engine.begin() as conn:
            await conn.execute("SELECT 1")
        logger.info("✅ Database connection established")
    except Exception as e:
        logger.error(f"❌ Failed to connect to database: {e}")
        raise


async def close_db_connection() -> None:
    """Close database connections on shutdown."""
    logger.info("Closing database connections...")
    try:
        await engine.dispose()
        logger.info("✅ Database connections closed")
    except Exception as e:
        logger.error(f"❌ Error closing database connections: {e}")

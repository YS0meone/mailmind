from .logger_config import get_logger
from .core.db import init_db
import asyncio

loggerr = get_logger(__name__)

async def main():
    """
    Initializes the database and logs the completion of the initialization.
    """
    loggerr.info("Initializing database...")
    try:
        await init_db()
    except Exception as e:
        loggerr.error("Failed to initialize database: %s", e)
        raise e
    loggerr.info("Database initialized successfully.")

if __name__ == "__main__":
    asyncio.run(main())
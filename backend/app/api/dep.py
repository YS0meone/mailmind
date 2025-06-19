from app.core.db import AsyncSessionLocal
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends
from typing import Annotated
from app.logger_config import get_logger


logger = get_logger(__name__)


async def get_db():
    """
    Database dependency with proper session management.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

SessionDep = Annotated[AsyncSession, Depends(get_db)]


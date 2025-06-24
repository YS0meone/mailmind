from fastapi.security import HTTPBearer
from app.core.db import AsyncSessionLocal
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends, HTTPException, Request
from typing import Annotated
from app.logger_config import get_logger
from app.core.security import decode_jwt_token


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

security = HTTPBearer(auto_error=False)

# get user email from the jwt token sent from the frontend
async def verify_user_email(
    request: Request,
    token: str = Depends(security)
) -> str:
    """
    Verify user email from the JWT token in the request.
    """
    if token:
        token_str = token.credentials
    else:
        token_str = request.cookies.get("access_token")

    if not token_str:
        raise HTTPException(status_code=401, detail="Not authenticated")
    try:
        return decode_jwt_token(token_str)
    except Exception as e:
        logger.error(f"Error verifying user email: {e}")
        raise HTTPException(status_code=401, detail="Invalid token") from e

TokenDep = Annotated[str, Depends(verify_user_email)]
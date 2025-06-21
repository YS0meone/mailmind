from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.postgresql import insert
from app.models import User, DbUser
from app.logger_config import get_logger
logger = get_logger(__name__)

async def upsert_user(*, session: AsyncSession, user: User) -> DbUser | None:
    # check if the user with given email exists
    stmt = select(DbUser).where(DbUser.email == user.email)
    result = await session.execute(stmt)
    db_user = result.scalar_one_or_none()
    if db_user:
        # if user exists, update the existing user
        db_user.accountId = user.accountId
        db_user.accountToken = user.accountToken
        db_user.lastDeltaToken = user.lastDeltaToken
        await session.commit()
        await session.refresh(db_user)
        logger.info(f"Updated existing user: {db_user}")
         # Return the updated user
        return db_user
    else:
        new_user = DbUser(
            accountId=user.accountId,
            accountToken=user.accountToken,
            email=user.email,
            lastDeltaToken=user.lastDeltaToken
        )
        session.add(new_user)
        await session.commit()
        await session.refresh(new_user)
        logger.info(f"Inserted new user: {new_user}")
         # Return the newly created user
        return new_user


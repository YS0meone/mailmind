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
        db_user.account_id = user.account_id
        db_user.account_token = user.account_token
        db_user.last_delta_token = user.last_delta_token
        await session.commit()
        await session.refresh(db_user)
        logger.info(f"Updated existing user: {db_user}")
         # Return the updated user
        return db_user
    else:
        new_user = DbUser(
            account_id=user.account_id,
            account_token=user.account_token,
            email=user.email,
            last_delta_token=user.last_delta_token
        )
        session.add(new_user)
        await session.commit()
        await session.refresh(new_user)
        logger.info(f"Inserted new user: {new_user}")
         # Return the newly created user
        return new_user


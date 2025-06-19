from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.postgresql import insert
from app.models import User, DbUser

async def upsert_user(*, session: AsyncSession, user: User) -> DbUser | None:
    stmt = insert(DbUser).values(
        **user.model_dump()
    )
    
    update_data = {key: stmt.excluded[key] for key in user.model_fields if key != 'account_id'}
    stmt = stmt.on_conflict_do_update(
        index_elements=['account_id'],
        set_=update_data
    ).returning(DbUser)
    result = await session.execute(stmt)
    await session.commit()
    return result.scalars().one_or_none()





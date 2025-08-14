from arq import cron
from arq.connections import RedisSettings
from app.core.config import settings
from app.core.db import AsyncSessionLocal
from sqlalchemy import select
from app.models import DbUser, User
from app.logger_config import get_logger
from app.crud import sync_emails_and_threads, delete_emails_by_ids
from app.api.routes.auth import init_sync_emails, increment_sync_updated, increment_sync_deleted
from datetime import datetime, timezone

logger = get_logger(__name__)


async def acquire_user_lock(redis, account_id: str) -> bool:
    key = f"locks:sync:{account_id}"
    # NX + EX → set if not exists with TTL
    return await redis.set(key, "1", ex=settings.SYNC_LOCK_TTL_SECONDS, nx=True) is True


async def release_user_lock(redis, account_id: str) -> None:
    await redis.delete(f"locks:sync:{account_id}")


async def sync_emails_task(ctx, user_email: str):
    redis = ctx["redis"]
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(DbUser).where(DbUser.email == user_email))
        db_user = result.scalar_one_or_none()
        if not db_user:
            logger.warning("User %s not found for sync", user_email)
            return

        # guard against duplicate syncs for the same user across workers
        if not await acquire_user_lock(redis, db_user.accountId):
            logger.info("Sync already running for %s", db_user.accountId)
            return

        try:
            # mark status as running
            await redis.hset(
                f"sync:status:{user_email}",
                mapping={
                    "state": "running",
                    "processed": 0,
                    "updatedAt": datetime.now(timezone.utc).isoformat(),
                },
            )
            # Ensure the user exists/up-to-date; build a simple User model if needed elsewhere
            user = User(
                accountId=db_user.accountId,
                accountToken=db_user.accountToken,
                email=db_user.email,
                lastUpdatedDeltaToken=db_user.lastUpdatedDeltaToken or db_user.lastDeltaToken,
                lastDeletedDeltaToken=db_user.lastDeletedDeltaToken,
            )
            # Choose tokens: if stored tokens exist, reuse them; otherwise initialize
            updated_token = user.lastUpdatedDeltaToken
            deleted_token = user.lastDeletedDeltaToken
            if not updated_token or not deleted_token:
                token_response = await init_sync_emails(db_user)
                if not token_response or not token_response.get("ready"):
                    logger.info(
                        "Email sync init not ready yet for %s", db_user.accountId)
                    return
                updated_token = token_response.get("syncUpdatedToken")
                deleted_token = token_response.get("syncDeletedToken")

            # Fetch updated records
            records: list[dict] = []
            last_updated_token = await increment_sync_updated(
                delta_token=updated_token,
                access_token=db_user.accountToken,
                records=records,
            )

            # Persist updated token
            db_user.lastUpdatedDeltaToken = last_updated_token
            await session.commit()

            # Fetch deleted records since same delta token
            deleted_ids: list[str] = []
            last_deleted_token = await increment_sync_deleted(
                delta_token=deleted_token,
                access_token=db_user.accountToken,
                deleted_ids=deleted_ids,
            )
            # Remove from DB
            if deleted_ids:
                await delete_emails_by_ids(session, deleted_ids)
            # Persist deleted token
            db_user.lastDeletedDeltaToken = last_deleted_token
            await session.commit()

            # Persist email records
            await sync_emails_and_threads(session, records, db_user, account_token=db_user.accountToken)
            logger.info(
                "Synced %d email records and updated tokens for user %s",
                len(records),
                db_user.accountId,
            )
            # update status to done
            await redis.hset(
                f"sync:status:{user_email}",
                mapping={
                    "state": "done",
                    "processed": len(records),
                    "updatedAt": datetime.now(timezone.utc).isoformat(),
                },
            )
        except Exception as e:
            # record error status
            await redis.hset(
                f"sync:status:{user_email}",
                mapping={
                    "state": "error",
                    "error": str(e),
                    "updatedAt": datetime.now(timezone.utc).isoformat(),
                },
            )
            raise
        finally:
            await release_user_lock(redis, db_user.accountId)


async def startup(ctx):
    pass


class WorkerSettings:
    functions = [sync_emails_task]
    on_startup = startup
    redis_settings = RedisSettings.from_dsn(settings.REDIS_URL)
    cron_jobs = []

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
import asyncio
from langchain_core.documents import Document
from app.services.vector_store import get_vector_store
from langchain_text_splitters import RecursiveCharacterTextSplitter

logger = get_logger(__name__)


def _unused():
    # placeholder to keep import grouping consistent
    return None


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
            # Remove from vector store (Chroma) by metadata filter
            try:
                if deleted_ids:
                    store = get_vector_store()
                    where = {"user_email": db_user.email,
                             "email_id": {"$in": deleted_ids}}
                    await asyncio.to_thread(store.delete, where=where)
            except Exception:
                pass

            # Persist email records
            await sync_emails_and_threads(session, records, db_user, account_token=db_user.accountToken)
            logger.info(
                "Synced %d email records and updated tokens for user %s",
                len(records),
                db_user.accountId,
            )
            # Index into Chroma vector store using LangChain Documents
            try:
                if records:
                    store = get_vector_store()
                    docs: list[Document] = []
                    for r in records:
                        text = ((r.get("subject") or "") + "\n" +
                                (r.get("body") or r.get("bodySnippet") or "")).strip()
                        if not text:
                            continue
                        meta = {
                            "user_email": db_user.email,
                            "email_id": r.get("id"),
                            "thread_id": r.get("threadId"),
                            "subject": r.get("subject") or "",
                            "snippet": r.get("bodySnippet") or "",
                            "sent_at": r.get("sentAt") or "",
                        }
                        docs.append(Document(page_content=text, metadata=meta))
                    docs_splitter = RecursiveCharacterTextSplitter(
                        # Set a really small chunk size, just to show.
                        chunk_size=1500,
                        chunk_overlap=150,
                        length_function=len,
                        is_separator_regex=False,
                    )
                    docs_split = docs_splitter.split_documents(docs)
                    logger.info(
                        "Indexed %d docs and persisted for %s", len(
                            docs_split), db_user.email
                    )
                    await store.aadd_documents(documents=docs_split)
                    logger.info("Added %d docs to vector store", len(docs_split))

                    # if docs:
                    #     await asyncio.to_thread(store.add_documents, docs)
                    #     # Ensure data is flushed to disk so other processes (API) can read it
                    #     try:
                    #         await asyncio.to_thread(store.persist)
                    #     except Exception:
                    #         pass
                    #     logger.info(
                    #         "Indexed %d docs and persisted for %s", len(
                    #             docs), db_user.email
                    #     )
            except Exception as e:
                logger.error("Vector indexing failed: %s", e)

            # (Removed legacy PGVector indexing path)

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

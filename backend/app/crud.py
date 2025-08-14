import httpx
import asyncio
from app.core.config import settings
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.postgresql import insert
from app.models import User, DbUser, DbEmailAddress, EmailLabel
from app.logger_config import get_logger
from app.models import DbEmail, DbThread, Email
from sqlalchemy import select
from app.models import DbUser, Email, Thread
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.postgresql import insert
from datetime import datetime
from typing import Iterable

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
        # Maintain legacy field while migrating
        db_user.lastDeltaToken = user.lastDeltaToken
        db_user.lastUpdatedDeltaToken = user.lastUpdatedDeltaToken or db_user.lastUpdatedDeltaToken
        db_user.lastDeletedDeltaToken = user.lastDeletedDeltaToken or db_user.lastDeletedDeltaToken
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
            lastDeltaToken=user.lastDeltaToken,
            lastUpdatedDeltaToken=user.lastUpdatedDeltaToken,
            lastDeletedDeltaToken=user.lastDeletedDeltaToken,
        )
        session.add(new_user)
        await session.commit()
        await session.refresh(new_user)
        logger.info(f"Inserted new user: {new_user}")
        # Return the newly created user
        return new_user


def parse_dt(iso_str):
    if not iso_str:
        return None
    dt = datetime.fromisoformat(iso_str.replace("Z", "+00:00"))
    # Strip timezone info for database compatibility
    return dt.replace(tzinfo=None)


async def get_or_create_email_address(session: AsyncSession, address_dict: dict) -> DbEmailAddress:
    if not address_dict:
        return None
    stmt = select(DbEmailAddress).where(
        DbEmailAddress.address == address_dict["address"])
    result = await session.execute(stmt)
    addr = result.scalar_one_or_none()
    if addr:
        # Update name if changed
        if address_dict.get("name") and addr.name != address_dict.get("name"):
            addr.name = address_dict.get("name")
        return addr

    addr = DbEmailAddress(
        address=address_dict["address"],
        name=address_dict.get("name")
    )
    session.add(addr)
    await session.flush()
    return addr


async def get_aurinko_token(session: AsyncSession, user_email: str) -> str:
    stmt = select(DbUser).where(DbUser.email == user_email)
    result = await session.execute(stmt)
    user = result.scalar_one_or_none()
    return user.accountToken


async def get_or_create_thread(session: AsyncSession, record: dict) -> DbThread:
    # Convert string threadId to integer
    thread_id = int(record["threadId"], 16)  # Convert hex string to int

    stmt = select(DbThread).where(DbThread.id == thread_id)
    result = await session.execute(stmt)
    thread = result.scalar_one_or_none()

    received_at = parse_dt(record["receivedAt"])

    if thread:
        # Only update lastMessageDate if receivedAt is newer
        if received_at and received_at > thread.lastMessageDate:
            thread.lastMessageDate = received_at.replace(
                tzinfo=None) if received_at.tzinfo else received_at
        # Update subject and brief if different
        if thread.subject != record["subject"]:
            thread.subject = record["subject"]

        # Update brief with bodySnippet
        body_snippet = record.get("bodySnippet", "Default Brief")
        if thread.brief != body_snippet:
            thread.brief = body_snippet

        return thread

    thread = DbThread(
        id=thread_id,  # Use converted integer ID
        subject=record["subject"],
        lastMessageDate=received_at.replace(
            tzinfo=None) if received_at and received_at.tzinfo else received_at,
        brief=record.get("bodySnippet", "Default Brief")
    )
    session.add(thread)
    await session.flush()
    return thread


async def upsert_record(session: AsyncSession, record: dict, body: str | None = None) -> None:
    # Handle None case for from address
    from_data = None
    if record.get("from"):
        from_data = await get_or_create_email_address(session, record["from"])

    to_addrs = [await get_or_create_email_address(session, a) for a in record.get("to", [])]
    cc_addrs = [await get_or_create_email_address(session, a) for a in record.get("cc", [])]
    bcc_addrs = [await get_or_create_email_address(session, a) for a in record.get("bcc", [])]
    reply_to_addrs = [await get_or_create_email_address(session, a) for a in record.get("replyTo", [])]

    # Ensure all addresses are flushed to get their IDs
    await session.flush()

    thread = await get_or_create_thread(session, record)

    stmt = select(DbEmail).where(DbEmail.id == int(record["id"], 16))
    result = await session.execute(stmt)
    existing_email = result.scalar_one_or_none()

    if existing_email:
        # Skip or update fields as needed
        return

    # Fix emailLabel - don't access array index if it might be empty
    sys_classifications = record.get("sysClassifications", [])
    # Make sure we have a valid fromId before creating the email
    email_label = sys_classifications[0] if sys_classifications else EmailLabel.inbox
    if from_data is None:
        logger.warning(
            f"No from address found for email {record['id']}, skipping...")
        return

    email = DbEmail(
        id=int(record["id"], 16),  # Convert hex string to int
        threadId=int(record["threadId"], 16),  # Convert hex string to int
        createdTime=parse_dt(record["createdTime"]),
        lastModifiedTime=parse_dt(record.get("lastModifiedTime")),
        sentAt=parse_dt(record["sentAt"]),
        receivedAt=parse_dt(record["receivedAt"]),
        subject=record["subject"],
        labels=record.get("sysLabels", []),
        fromId=from_data.id,  # Now safe since we checked above
        body=record.get("body"),
        inReplyTo=record.get("inReplyTo"),
        emailLabel=email_label,
        threadIndex=record.get("threadIndex")
    )

    # Filter out None values before setting relationships
    email.to_addresses = [addr for addr in to_addrs if addr is not None]
    email.cc_addresses = [addr for addr in cc_addrs if addr is not None]
    email.bcc_addresses = [addr for addr in bcc_addrs if addr is not None]
    email.reply_to_addresses = [
        addr for addr in reply_to_addrs if addr is not None]

    # Add addresses to thread access using explicit SQL to avoid lazy loading issues
    access_addresses = set([from_data] + to_addrs +
                           cc_addrs + bcc_addrs + reply_to_addrs)
    # Filter out None values
    access_addresses = {addr for addr in access_addresses if addr is not None}

    # Get current thread access addresses
    current_access_result = await session.execute(
        text("SELECT address_id FROM address_has_threads WHERE thread_id = :thread_id"),
        {"thread_id": thread.id}
    )
    current_address_ids = set(current_access_result.scalars().all())

    # Add new addresses to the association table
    for addr in access_addresses:
        if addr.id not in current_address_ids:
            await session.execute(
                text("INSERT INTO address_has_threads (address_id, thread_id) VALUES (:address_id, :thread_id) ON CONFLICT DO NOTHING"),
                {"address_id": addr.id, "thread_id": thread.id}
            )

    session.add(email)


async def sync_emails_and_threads(session: AsyncSession, records: list[dict], user: DbUser | None = None, account_token: str | None = None) -> None:
    """
    Sync emails and threads using the new logic that properly handles addresses_with_access.
    This replaces the old bulk upsert approach with a record-by-record approach that 
    manages email addresses and thread access relationships.
    """
    if not records:
        logger.info("No records to sync.")
        return

    logger.info(f"Starting sync of {len(records)} email records...")

    processed_count = 0
    for record in records:
        try:
            if "body" in record.get("omitted", {}):
                limits = httpx.Limits(
                    max_connections=settings.HTTP_MAX_CONNECTIONS,
                    max_keepalive_connections=settings.HTTP_MAX_KEEPALIVE_CONNECTIONS,
                )
                timeout = httpx.Timeout(
                    connect=settings.HTTP_CONNECT_TIMEOUT,
                    read=settings.HTTP_READ_TIMEOUT,
                    write=settings.HTTP_WRITE_TIMEOUT,
                    pool=settings.HTTP_POOL_TIMEOUT,
                )
                attempts = settings.HTTP_RETRY_ATTEMPTS
                base = settings.HTTP_RETRY_BACKOFF_BASE
                cap = settings.HTTP_RETRY_BACKOFF_CAP
                jitter = settings.HTTP_RETRY_JITTER
                retry_status = set(settings.HTTP_RETRY_STATUS_CODES)
                async with httpx.AsyncClient(limits=limits, timeout=timeout) as client:
                    last_exc = None
                    for attempt in range(attempts):
                        try:
                            response = await client.get(
                                f"{settings.AURINKO_BASE_URL}/email/messages/{record['id']}",
                                headers={
                                    "Authorization": f"Bearer {account_token or (user.accountToken if user else '')}"}
                            )
                            if response.status_code in retry_status:
                                raise httpx.HTTPStatusError(
                                    "retryable status", request=response.request, response=response
                                )
                            response.raise_for_status()
                            break
                        except (httpx.TimeoutException, httpx.TransportError, httpx.HTTPStatusError) as e:
                            last_exc = e
                            if attempt == attempts - 1:
                                raise
                            sleep_s = min(cap, base * (2 ** attempt)) + jitter
                            await asyncio.sleep(sleep_s)
                if response.status_code == 200:
                    record["body"] = response.json().get("body", None)
                    logger.info(f"Fetched body for email {record['id']}")
                else:
                    logger.error(
                        f"Failed to fetch body for email {record['id']}: {response.text}")
                    continue
            await upsert_record(session, record, body=record.get("body"))
            processed_count += 1
        except Exception as e:
            # Roll back this failed record so the session can proceed
            try:
                await session.rollback()
            except Exception:
                pass
            logger.error(
                f"Failed to process record {record.get('id', 'unknown')}: {e}")
            continue

    # Commit all changes at the end
    await session.commit()
    logger.info(
        f"Successfully synced {processed_count} email records with their threads and address relationships.")


async def delete_emails_by_ids(session: AsyncSession, ids: Iterable[str]) -> int:
    """Delete emails (and optionally cleanup) by provider ids that come from Aurinko.
    Incoming ids are hex strings; map to integer primary keys.
    Returns number of emails deleted.
    """
    # Convert to integer IDs and deduplicate
    int_ids = []
    for s in ids:
        if not s:
            continue
        try:
            int_ids.append(int(str(s), 16))
        except Exception:
            continue
    if not int_ids:
        return 0

    # Delete emails by primary key; rely on ON DELETE constraints for FKs if configured
    await session.execute(
        text("DELETE FROM emails WHERE id = ANY(:ids)"),
        {"ids": int_ids},
    )
    await session.commit()
    logger.info(f"Deleted {len(int_ids)} emails from database")
    return len(int_ids)

'''
curl -X GET -H 'Authorization: Bearer pL3FlLcng4Mbe2pIjHgxaILbUBwrPhGR4WC1touNEGU' \
    -G https://api.aurinko.io/v1/email/sync/updated \
    -d deltaToken='H4sIAAAAAAAA_2NgZmBkAAPGt60MgiBGhvF0VwDJixd4FwAAAA'
'''

'''
curl -X GET -H 'Authorization: Bearer pL3FlLcng4Mbe2pIjHgxaILbUBwrPhGR4WC1touNEGU' \
    https://api.aurinko.io/v1/email/messages/19778fdd6eb3eaf9/raw
'''

'''
curl -X GET -H 'Authorization: Bearer pL3FlLcng4Mbe2pIjHgxaILbUBwrPhGR4WC1touNEGU' \
    https://api.aurinko.io/v1/email/messages/19778fdd6eb3eaf9
    '''

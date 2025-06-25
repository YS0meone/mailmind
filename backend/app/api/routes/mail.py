from fastapi import APIRouter
from fastapi.exceptions import HTTPException
from app.logger_config import get_logger
from app.api.dep import SessionDep, TokenDep
from app.models import Thread, DbThread, DbEmail, Email, DbEmailAddress, address_has_threads
from sqlalchemy import and_, select, func
from sqlalchemy.orm import selectinload

logger = get_logger(__name__)

router = APIRouter(
    prefix="/mail",
    tags=["mail"]
)

'''
Test with:
curl -X GET "http://localhost:8000/mail/threads/<thread_id>/messages" \
    -H "Authorization: Bearer <token>"
'''
# get the email messsages associated with a thread


@router.get("/threads/{thread_id}/messages", response_model=list[Email])
async def get_thread_messages(thread_id: int, session: SessionDep, user_email: TokenDep):
    """
    Get all messages in a thread.
    """
    try:
        # First check if the thread exists and user has access
        thread_query = select(DbThread).where(
            and_(
                DbThread.id == thread_id,
                DbThread.addresses_with_access.any(
                    DbEmailAddress.address == user_email)
            )
        )

        thread_result = await session.execute(thread_query)
        thread = thread_result.scalar_one_or_none()

        if not thread:
            raise HTTPException(
                status_code=404, detail="Thread not found or you don't have access to this thread.")

        # Get all emails in the thread using the relationship
        email_query = select(DbEmail).where(DbEmail.threadId == thread_id).options(
            selectinload(DbEmail.from_address),
            selectinload(DbEmail.to_addresses),
            selectinload(DbEmail.cc_addresses),
            selectinload(DbEmail.bcc_addresses),
            selectinload(DbEmail.reply_to_addresses)
        )
        results = await session.execute(email_query)
        emails = results.scalars().all()

        return emails
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Error fetching thread messages for thread {thread_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

'''
Test with:
curl -X GET "http://localhost:8000/mail/threads?page=1&limit=10" \
    -H "Authorization: Bearer <token>"
'''


@router.get("/threads", response_model=list[Thread])
async def get_user_threads(page: int, limit: int, session: SessionDep, user_email: TokenDep):
    """
    Get paginated threads with their associated emails.
    """
    try:
        offset = (page - 1) * limit
        # Get threads where the user has access - using join for better performance
        # Include emails with their related addresses
        query = (
            select(DbThread)
            .join(address_has_threads)
            .join(DbEmailAddress)
            .where(DbEmailAddress.address == user_email)
            .options(
                selectinload(DbThread.emails).selectinload(
                    DbEmail.from_address),
                selectinload(DbThread.emails).selectinload(
                    DbEmail.to_addresses),
                selectinload(DbThread.emails).selectinload(
                    DbEmail.cc_addresses),
                selectinload(DbThread.emails).selectinload(
                    DbEmail.bcc_addresses),
                selectinload(DbThread.emails).selectinload(
                    DbEmail.reply_to_addresses)
            )
            .offset(offset)
            .limit(limit)
            .order_by(DbThread.lastMessageDate.desc())
        )

        results = await session.execute(query)
        threads = results.scalars().all()
        return threads
    except Exception as e:
        logger.error(f"Error fetching user threads: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


'''
Test with:
curl -X GET "http://localhost:8000/mail/threads/count?status=inbox" \
    -H "Authorization: Bearer <token>"
curl -X GET "http://localhost:8000/mail/threads/count?status=draft" \
    -H "Authorization: Bearer <token>"
curl -X GET "http://localhost:8000/mail/threads/count?status=sent" \
    -H "Authorization: Bearer <token>"
'''
# get the email count for threads with different statuses


@router.get("/threads/count")
async def get_thread_counts(status: str, session: SessionDep, user_email: TokenDep):
    """
    Get the count of threads based on their status.
    """
    try:
        # More efficient join-based query
        base_query = select(func.count(DbThread.id)).select_from(
            DbThread.join(address_has_threads).join(DbEmailAddress)
        ).where(DbEmailAddress.address == user_email)

        if status == "inbox":
            query = base_query.where(DbThread.inboxStatus is True)
        elif status == "draft":
            query = base_query.where(DbThread.draftStatus is True)
        elif status == "sent":
            query = base_query.where(DbThread.sentStatus is True)
        else:
            raise HTTPException(
                status_code=400, detail="Invalid status. Must be 'inbox', 'draft', or 'sent'.")

        results = await session.execute(query)
        count = results.scalar_one()
        return {"count": count}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching thread counts for status {status}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

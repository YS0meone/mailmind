from fastapi import APIRouter
from fastapi.exceptions import HTTPException
from app.logger_config import get_logger
from app.api.dep import SessionDep, TokenDep
from app.models import ReplyEmail, Thread, DbThread, DbEmail, Email, DbEmailAddress, address_has_threads
from sqlalchemy import and_, select, func
from sqlalchemy.orm import selectinload
import httpx
from app.core.config import settings
from app.crud import get_aurinko_token

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


@router.post("/thread/{message_id}/reply")
async def reply_to_message(message_id: str, reply_email: ReplyEmail, session: SessionDep, user_email: TokenDep):
    """
    Reply to a message.
    """
    try:
        aurinko_token = await get_aurinko_token(session, user_email)
        if not aurinko_token:
            raise HTTPException(
                status_code=401, detail="Unauthorized. Please login again.")
        # logger.info(f"message_id: {message_id}")
        # Build minimal payload that aligns with Aurinko expectations
        def _addr(a):
            return {"address": a.address, "name": a.name} if a else None

        payload: dict = {"body": reply_email.body}
        if reply_email.to:
            payload["to"] = [_addr(a) for a in reply_email.to]
        if reply_email.cc:
            payload["cc"] = [_addr(a) for a in reply_email.cc]
        if reply_email.bcc:
            payload["bcc"] = [_addr(a) for a in reply_email.bcc]

        logger.info(
            f"Replying via Aurinko id hex={message_id} payloadKeys={list(payload.keys())}")
        async with httpx.AsyncClient() as client:
            url = f"{settings.AURINKO_BASE_URL}/email/messages/{message_id}/reply?bodyType=text"
            response = await client.post(url, headers={"Authorization": f"Bearer {aurinko_token}"}, json=payload)
            if response.status_code == 200:
                return {
                    "message": "Message replied successfully",
                    "aurinkoMessageIdHex": message_id,
                    "aurinkoMessageIdDec": message_id,
                }
            else:
                logger.error(
                    f"Aurinko reply failed {response.status_code}: {response.text}")
                detail = response.text
                try:
                    detail_json = response.json()
                    detail = detail_json.get(
                        "message") or detail_json.get("detail") or detail
                except Exception:
                    pass
                raise HTTPException(
                    status_code=response.status_code, detail=detail)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error replying to message {message_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


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


@router.get("/thread/{thread_id}", response_model=Thread)
async def get_single_thread(thread_id: int, session: SessionDep, user_email: TokenDep):
    """
    Get a single thread by ID.
    """
    try:
        # Query for the specific thread with access check
        query = (
            select(DbThread)
            .join(address_has_threads, DbThread.id == address_has_threads.c.thread_id)
            .join(DbEmailAddress, address_has_threads.c.address_id == DbEmailAddress.id)
            .where(
                and_(
                    DbThread.id == thread_id,
                    DbEmailAddress.address == user_email
                )
            )
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
        )

        result = await session.execute(query)
        thread = result.scalar_one_or_none()

        if not thread:
            raise HTTPException(
                status_code=404,
                detail="Thread not found or you don't have access to this thread."
            )

        # Convert to Pydantic model
        return Thread(
            id=thread.id,
            subject=thread.subject,
            lastMessageDate=thread.lastMessageDate,
            done=thread.done,
            brief=thread.brief,
            inboxStatus=thread.inboxStatus,
            draftStatus=thread.draftStatus,
            sentStatus=thread.sentStatus,
            emails=thread.emails
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching thread {thread_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

# curl -X GET -H 'Authorization: Bearer WPXcOzlT3vNjp0R--p5IkS6u-dypq9XxRvdaVLcoBL8' \
#     https://api.aurinko.io/v1/email/conversations/1988b48816197963


# curl -H 'Authorization: Bearer WPXcOzlT3vNjp0R--p5IkS6u-dypq9XxRvdaVLcoBL8' \
# -X POST https://api.aurinko.io/v1/email/messages/1988b48816197963/reply?bodyType=text \
# -d '{
#     "subject": "RE: XXOO",
#     "body": "mua",
#     "to": [{"address": "nikkiwu0128@gmail.com"}]
#     "cc": []
#     }'


# curl -X POST 'https://api.aurinko.io/v1/email/messages/1988b48816197963/reply?bodyType=text' \
#   -H 'Authorization: Bearer WPXcOzlT3vNjp0R--p5IkS6u-dypq9XxRvdaVLcoBL8' \
#   -H 'Content-Type: application/json' \
#   --data '{"subject":"RE: XXOO","body":"mua","to":[{"address":"nikkiwu0128@gmail.com"}],"cc":[],"bcc":[]}'

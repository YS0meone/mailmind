from asyncio import sleep
from datetime import timedelta
from fastapi import APIRouter, Request, BackgroundTasks
from fastapi.responses import RedirectResponse
from app.core.config import settings
from urllib.parse import urlencode
import httpx
from fastapi.exceptions import HTTPException
from app.logger_config import get_logger
from app.api.dep import SessionDep, TokenDep
from app.models import Thread, DbThread, DbEmail, Email
from sqlalchemy import insert, select, func
from app.crud import upsert_user, sync_emails_and_threads
from app.core.security import create_access_token
from app.core.db import AsyncSessionLocal, engine

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
async def get_thread_messages(thread_id: str, session: SessionDep, _: TokenDep):
    """
    Get all messages in a thread.
    """
    # select all messages in the thread where the user is involved
    query = select(DbEmail).where(
        DbThread.id == thread_id,
    )
    results = await session.execute(query)
    emails = results.scalars().all()
    
    if not emails:
        raise HTTPException(status_code=404, detail="Thread not found or you are not involved in this thread.")
    
    return emails


'''
Test with:
curl -X GET "http://localhost:8000/mail/threads?page=1&limit=10" \
   -H "Authorization: Bearer <token>"
'''
@router.get("/threads", response_model=list[Thread])
async def get_user_threads(page: int, limit: int, session: SessionDep, user_email: TokenDep):
    """
    Get paginated threads.
    """
    offset = (page - 1) * limit
    # select all threads whose involvedEmails contains the user email
    query = select(DbThread).where(DbThread.involvedEmails.contains([user_email])).offset(offset)
    query = query.limit(limit)
    results = await session.execute(query)
    threads = results.scalars().all()
    return threads


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
    if status == "inbox":
        query = select(func.count()).where(
            DbThread.involvedEmails.contains([user_email]),
            DbThread.inboxStatus == True
        )
    elif status == "draft":
        query = select(func.count()).where(
            DbThread.involvedEmails.contains([user_email]),
            DbThread.draftStatus == True
        )
    elif status == "sent":
        query = select(func.count()).where(
            DbThread.involvedEmails.contains([user_email]),
            DbThread.sentStatus == True
        )
    else:
        raise HTTPException(status_code=400, detail="Invalid status. Must be 'inbox', 'draft', or 'sent'.")
    results = await session.execute(query)
    count = results.scalar_one()
    return {"count": count}


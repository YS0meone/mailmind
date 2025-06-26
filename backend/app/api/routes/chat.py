from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.api.dep import SessionDep, TokenDep
from app.services.rag_service import rag_service
from app.logger_config import get_logger

logger = get_logger(__name__)

router = APIRouter(
    prefix="/chat",
    tags=["chat"]
)


class ChatMessage(BaseModel):
    message: str


class EmailSource(BaseModel):
    email_id: str
    thread_id: str
    subject: str
    from_address: str
    from_name: str
    sent_at: str


class ChatResponse(BaseModel):
    response: str
    sources: list[EmailSource] = []


@router.post("/", response_model=ChatResponse)
async def chat_with_emails(
    chat_message: ChatMessage,
    session: SessionDep,
    user_email: TokenDep
):
    """Chat with your emails using AI"""
    try:
        logger.info(f"Chat request from {user_email}: {chat_message.message}")

        # Retrieve relevant emails
        relevant_emails = rag_service.query_emails(
            user_email=user_email,
            query=chat_message.message,
            limit=5
        )

        logger.info(f"Found {len(relevant_emails)} relevant emails")

        # Generate AI response
        ai_response = await rag_service.generate_response(
            user_query=chat_message.message,
            relevant_emails=relevant_emails
        )

        # Prepare sources for frontend
        sources = [
            EmailSource(
                email_id=email["email_id"],
                thread_id=email["thread_id"],
                subject=email["subject"],
                from_address=email["from_address"],
                from_name=email["from_name"],
                sent_at=email["sent_at"]
            )
            for email in relevant_emails
        ]

        return ChatResponse(
            response=ai_response,
            sources=sources
        )

    except Exception as e:
        logger.error(f"Error in chat endpoint: {e}")
        raise HTTPException(
            status_code=500, detail="Error processing chat request")


@router.post("/index")
async def index_user_emails(session: SessionDep, user_email: TokenDep):
    """Index user's emails for better search and chat functionality"""
    try:
        logger.info(f"Indexing emails for user: {user_email}")
        await rag_service.index_user_emails(session, user_email)
        return {"message": "Emails indexed successfully"}
    except Exception as e:
        logger.error(f"Error indexing emails: {e}")
        raise HTTPException(status_code=500, detail="Error indexing emails")


@router.get("/status")
async def get_chat_status(user_email: TokenDep):
    """Get chat service status for the user"""
    try:
        indexed_count = len(rag_service.indexed_emails.get(user_email, []))
        has_openai_key = bool(rag_service.openai_api_key)

        return {
            "indexed_emails": indexed_count,
            "ai_enabled": has_openai_key,
            "status": "ready" if has_openai_key and indexed_count > 0 else "not_ready"
        }
    except Exception as e:
        logger.error(f"Error getting chat status: {e}")
        raise HTTPException(
            status_code=500, detail="Error getting chat status")

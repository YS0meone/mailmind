from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from app.api.dep import SessionDep, TokenDep
from app.logger_config import get_logger
from app.services.chat_graph import chat_app, llm_test
from fastapi.responses import StreamingResponse
import json

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
    user_email: TokenDep,
):
    """Chat with your emails using AI via LangGraph RAG."""
    try:
        logger.info(f"Chat request from {user_email}: {chat_message.message}")
        result = await chat_app.ainvoke({"query": chat_message.message, "user_email": user_email})
        ans = (result.get("answer", "") or "")
        logger.info(
            "Chat answer ready len=%d preview=%s",
            len(ans),
            ans[:200].replace("\n", " ")
        )
        sources = [
            EmailSource(
                email_id=str(s.get("email_id")),
                thread_id=str(s.get("thread_id")),
                subject=s.get("subject", ""),
                from_address="",
                from_name="",
                sent_at=str(s.get("sent_at", "")),
            )
            for s in result.get("sources", [])
        ]
        return ChatResponse(response=ans, sources=sources)
    except Exception as e:
        logger.error(f"Error in chat endpoint: {e}")
        raise HTTPException(
            status_code=500, detail="Error processing chat request")


# Indexing endpoints disabled for now


@router.get("/status")
async def get_chat_status(user_email: TokenDep):
    """Simple readiness indicator for chat (checks for API key)."""
    try:
        from app.core.config import settings
        has_openai_key = bool(settings.OPENAI_API_KEY)
        return {"ai_enabled": has_openai_key, "status": "ready" if has_openai_key else "not_ready"}
    except Exception as e:
        logger.error(f"Error getting chat status: {e}")
        raise HTTPException(
            status_code=500, detail="Error getting chat status")


@router.post("/stream")
async def chat_stream(
    chat_message: ChatMessage,
    session: SessionDep,
    user_email: TokenDep,
):
    """Stream a chat response (JSON lines)."""
    async def gen():
        try:
            logger.info(f"Chat stream request from {user_email}: {chat_message.message}")
            result = await chat_app.ainvoke({"query": chat_message.message, "user_email": user_email})
            ans = (result.get("answer", "") or "")
            logger.info(
                "Chat stream final len=%d preview=%s",
                len(ans),
                ans[:200].replace("\n", " ")
            )
            yield json.dumps({"type": "final", "data": {"answer": ans, "sources": result.get("sources", [])}}) + "\n"
        except Exception as e:
            logger.error(f"Error in chat stream endpoint: {e}")
            yield json.dumps({"type": "error", "message": str(e)}) + "\n"

    return StreamingResponse(gen(), media_type="application/json")


@router.get("/health")
async def chat_health():
    """Basic LLM health check; returns a short model response."""
    out = llm_test("Say 'pong' if you can read this.")
    return {"ok": bool(out), "answer": out[:200]}

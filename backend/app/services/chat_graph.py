from typing import Any, Dict, List
from langgraph.graph import StateGraph, END
from langchain.chat_models import init_chat_model
from langchain_core.messages import SystemMessage, HumanMessage
from app.core.config import settings
from app.services.vector_store import get_vector_store
from app.logger_config import get_logger
from app.core.config import settings
import os
import datetime

logger = get_logger(__name__)

os.environ["OPENAI_API_KEY"] = settings.OPENAI_API_KEY


def build_chat_graph() -> Any:
    """Build a simple LangGraph for email RAG: retrieve -> generate."""
    llm = init_chat_model(settings.OPENAI_MODEL, temperature=0)
    store = get_vector_store()
    retriever = store.as_retriever(search_kwargs={"k": 5})

    def retrieve(state: Dict[str, Any]) -> Dict[str, Any]:
        """Retrieve docs filtered by user_email from metadata."""
        user_email: str = state["user_email"]
        query: str = state["query"]
        logger.info(
            f"RAG retrieve start user={user_email} query='{query[:120]}'")
        # With Chroma, apply metadata filter via vector store directly for reliability
        # Try vector-store-native filter first; fallback to retriever with filter
        try:
            docs = store.similarity_search(
                query, k=5, filter={"user_email": user_email}
            )
        except Exception as e:
            logger.error("Error in similarity_search: %s", e)
            retriever.search_kwargs["filter"] = {"user_email": user_email}
            docs = retriever.get_relevant_documents(query)
        # Extra diagnostics: count totals and per-user filter for troubleshooting
        try:
            total = store._collection.count()  # type: ignore[attr-defined]
            # Chroma where filter for counting
            where = {"user_email": user_email}
            per_user = store._collection.count(
                where=where)  # type: ignore[attr-defined]
            logger.info(
                "RAG retrieve diag: total=%s per_user=%s user=%s", total, per_user, user_email
            )
        except Exception:
            pass
        logger.info(
            "RAG retrieve done: %d docs | subjects=%s",
            len(docs),
            [(getattr(d, 'metadata', {}) or {}).get('subject') for d in docs]
        )
        # IMPORTANT: carry forward original fields so downstream nodes can access them
        return {"docs": docs, "query": query, "user_email": user_email}

    def generate(state: Dict[str, Any]) -> Dict[str, Any]:
        docs = state.get("docs", [])
        query = state["query"]
        context = "\n\n".join(d.page_content for d in docs)
        logger.info(
            "RAG generate: context_chars=%d, num_docs=%d",
            len(context),
            len(docs),
        )
        system = "You are an email assistant. Answer strictly using the provided context."
        messages = [
            SystemMessage(content=system),
            HumanMessage(content=f"Question: {query}\n\nContext:\n{context}"),
        ]
        try:
            msg = llm.invoke(messages)
        except Exception as e:
            logger.error("LLM invoke failed: %s", e)
            return {"answer": "", "sources": []}
        ans = (msg.content or "").strip()
        logger.info("RAG generate: answer_chars=%d empty=%s",
                    len(ans), not bool(ans))
        sources: List[Dict[str, Any]] = []
        for d in docs:
            md = d.metadata or {}
            sources.append({
                "email_id": md.get("email_id"),
                "thread_id": md.get("thread_id"),
                "subject": md.get("subject"),
                "snippet": md.get("snippet"),
                "sent_at": md.get("sent_at"),
            })
        return {"answer": ans, "sources": sources}

    g = StateGraph(dict)
    g.add_node("retrieve", retrieve)
    g.add_node("generate", generate)
    g.set_entry_point("retrieve")
    g.add_edge("retrieve", "generate")
    g.add_edge("generate", END)
    return g.compile()


# Singleton compiled app
chat_app = build_chat_graph()


def llm_test(prompt: str = "Respond with the word 'pong'.") -> str:
    """Simple non-RAG LLM call to verify API key/model wiring."""
    try:
        llm = init_chat_model(settings.OPENAI_MODEL, temperature=0)
        now = datetime.datetime.utcnow().isoformat()
        messages = [
            SystemMessage(content="You are a helpful assistant."),
            HumanMessage(content=f"{prompt} UTC={now}"),
        ]
        msg = llm.invoke(messages)
        return (msg.content or "").strip()
    except Exception as e:
        logger.error("LLM test failed: %s", e)
        return ""

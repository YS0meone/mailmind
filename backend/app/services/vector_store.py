from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma
from app.core.config import settings
from app.logger_config import get_logger
from pathlib import Path
import os


logger = get_logger(__name__)


def get_vector_store(collection_name: str = "emails") -> Chroma:
    # Use a stable absolute directory so API and worker see the same data
    env_dir = os.getenv("CHROMA_PERSIST_DIR")
    default_dir = (Path(__file__).resolve(
    ).parents[2] / "chroma_langchain_db").as_posix()
    persist_dir = env_dir if env_dir else default_dir
    embeddings = OpenAIEmbeddings(
        model=settings.EMBEDDING_MODEL, api_key=settings.OPENAI_API_KEY
    )
    store = Chroma(
        collection_name=collection_name,
        embedding_function=embeddings,
        persist_directory=persist_dir,
    )
    # Lightweight debug to help diagnose zero-retrieval situations
    try:
        count = store._collection.count()  # type: ignore[attr-defined]
        logger.debug("Chroma store ready collection=%s dir=%s count=%s",
                     collection_name, persist_dir, count)
    except Exception:
        pass
    return store

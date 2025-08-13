from fastapi import FastAPI
from app.api.main import api_router
from app.core.config import settings
from .logger_config import setup_logging
from fastapi.middleware.cors import CORSMiddleware
from arq.connections import create_pool, RedisSettings
from contextlib import asynccontextmanager

setup_logging()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Lazy init: don't fail startup if Redis is unavailable
    app.state.arq = None
    app.state.redis_settings = RedisSettings.from_dsn(settings.REDIS_URL)
    try:
        # Optionally pre-warm here; we skip to avoid blocking startup
        pass
    finally:
        yield
        if getattr(app.state, "arq", None):
            await app.state.arq.close()


app = FastAPI(lifespan=lifespan)

# Add cors middleware if needed
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_URL],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)

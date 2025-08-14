from fastapi import FastAPI
from app.api.main import api_router
from app.core.config import settings
from .logger_config import setup_logging
from fastapi.middleware.cors import CORSMiddleware
from arq.connections import create_pool, RedisSettings
import redis.asyncio as redis
from contextlib import asynccontextmanager

setup_logging()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Strict init: require Redis at startup
    app.state.redis_settings = RedisSettings.from_dsn(settings.REDIS_URL)
    app.state.arq = await create_pool(app.state.redis_settings)
    # Sanity check
    await app.state.arq.ping()
    # Create a shared Redis client for API reads (e.g., /sync/status)
    app.state.redis = redis.from_url(settings.REDIS_URL)
    await app.state.redis.ping()
    try:
        yield
    finally:
        if getattr(app.state, "arq", None):
            await app.state.arq.close()
        if getattr(app.state, "redis", None):
            try:
                await app.state.redis.aclose()
            except Exception:
                pass


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

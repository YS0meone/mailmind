from fastapi import FastAPI, HTTPException, Request
from app.api.main import api_router
from app.core.config import settings
from .logger_config import setup_logging
from fastapi.middleware.cors import CORSMiddleware
from arq.connections import create_pool, RedisSettings
import redis.asyncio as redis
from contextlib import asynccontextmanager
from sqlalchemy import text
from app.core.db import engine

setup_logging()


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        app.state.redis_settings = RedisSettings.from_dsn(settings.REDIS_URL)
        app.state.arq = await create_pool(app.state.redis_settings)
        await app.state.arq.ping()

        app.state.redis = redis.from_url(settings.REDIS_URL)
        await app.state.redis.ping()
    except Exception as e:
        # log warning instead of exiting
        app.state.arq = None
        app.state.redis = None

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

# Configure CORS for frontend + dev + previews
cors_allowed_origins = [settings.FRONTEND_URL]
if settings.DEBUG:
    cors_allowed_origins.extend([
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ])

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_allowed_origins,
    allow_origin_regex=r"^https://.*\.vercel\.app$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)


@app.get("/healthz")
async def healthz() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/readyz")
async def readyz(request: Request) -> dict[str, str]:
    try:
        # Check Redis
        if getattr(request.app.state, "redis", None) is None:
            raise RuntimeError("redis not initialized")
        await request.app.state.redis.ping()

        # Check DB
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))

        return {"status": "ready"}
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=503, detail=f"not ready: {exc}")

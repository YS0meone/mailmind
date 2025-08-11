from fastapi import FastAPI
from app.api.main import api_router
from app.core.config import settings
from .logger_config import setup_logging
from fastapi.middleware.cors import CORSMiddleware

setup_logging()

app = FastAPI()

# Add cors middleware if needed
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_URL],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)

from fastapi import FastAPI
from app.api.main import api_router
from .logger_config import setup_logging
from fastapi.middleware.cors import CORSMiddleware

setup_logging()

app = FastAPI()

# Add cors middleware if needed
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust this to your needs
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)




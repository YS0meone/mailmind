from fastapi import APIRouter
from .routes import auth, mail, chat

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(mail.router)
api_router.include_router(chat.router)

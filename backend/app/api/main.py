from fastapi import APIRouter
from .routes import auth, mail, chat, sync, webhooks

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(mail.router)
api_router.include_router(chat.router)
api_router.include_router(sync.router)
api_router.include_router(webhooks.router)

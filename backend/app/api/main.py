from fastapi import APIRouter
from .routes import auth, mail

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(mail.router)




from fastapi import APIRouter, Request
from app.core.config import settings
import logging
from urllib.parse import urlencode
import httpx
import asyncio

logging.baseConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/auth",
    tags=["auth"]
)

@router.get("/redirect")
async def aurinko_redirect(request: Request):
    query_params = dict(request.query_params())
    redirect_url = f'{settings.AURINKO_BASE_URL}/auth/authorize/{urlencode(query_params)}'
    logger.info("Redirecting to the url: %s", redirect_url)
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(redirect_url)
            response.raise_for_status()
            logger.info("Replied with data %s", str(response))
            return response.json()
    except httpx.HTTPStatusError as e:
        logger.error("HTTP error %s - %s", e.response.status_code, e.response.text)
    except httpx.RequestError as e:
        logger.error("Request failed: %s", e)
    except Exception as e:
        logger.error("Unexpected error: %s", e)
    
        

@router.get("/callback")
async def aurinko_final_callback():
    pass
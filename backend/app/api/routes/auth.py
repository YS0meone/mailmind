from fastapi import APIRouter, Request
from fastapi.responses import RedirectResponse
from app.core.config import settings
import logging
from urllib.parse import urlencode
import httpx
from fastapi.exceptions import HTTPException

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/auth",
    tags=["auth"]
)


@router.get("/redirect")
async def aurinko_redirect(request: Request):
    query_params = dict(request.query_params)
    
    if not query_params:
        raise HTTPException(
            status_code=400, detail="No query parameters provided")
    redirect_url = f'{settings.AURINKO_BASE_URL}/auth/callback?{urlencode(query_params)}'
    logger.info("Redirecting to the url: %s", redirect_url)

    return RedirectResponse(url=redirect_url, status_code=307)


@router.get("/callback")
async def aurinko_final_callback(code: str, state: str):
    """
    Handle the final callback from Aurinko after authorization.
    This endpoint is called by Aurinko after the user has authorized the application.
    """
    logger.info("Received code: %s, state: %s", code, state)

    token_url = f'{settings.AURINKO_BASE_URL}/auth/token/{code}'

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                token_url,
                auth=(settings.AURINKO_CLIENT_ID,
                      settings.AURINKO_CLIENT_SECRET)
            )
            response.raise_for_status()
            logger.info("Token exchange successful")
            return response.json()
    except httpx.HTTPStatusError as e:
        logger.error("HTTP error %s - %s",
                     e.response.status_code, e.response.text)
        raise HTTPException(status_code=e.response.status_code,
                            detail="Failed to exchange code for token due to HTTP error")
    except httpx.RequestError as e:
        logger.error("Request failed: %s", e)
        raise HTTPException(
            status_code=500, detail="Failed to exchange code for token due to request error")
    except Exception as e:
        logger.error("Unexpected error: %s", e)
        raise HTTPException(
            status_code=500, detail="Failed to exchange code for token")

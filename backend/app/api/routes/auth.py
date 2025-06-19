from datetime import timedelta
from fastapi import APIRouter, Request
from fastapi.responses import RedirectResponse
from app.core.config import settings
from urllib.parse import urlencode
import httpx
from fastapi.exceptions import HTTPException
from app.logger_config import get_logger
from app.api.dep import SessionDep
from app.models import DbUser, User
from sqlalchemy import insert
from app.crud import upsert_user
from app.core.security import generate_access_token


logger = get_logger(__name__)

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

async def exchangeCodeForToken(code: str) -> dict | None:
    token_url = f"{settings.AURINKO_BASE_URL}/auth/token/{code}"
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                token_url,
                auth=(settings.AURINKO_CLIENT_ID, settings.AURINKO_CLIENT_SECRET)
            )
            response.raise_for_status()
            logger.info("Token exchange successful")
            return response.json()
    except httpx.HTTPStatusError as e:  
        logger.error("HTTP error %s - %s", e.response.status_code, e.response.text)
        raise HTTPException(status_code=e.response.status_code,
                            detail="Failed to exchange code for token due to HTTP error")
    except httpx.RequestError as e:
        logger.error("Request failed: %s", e)
        raise HTTPException(
            status_code=500, detail="Failed to exchange code for token due to request error")   

   
    

@router.get("/callback")
async def aurinko_final_callback(code: str, state: str, session: SessionDep):
    """
    Handle the final callback from Aurinko after authorization.
    This endpoint is called by Aurinko after the user has authorized the application.
    """
    logger.info("Received code: %s, state: %s", code, state)

    if not code:
        logger.error("No code provided in the callback")
        raise HTTPException(status_code=400, detail="No code provided in the callback")
    if not state:
        logger.error("No state provided in the callback")
        raise HTTPException(status_code=400, detail="No state provided in the callback")
    
    # Exchange the code for a token
    token_data = await exchangeCodeForToken(code)
    
    user_model = User(
        account_id = token_data.get("accountId"),
        account_token= token_data.get("accessToken"),
    )
    # create new user or update existing user in the database
    new_user = await upsert_user(session=session, user=user_model)

    if not new_user:
        logger.error("Failed to create or update user in the database")
        raise HTTPException(status_code=500, detail="Failed to create or update user in the database")

    logger.info("User %s created or updated successfully", new_user.account_id)

    # return an access token and redirect to the frontend
    expire_minutes = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = generate_access_token(new_user.account_id, expire_minutes)
    logger.info("Generated access token for user %s", new_user.account_id)

    redirect_url = f"{settings.FRONTEND_URL}/dashboard"
    # set http-only cookie with the access token
    response = RedirectResponse(url=redirect_url, status_code=307) 
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=True,
        samesite="Lax",  # Adjust as needed
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60  # Convert minutes to seconds
    )

    return {"message": "test insert user"}

    


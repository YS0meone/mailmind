from asyncio import sleep
from datetime import timedelta
from fastapi import APIRouter, Request, BackgroundTasks
from fastapi.responses import RedirectResponse
from app.core.config import settings
from urllib.parse import urlencode
import httpx
from fastapi.exceptions import HTTPException
from app.logger_config import get_logger
from app.api.dep import SessionDep, TokenDep
from app.models import DbUser, User
from app.crud import upsert_user, sync_emails_and_threads
from app.core.security import create_access_token
from app.core.db import AsyncSessionLocal
from sqlalchemy import select
# import json
# from pathlib import Path


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


async def init_sync_emails(user: DbUser):
    logger.info("Syncing emails for user %s", user.accountId)

    sync_url = f"{settings.AURINKO_BASE_URL}/email/sync"
    init_succeeded = False
    retry = 5
    try:
        async with httpx.AsyncClient() as client:
            while not init_succeeded and retry > 0:
                logger.info("Starting email sync for user %s", user.accountId)
                # Send a POST request to start the sync
                response = await client.post(
                    sync_url,
                    headers={
                        "Authorization": f"Bearer {user.accountToken}",
                    },
                    params={
                        "daysWithin": settings.AURINKO_SYNC_DAYS_WITHIN,
                    }
                )
                response.raise_for_status()
                # we check if the response has a field called ready that is true
                if response.json().get("ready", False):
                    init_succeeded = True
                    logger.info(
                        "Email sync initialization for user %s completed successfully", user.accountId)
                else:
                    logger.info(
                        "Email sync initialization for user %s is still in progress, waiting...", user.accountId)
                    # wait for 1 second before checking again
                    await sleep(1)
                    retry -= 1
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


async def increment_sync_updated(delta_token: str, access_token: str, records: list[dict]) -> str:
    logger.info("sync updated email incrementally for token: %s", delta_token)
    increment_url = f"{settings.AURINKO_BASE_URL}/email/sync/updated"
    current_delta_token = delta_token
    try:
        async with httpx.AsyncClient() as client:
            while current_delta_token:
                response = await client.get(
                    increment_url,
                    headers={
                        "Authorization": f"Bearer {access_token}",
                    },
                    params={
                        "deltaToken": current_delta_token
                    }
                )
                response.raise_for_status()
                logger.info("response received with delta token: %s",
                            current_delta_token)
                data = response.json()

                # Get the next delta token from the response
                next_delta_token = data.get("nextDeltaToken")
                page_token = data.get("nextPageToken")

                logger.info("current delta token: %s, next delta token: %s, next page token: %s",
                            current_delta_token, next_delta_token, page_token)

                # Add records from this page
                records.extend(data.get("records", []))
                logger.info("Fetched %d records", len(data.get("records", [])))

                # Handle pagination for the current delta token
                while page_token:
                    logger.info(
                        "Fetching next page of emails with page token: %s", page_token)
                    response = await client.get(
                        f"{settings.AURINKO_BASE_URL}/email/sync/updated",
                        headers={
                            "Authorization": f"Bearer {access_token}",
                        },
                        params={"pageToken": page_token}
                    )
                    response.raise_for_status()

                    data = response.json()
                    page_token = data.get("nextPageToken")
                    logger.info("next page token: %s", page_token)
                    records.extend(data.get("records", []))
                    logger.info("Fetched %d additional records",
                                len(data.get("records", [])))

                    # Update next_delta_token from paginated response if present
                    if data.get("nextDeltaToken"):
                        next_delta_token = data.get("nextDeltaToken")

                logger.info("Updated email for delta token %s completed with %d total records",
                            current_delta_token, len(records))

                # Break if no new delta token (no more updates)
                if not next_delta_token or next_delta_token == current_delta_token:
                    logger.info(
                        "No more updates available. Breaking sync loop.")
                    break

                # Move to next delta token
                current_delta_token = next_delta_token

            logger.info("All emails synced successfully for user")
            return current_delta_token

    except httpx.HTTPStatusError as e:
        logger.error("HTTP error %s - %s",
                     e.response.status_code, e.response.text)
        raise HTTPException(status_code=e.response.status_code,
                            detail="Failed to increment sync updated count due to HTTP error")
    except httpx.RequestError as e:
        logger.error("Request failed: %s", e)
        raise HTTPException(
            status_code=500, detail="Failed to increment sync updated count due to request error")


async def get_user_email_by_id(accountId: str) -> str | None:
    logger.info("Fetching user email for account ID: %s", accountId)
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                f"{settings.AURINKO_BASE_URL}/am/accounts/{accountId}",
                auth=(settings.AURINKO_CLIENT_ID,
                      settings.AURINKO_CLIENT_SECRET)
            )
            response.raise_for_status()
            user_data = response.json()
            return user_data.get("email")
        except httpx.HTTPStatusError as e:
            logger.error("HTTP error %s - %s",
                         e.response.status_code, e.response.text)
            raise HTTPException(status_code=e.response.status_code,
                                detail="Failed to get user email due to HTTP error")
        except httpx.RequestError as e:
            logger.error("Request failed: %s", e)
            raise HTTPException(
                status_code=500, detail="Failed to get user email due to request error")


async def sync_emails(user: User):
    records = []
    async with AsyncSessionLocal() as session:
        # create new user or update existing user in the database
        new_user = await upsert_user(session=session, user=user)

        if not new_user:
            logger.error("Failed to create or update user in the database")
            raise HTTPException(
                status_code=500, detail="Failed to create or update user in the database")

        logger.info("User %s created or updated successfully",
                    new_user.accountId)

        current_delta_token = new_user.lastDeltaToken

        if not current_delta_token:
            token_response = await init_sync_emails(new_user)
            logger.info("Email sync response: %s", token_response)

            if not token_response.get("ready"):
                logger.error(
                    "Email sync initialization failed for user %s", new_user.accountId)
                raise HTTPException(
                    status_code=500, detail="Email sync initialization failed")
            current_delta_token = token_response.get("syncUpdatedToken")
            logger.info(
                "Current delta token after initialization: %s", current_delta_token)

        # increment sync emails updated
        lastDeltaToken = await increment_sync_updated(
            delta_token=current_delta_token,
            access_token=new_user.accountToken,
            records=records
        )

        logger.info("Last delta token after sync: %s", lastDeltaToken)

        # update the user with the last delta token
        user.lastDeltaToken = lastDeltaToken
        updated_user = await upsert_user(session=session, user=user)
        logger.info("User %s updated with last delta token: %s",
                    updated_user.accountId, updated_user.lastDeltaToken)

        # # load all email records into a json file
        # with open(Path(__file__).parent / "emails.json", "w") as f:
        #     json.dump(records, f, indent=4)
        #     logger.info("Saved %d email records to emails.json", len(records))

        # sync emails and threads
        try:
            await sync_emails_and_threads(session, records, updated_user)
            logger.info(
                f"Successfully synced {len(records)} email records for user {updated_user.accountId}")
        except Exception as e:
            logger.error(
                f"Failed to sync emails and threads for user {updated_user.accountId}: {e}")
            # Don't raise here as this is a background task - just log the error

        # Index emails for RAG chat functionality
        try:
            from app.services.rag_service import rag_service
            await rag_service.index_user_emails(session, updated_user.email)
            logger.info(
                f"Successfully indexed emails for RAG for user {updated_user.email}")
        except Exception as e:
            logger.error(
                f"Failed to index emails for RAG for user {updated_user.email}: {e}")
            # Don't fail the sync if indexing fails


# async def insert_all_email_records(records: list[dict]):
#     if not records:
#         logger.info("No records to insert")
#         return
#     async with engine.begin() as conn:
#         pass

#     logger.info("Inserted %d email records into the database", len(records))

@router.get("/callback")
async def aurinko_final_callback(code: str, state: str, session: SessionDep, background_tasks: BackgroundTasks):
    """
    Handle the final callback from Aurinko after authorization.
    This endpoint is called by Aurinko after the user has authorized the application.
    """
    logger.info("Received code: %s, state: %s", code, state)

    if not code:
        logger.error("No code provided in the callback")
        raise HTTPException(
            status_code=400, detail="No code provided in the callback")
    if not state:
        logger.error("No state provided in the callback")
        raise HTTPException(
            status_code=400, detail="No state provided in the callback")

    # Exchange the code for a token
    token_data = await exchangeCodeForToken(code)

    # get user email
    user_email = await get_user_email_by_id(token_data.get("accountId"))
    logger.info("User email fetched: %s", user_email)
    if not user_email:
        logger.error("Failed to fetch user email for account ID: %s",
                     token_data.get("accountId"))
        raise HTTPException(
            status_code=500, detail="Failed to fetch user email")

    user = User(
        accountId=token_data.get("accountId"),
        accountToken=token_data.get("accessToken"),
        email=user_email,
    )

    # run background task to sync emails
    background_tasks.add_task(sync_emails, user)
    logger.info("Background task to sync emails added for user %s",
                user.accountId)

    # return an access token and redirect to the frontend
    expire_minutes = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(user.email, expire_minutes)
    logger.info("Generated access token for user %s: %s",
                user.accountId, access_token)

    redirect_url = f"{settings.FRONTEND_URL}/inbox"

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

    return response


@router.get("/me", response_model=User)
async def get_current_user(session: SessionDep, user_email: TokenDep):
    """
    Get current authenticated user information.
    """
    try:
        # Query the user by email
        user_query = select(DbUser).where(DbUser.email == user_email)
        result = await session.execute(user_query)
        db_user = result.scalar_one_or_none()

        if not db_user:
            raise HTTPException(status_code=404, detail="User not found")

        return User(
            id=db_user.id,
            accountId=db_user.accountId,
            accountToken=db_user.accountToken,
            email=db_user.email,
            lastDeltaToken=db_user.lastDeltaToken
        )
    except Exception as e:
        logger.error(f"Error fetching current user: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

from fastapi import APIRouter, Request, Response, HTTPException
from app.core.config import settings
from app.logger_config import get_logger
import hmac
import hashlib
from sqlalchemy import select
from app.core.db import AsyncSessionLocal
from app.models import DbUser

logger = get_logger(__name__)

router = APIRouter(prefix="/webhooks/aurinko", tags=["webhooks"])


def _verify_signature(timestamp: str | None, signature: str | None, raw_body: bytes) -> bool:
    if not timestamp or not signature:
        return False
    base = f"v0:{timestamp}:".encode() + raw_body
    digest = hmac.new(settings.AURINKO_SIGNING_SECRET.encode(),
                      base, hashlib.sha256).hexdigest()
    # constant-time compare
    return hmac.compare_digest(digest, signature)


@router.post("")
async def aurinko_webhook(request: Request):
    # Challenge for notification URL validation
    token = request.query_params.get("validationToken")
    if token:
        return Response(content=token, media_type="text/plain")

    # Verify signature
    ts = request.headers.get("X-Aurinko-Request-Timestamp")
    sig = request.headers.get("X-Aurinko-Signature")
    raw = await request.body()
    if not _verify_signature(ts, sig, raw):
        logger.warning("Invalid webhook signature")
        raise HTTPException(status_code=401, detail="Invalid signature")

    try:
        payload = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON")

    # Inspect payload (subscription/accountId/resource)
    logger.info("Received Aurinko webhook: %s", payload)

    # Enqueue a sync for the associated account if we can map it
    account_id = payload.get("accountId")
    if account_id is not None:
        async with AsyncSessionLocal() as session:
            result = await session.execute(select(DbUser).where(DbUser.accountId == account_id))
            user = result.scalar_one_or_none()
            if user:
                try:
                    if getattr(request.app.state, "arq", None) is None:
                        from arq.connections import create_pool
                        request.app.state.arq = await create_pool(request.app.state.redis_settings)
                    await request.app.state.arq.enqueue_job("sync_emails_task", user.email)
                    logger.info("Enqueued sync for account %s (%s)",
                                account_id, user.email)
                except Exception as e:
                    logger.error(
                        "Failed to enqueue sync for account %s: %s", account_id, e)
            else:
                logger.warning("No user found for accountId %s", account_id)

    # Acknowledge
    return Response(status_code=200)

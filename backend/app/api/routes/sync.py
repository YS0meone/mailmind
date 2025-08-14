from fastapi import APIRouter, Request
from app.api.dep import TokenDep

router = APIRouter(prefix="/sync", tags=["sync"])


@router.get("/status")
async def sync_status(request: Request, user_email: TokenDep):
    data = await request.app.state.redis.hgetall(f"sync:status:{user_email}")
    if not data:
        return {"state": "idle"}

    # decode bytes to strings
    return {k.decode(): v.decode() for k, v in data.items()}

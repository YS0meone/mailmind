from fastapi import APIRouter, Request
from app.api.dep import TokenDep

router = APIRouter(prefix="/sync", tags=["sync"])


@router.get("/status")
async def sync_status(request: Request, user_email: TokenDep):
    arq = getattr(request.app.state, "arq", None)
    if arq is None:
        # lazy create a pool if not present
        from arq.connections import create_pool
        request.app.state.arq = await create_pool(request.app.state.redis_settings)
        arq = request.app.state.arq

    # read status hash from redis
    data = await arq.connection.hgetall(f"sync:status:{user_email}")
    if not data:
        return {"state": "idle"}

    # decode bytes to strings
    return {k.decode(): v.decode() for k, v in data.items()}

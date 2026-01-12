from fastapi import APIRouter, status
from fastapi.responses import JSONResponse

from app.database.redis import redis_db

router = APIRouter(tags=["health"])


@router.get("/health")
async def health_check():
    is_healthy = redis_db.async_client is not None and redis_db.token_bucket_lua_sha is not None

    return JSONResponse(
        status_code=status.HTTP_200_OK if is_healthy else status.HTTP_503_SERVICE_UNAVAILABLE,
        content={
            "status": "healthy" if is_healthy else "unhealthy",
            "redis_connected": redis_db.async_client is not None,
            "script_loaded": redis_db.token_bucket_lua_sha is not None
        }
    )

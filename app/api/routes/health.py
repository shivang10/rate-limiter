from fastapi import APIRouter, status
from fastapi.responses import JSONResponse

from app.database.redis import redis_connection

router = APIRouter(tags=["health"])


@router.get("/health")
async def health_check():
    is_healthy = redis_connection.async_client is not None and 'token_bucket' in redis_connection.script_shas

    return JSONResponse(
        status_code=status.HTTP_200_OK if is_healthy else status.HTTP_503_SERVICE_UNAVAILABLE,
        content={
            "status": "healthy" if is_healthy else "unhealthy",
            "redis_connected": redis_connection.async_client is not None,
            "scripts_loaded": list(redis_connection.script_shas.keys())
        }
    )

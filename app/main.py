import logging
import socket
from contextlib import asynccontextmanager

from fastapi import FastAPI, Depends, status
from fastapi.responses import JSONResponse

from app.db.redis_session import connect_async_redis, close_redis, redis_db
from app.dependencies.token_bucket_rate_limit_dependency import token_bucket_rate_limit_dependency

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app_: FastAPI):
    logger.info("Starting application...")
    try:
        await connect_async_redis()
        logger.info("Application startup complete")
    except Exception as e:
        logger.error(f"Failed to start application: {e}")
        raise

    yield

    logger.info("Shutting down application...")
    await close_redis()
    logger.info("Application shutdown complete")


app = FastAPI(
    title="Rate Limiter API",
    version="1.0.0",
    lifespan=lifespan
)


@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "redis_connected": redis_db.async_client is not None,
        "script_loaded": redis_db.token_bucket_lua_sha is not None,
        "script_sha": redis_db.token_bucket_lua_sha
    }


@app.get("/token-bucket", dependencies=[Depends(token_bucket_rate_limit_dependency)])
async def token_bucket():
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={"message": "Request successful",
                 "handled_by_container": socket.gethostname()}
    )


@app.exception_handler(429)
async def rate_limit_handler(request, exc):
    return JSONResponse(
        status_code=429,
        content={
            "error": "Rate limit exceeded",
            "message": str(exc.detail),
            "retry_after": "1 second"
        },
        headers={"Retry-After": "1"}
    )

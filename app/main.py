# Updated main.py
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI

from app.database.redis import connect_redis, disconnect_redis
from app.api.routes import health, token_bucket_route

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def application_lifespan(app_: FastAPI):
    logger.info("Starting application...")
    try:
        await connect_redis()
        logger.info("Application startup complete")
    except Exception as e:
        logger.error(f"Failed to start: {e}", exc_info=True)
        logger.warning("Starting in degraded mode")

    yield

    logger.info("Shutting down...")
    await disconnect_redis()


app = FastAPI(
    title="Rate Limiter API",
    version="1.0.0",
    lifespan=application_lifespan
)

# Include routers
app.include_router(health.router)
app.include_router(token_bucket_route.router)

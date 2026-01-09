import logging
import socket
from typing import Optional

import redis
import redis.asyncio as redis_asyncio
from fastapi import HTTPException, status

from config import settings

logger = logging.getLogger(__name__)


class Redis:
    sync_client: Optional[redis.Redis] = None
    async_client: Optional[redis_asyncio.Redis] = None


redis_db = Redis()


def connect_sync_redis():
    try:
        if not settings.redis_host:
            raise ValueError("Redis host is not configured")

        logger.info(
            f"Connecting to Redis at {settings.redis_host}:{settings.redis_port}")

        redis_db.sync_client = redis.Redis(
            host=settings.redis_host,
            port=settings.redis_port,
            db=settings.redis_db,
            password=settings.redis_password if settings.redis_password else None,
            decode_responses=True,
            socket_timeout=5,
            socket_connect_timeout=5
        )

        redis_db.sync_client.ping()
        logger.info("Synchronous Redis connection successful")
        return redis_db.sync_client

    except socket.gaierror as e:
        logger.error(
            f"Redis hostname resolution failed: {settings.redis_host}. Error: {str(e)}")
        logger.warning(
            "Application will continue without synchronous Redis functionality")
    except (redis.ConnectionError, redis.RedisError) as e:
        logger.error(f"Synchronous Redis connection error: {str(e)}")
        logger.warning(
            "Application will continue without synchronous Redis functionality")
    except Exception as e:
        logger.error(
            f"Unexpected error connecting to synchronous Redis: {str(e)}")
        logger.warning(
            "Application will continue without synchronous Redis functionality")

    return None


async def connect_async_redis():
    try:
        if not settings.redis_host:
            raise ValueError("Redis host is not configured")
        redis_db.async_client = redis_asyncio.Redis(
            host=settings.redis_host,
            port=settings.redis_port,
            db=settings.redis_db,
            password=settings.redis_password if settings.redis_password else None,
            decode_responses=True,
            socket_timeout=5,
            socket_connect_timeout=5
        )

        await redis_db.async_client.ping()
        logger.info("Asynchronous Redis connection successful")
        return redis_db.async_client

    except socket.gaierror as e:
        logger.error(
            f"Redis hostname resolution failed: {settings.redis_host}. Error: {str(e)}")
        logger.warning(
            "Application will continue without asynchronous Redis functionality")
    except (redis.ConnectionError, redis.RedisError) as e:
        logger.error(f"Asynchronous Redis connection error: {str(e)}")
        logger.warning(
            "Application will continue without asynchronous Redis functionality")
    except Exception as e:
        logger.error(
            f"Unexpected error connecting to asynchronous Redis: {str(e)}")
        logger.warning(
            "Application will continue without asynchronous Redis functionality")

    return None


async def close_redis():
    try:
        if redis_db.sync_client:
            redis_db.sync_client.close()
            logger.info("Closed synchronous Redis connection")

        if redis_db.async_client:
            await redis_db.async_client.close()
            logger.info("Closed asynchronous Redis connection")
    except Exception as e:
        logger.error(f"Error closing Redis connections: {str(e)}")


def get_redis() -> redis.Redis:
    if redis_db.sync_client is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Redis connection not available."
        )
    return redis_db.sync_client


async def get_async_redis() -> redis_asyncio.Redis:
    if redis_db.async_client is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Redis connection not available."
        )
    return redis_db.async_client

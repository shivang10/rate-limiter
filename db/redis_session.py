from __future__ import annotations

import logging
import socket
from typing import Optional

import redis
import redis.asyncio as redis_asyncio
from fastapi import HTTPException, status

from config import settings
from .lua import load_lua_script

logger = logging.getLogger(__name__)


class Redis:
    async_client: Optional[redis_asyncio.Redis] = None


TOKEN_BUCKET_LUA = load_lua_script("token_bucket.lua")

token_bucket_sha: str | None = None
redis_db = Redis()


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
        global token_bucket_sha

        await redis_db.async_client.ping()
        logger.info("Asynchronous Redis connection successful")
        token_bucket_sha = await redis_db.async_client.script_load(TOKEN_BUCKET_LUA)
        logger.info(
            f"Token bucket lua script loaded with SHA: {token_bucket_sha}")

        if token_bucket_sha is None:
            raise
        return redis_db.async_client

    except socket.gaierror as e:
        logger.error(
            f"Redis hostname resolution failed: {settings.redis_host}. Error: {str(e)}")
        raise
    except (redis.ConnectionError, redis.RedisError) as e:
        logger.error(f"Asynchronous Redis connection error: {str(e)}")
        raise
    except Exception as e:
        logger.error(
            f"Unexpected error connecting to asynchronous Redis: {str(e)}")
        raise


async def close_redis():
    try:
        if redis_db.async_client:
            await redis_db.async_client.close()
            logger.info("Closed asynchronous Redis connection")
    except Exception as e:
        logger.error(f"Error closing Redis connections: {str(e)}")


async def get_async_redis() -> redis_asyncio.Redis:
    if redis_db.async_client is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Redis connection not available."
        )
    return redis_db.async_client

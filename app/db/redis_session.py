from __future__ import annotations

import logging
import socket
from typing import Optional

import redis
from redis.asyncio.cluster import RedisCluster, ClusterNode
import redis.asyncio as redis_asyncio
from fastapi import HTTPException, status

from app.config import settings
from app.db.lua import load_lua_script

logger = logging.getLogger(__name__)


class Redis:
    def __init__(self):
        self.async_client: Optional[RedisCluster] = None
        self.token_bucket_lua_sha: Optional[str] = None


TOKEN_BUCKET_LUA = load_lua_script("token_bucket.lua")
redis_db = Redis()


async def connect_async_redis():
    try:
        if not settings.redis_host_node_1:
            raise ValueError("Redis cluster nodes are not configured")

        startup_nodes = [
            ClusterNode(settings.redis_host_node_1,
                        settings.redis_port_node_1),
            ClusterNode(settings.redis_host_node_2,
                        settings.redis_port_node_2),
            ClusterNode(settings.redis_host_node_3,
                        settings.redis_port_node_3),
            ClusterNode(settings.redis_host_node_4,
                        settings.redis_port_node_4),
            ClusterNode(settings.redis_host_node_5,
                        settings.redis_port_node_5),
            ClusterNode(settings.redis_host_node_6,
                        settings.redis_port_node_6)
        ]

        redis_db.async_client = redis_asyncio.RedisCluster(
            startup_nodes=startup_nodes,
            password=settings.redis_password if settings.redis_password else None,
            decode_responses=True,
            socket_timeout=5,
            socket_connect_timeout=5,
        )

        await redis_db.async_client.ping()
        logger.info(
            f"Redis cluster connection successful: {settings.redis_host_node_1}:{settings.redis_port_node_1}, "
            f"{settings.redis_host_node_2}:{settings.redis_port_node_2}, "
            f"{settings.redis_host_node_3}:{settings.redis_port_node_3}, "
            f"{settings.redis_host_node_4}:{settings.redis_port_node_4}, "
            f"{settings.redis_host_node_5}:{settings.redis_port_node_5}, "
            f"{settings.redis_host_node_6}:{settings.redis_port_node_6}")

        redis_db.token_bucket_lua_sha = await redis_db.async_client.script_load(TOKEN_BUCKET_LUA)
        logger.info(
            f"Token bucket Lua script loaded with SHA: {redis_db.token_bucket_lua_sha}")

        return redis_db.async_client

    except socket.gaierror as e:
        logger.error(
            f"Redis hostname resolution failed: {settings.redis_host}. Error: {e}")
        raise
    except (redis.ConnectionError, redis.RedisError) as e:
        logger.error(f"Redis connection error: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error connecting to Redis: {e}")
        raise


async def close_redis():
    try:
        if redis_db.async_client:
            await redis_db.async_client.aclose()
            logger.info("Redis connection closed")
    except Exception as e:
        logger.error(f"Error closing Redis connection: {e}")


async def get_async_redis() -> RedisCluster:
    if redis_db.async_client is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Redis connection not available"
        )
    return redis_db.async_client

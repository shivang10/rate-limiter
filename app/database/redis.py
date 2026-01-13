from __future__ import annotations

import logging
import socket
from typing import Optional

import redis
from redis.asyncio.cluster import RedisCluster, ClusterNode
import redis.asyncio as redis_asyncio
from fastapi import HTTPException, status

from app.config import settings
from app.database.lua import load_lua_script

logger = logging.getLogger(__name__)


class RedisConnection:
    def __init__(self):
        self.async_client: Optional[RedisCluster] = None
        self.script_shas: dict[str, str] = {}


TOKEN_BUCKET_SCRIPT = load_lua_script("token_bucket.lua")
SLIDING_WINDOW_COUNTER_SCRIPT = load_lua_script("sliding_window_counter.lua")
redis_connection = RedisConnection()


async def connect_redis():
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

        redis_connection.async_client = redis_asyncio.RedisCluster(
            startup_nodes=startup_nodes,
            password=settings.redis_password if settings.redis_password else None,
            decode_responses=True,
            socket_timeout=5,
            socket_connect_timeout=5,
        )

        await redis_connection.async_client.ping()
        logger.info(
            f"Redis cluster connection successful: {settings.redis_host_node_1}:{settings.redis_port_node_1}, "
            f"{settings.redis_host_node_2}:{settings.redis_port_node_2}, "
            f"{settings.redis_host_node_3}:{settings.redis_port_node_3}, "
            f"{settings.redis_host_node_4}:{settings.redis_port_node_4}, "
            f"{settings.redis_host_node_5}:{settings.redis_port_node_5}, "
            f"{settings.redis_host_node_6}:{settings.redis_port_node_6}")

        token_bucket_sha = await redis_connection.async_client.script_load(TOKEN_BUCKET_SCRIPT)
        redis_connection.script_shas['token_bucket'] = token_bucket_sha
        logger.info(
            f"Token bucket Lua script loaded with SHA: {token_bucket_sha}")

        sliding_window_counter_sha = await redis_connection.async_client.script_load(SLIDING_WINDOW_COUNTER_SCRIPT)
        redis_connection.script_shas['sliding_window_counter'] = sliding_window_counter_sha
        logger.info(
            f"Sliding window counter Lua script loaded with SHA: {sliding_window_counter_sha}")

        return redis_connection.async_client

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


async def disconnect_redis():
    try:
        if redis_connection.async_client:
            await redis_connection.async_client.aclose()
            logger.info("Redis connection closed")
    except Exception as e:
        logger.error(f"Error closing Redis connection: {e}")


async def get_redis_client() -> RedisCluster:
    if redis_connection.async_client is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Redis connection not available"
        )
    return redis_connection.async_client

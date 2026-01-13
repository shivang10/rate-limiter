import logging
import time

import redis

from app.database.redis import redis_connection
from app.core.base import RateLimiterStrategy

logger = logging.getLogger(__name__)


class SlidingWindowCounterRateLimiter(RateLimiterStrategy):
    def __init__(self, redis_client, window_size_seconds: int, max_requests: int,  expiry_seconds: int):
        self.redis_client = redis_client
        self.window_size_seconds = window_size_seconds
        self.max_requests = max_requests
        self.current_window = time.time()
        self.request_count = 0
        self.previous_count = 0
        self.ttl_seconds = expiry_seconds

    async def is_request_allowed(self, key: str) -> bool:
        try:
            node_info = await redis_connection.async_client.cluster_keyslot(key)
            logger.debug(f"Key '{key}' will be handled by node: {node_info}")
        except Exception as e:
            logger.warning(f"Could not determine node for key '{key}': {e}")

        now = time.time()

        try:
            result = await redis_connection.async_client.evalsha(
                redis_connection.script_shas['sliding_window_counter'],
                1,
                key,
                self.window_size_seconds,
                self.max_requests,
                int(now),
                self.ttl_seconds,
            )

        except redis.exceptions.NoScriptError:
            logger.error(f"Lua script not loaded. Reloading...")
            sliding_window_counter_sha = await redis_connection.async_client.script_load(
                redis_connection.SLIDING_WINDOW_COUNTER_SCRIPT)
            redis_connection.script_shas['sliding_window_counter'] = sliding_window_counter_sha
            result = await redis_connection.async_client.evalsha(
                redis_connection.script_shas['sliding_window_counter'],
                1,
                key,
                self.window_size_seconds,
                self.max_requests,
                int(now),
                self.ttl_seconds,
            )
        except redis.exceptions.RedisError as e:
            logger.error(f"Redis error during rate limit check: {e}")
            return True
        except Exception as e:
            logger.error(
                f"Error in SlidingWindowCounterRateLimiter for key '{key}': {e}")
            return True

        allowed, request_count = result

        if allowed == 0:
            logger.info(
                f"Rate limit exceeded for key: {key}, count: {request_count}/{self.max_requests}")
        else:
            logger.debug(
                f"Request allowed for key: {key}, count: {request_count}/{self.max_requests}")

        return allowed == 1

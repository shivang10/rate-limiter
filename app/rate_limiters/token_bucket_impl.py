import logging
import time

import redis

from app.db.redis_session import redis_db, TOKEN_BUCKET_LUA
from app.rate_limiters.rate_limiter_base import RateLimiterBase

logger = logging.getLogger(__name__)


class TokenBucketImpl(RateLimiterBase):
    def __init__(self, refill_rate: int, bucket_capacity: int, redis_client: redis.Redis, ttl_seconds: int, cost: int):
        self.refill_rate = refill_rate
        self.bucket_capacity = bucket_capacity
        self.redis_client = redis_client
        self.ttl_seconds = ttl_seconds or int(bucket_capacity / refill_rate)
        self.cost = cost

    async def allow_request(self, key: str) -> bool:
        if not key:
            logger.warning("Rate limit check called with empty key")
            return False

        now = int(time.time())

        try:
            # node_info = await self._get_node_for_key(key)
            node_info = await redis_db.async_client.cluster_keyslot(key)
            logger.info(f"Key '{key}' will be handled by node: {node_info}")

            result = await redis_db.async_client.evalsha(
                redis_db.token_bucket_lua_sha,
                1,
                key,
                self.bucket_capacity,
                self.refill_rate,
                now,
                self.cost,
                self.ttl_seconds,
            )
        except redis.exceptions.NoScriptError:
            logger.warning("Lua script not found in Redis, reloading...")
            redis_db.token_bucket_lua_sha = await redis_db.async_client.script_load(TOKEN_BUCKET_LUA)

            result = await redis_db.async_client.evalsha(
                redis_db.token_bucket_lua_sha,
                1,
                key,
                self.bucket_capacity,
                self.refill_rate,
                now,
                self.cost,
                self.ttl_seconds,
            )
        except redis.exceptions.RedisError as e:
            logger.error(f"Redis error during rate limit check: {e}")
            return True
        except Exception as e:
            logger.error(f"Unexpected error during rate limit check: {e}")
            return True

        allowed, remaining_tokens = result

        if allowed == 0:
            logger.debug(
                f"Rate limit exceeded for key: {key}, remaining tokens: {remaining_tokens}")

        return allowed == 1

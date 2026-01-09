import time

import redis

from db.redis_session import redis_db, token_bucket_sha

from rate_limiters.rate_limiter_base import RateLimiterBase


class TokenBucketImpl(RateLimiterBase):
    def __init__(self, refill_rate: int, bucket_capacity: int, redis_client: redis.Redis, ttl_seconds: int, cost: int):
        self.refill_rate = refill_rate
        self.bucket_capacity = bucket_capacity
        self.redis_client = redis_client
        self.ttl_seconds = ttl_seconds or int(bucket_capacity / refill_rate)
        self.cost = cost

    async def allow_request(self, key: str = None):
        now = int(time.time())

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
        allowed, _ = result
        return allowed == 1

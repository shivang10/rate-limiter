import time

import redis

from rate_limiters.rate_limiter_base import RateLimiterBase


class TokenBucketImpl(RateLimiterBase):
    def __init__(self, rate: int, bucket: int, redis_client: redis.Redis, ttl_seconds: int, cost: int):
        self.rate = rate
        self.bucket = bucket
        self.redis_client = redis_client
        self.ttl_seconds = ttl_seconds or int(bucket / rate)
        self.cost = cost

    async def allow_request(self, key: str = None):
        now = int(time.time())

        data = await self.redis_client.hgetall(key)

        if not data:
            await self.redis_client.hset(
                key,
                mapping={
                    "tokens": self.bucket - self.cost,
                    "timestamp": now,
                }
            )
            await self.redis_client.expire(key, self.ttl_seconds)
            return True

        tokens = int(data["tokens"])
        last_timestamp = int(data["timestamp"])

        elapsed_timestamp = now - last_timestamp

        tokens = min(self.bucket, tokens + elapsed_timestamp * self.rate)

        if tokens < self.cost:
            return False

        tokens -= self.cost

        await self.redis_client.hset(
            key,
            mapping={
                "tokens": self.bucket - self.cost,
                "timestamp": now,
            }
        )
        await self.redis_client.expire(key, self.ttl_seconds)
        return True

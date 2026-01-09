from __future__ import annotations

import logging

from app.db.redis_session import redis_db
from .token_bucket_impl import TokenBucketImpl

logger = logging.getLogger(__name__)

_token_bucket: TokenBucketImpl | None = None


def get_token_bucket() -> TokenBucketImpl:
    global _token_bucket

    if _token_bucket is None:
        if redis_db.async_client is None:
            raise RuntimeError("Redis client not initialized")

        _token_bucket = TokenBucketImpl(
            redis_client=redis_db.async_client,
            refill_rate=1,  # 1 token per second
            bucket_capacity=5,  # Max 5 tokens
            ttl_seconds=10,  # Key expires after 10 seconds of inactivity
            cost=1  # Each request costs 1 token
        )

        logger.info("Token bucket rate limiter initialized")

    return _token_bucket

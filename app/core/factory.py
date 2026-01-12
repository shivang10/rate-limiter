from __future__ import annotations

import logging

from app.database.redis import redis_connection
from .token_bucket import TokenBucketRateLimiter

logger = logging.getLogger(__name__)

_token_bucket_limiter: TokenBucketRateLimiter | None = None


def get_rate_limiter() -> TokenBucketRateLimiter:
    global _token_bucket_limiter

    if _token_bucket_limiter is None:
        if redis_connection.async_client is None:
            raise RuntimeError("Redis client not initialized")

        _token_bucket_limiter = TokenBucketRateLimiter(
            redis_client=redis_connection.async_client,
            tokens_per_second=1,
            max_tokens=5,
            expiry_seconds=10,
            tokens_per_request=1
        )

        logger.info("Token bucket rate limiter initialized")

    return _token_bucket_limiter

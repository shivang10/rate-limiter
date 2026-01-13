from __future__ import annotations

import logging

from app.database.redis import redis_connection
from .token_bucket import TokenBucketRateLimiter
from .sliding_window_counter import SlidingWindowCounterRateLimiter

logger = logging.getLogger(__name__)

_token_bucket_limiter: TokenBucketRateLimiter | None = None
__sliding_window_counter_limiter: SlidingWindowCounterRateLimiter | None = None


def get_token_bucket_rate_limiter() -> TokenBucketRateLimiter:
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


def get_sliding_window_counter_rate_limiter() -> SlidingWindowCounterRateLimiter:
    global __sliding_window_counter_limiter

    if __sliding_window_counter_limiter is None:
        if redis_connection.async_client is None:
            raise RuntimeError("Redis client not initialized")

        __sliding_window_counter_limiter = SlidingWindowCounterRateLimiter(
            redis_client=redis_connection.async_client,
            window_size_seconds=60,
            max_requests=10,
            expiry_seconds=60
        )

        logger.info("Sliding window counter rate limiter initialized")

    return __sliding_window_counter_limiter

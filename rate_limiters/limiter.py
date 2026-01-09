from __future__ import annotations

from db.redis_session import redis_db
from .token_bucket_impl import TokenBucketImpl

_token_bucket: TokenBucketImpl | None = None


def get_token_bucket() -> TokenBucketImpl:
    global _token_bucket

    if _token_bucket is None:
        if redis_db.async_client is None:
            raise RuntimeError("Redis is not initialized")

        _token_bucket = TokenBucketImpl(
            redis_client=redis_db.async_client,
            rate=1,
            bucket=5,
            ttl_seconds=10,
            cost=1
        )

    return _token_bucket

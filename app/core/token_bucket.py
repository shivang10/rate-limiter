import logging
import time

import redis

from app.core.base import RateLimiterStrategy
from app.core.metrics import (
    MetricsContext, rate_limit_requests_total, rate_limit_allowed,
    rate_limit_rejected, redis_operations_total, redis_script_errors,
    token_bucket_tokens_remaining
)
from app.database.redis import redis_connection, TOKEN_BUCKET_SCRIPT

logger = logging.getLogger(__name__)


class TokenBucketRateLimiter(RateLimiterStrategy):
    def __init__(self, tokens_per_second: int, max_tokens: int, redis_client: redis.Redis, expiry_seconds: int,
                 tokens_per_request: int):
        self.tokens_per_second = tokens_per_second
        self.max_tokens = max_tokens
        self.redis_client = redis_client
        self.expiry_seconds = expiry_seconds or int(
            max_tokens / tokens_per_second)
        self.tokens_per_request = tokens_per_request

    async def is_request_allowed(self, key: str) -> bool:
        if not key:
            logger.warning("Rate limit check called with empty key")
            return False

        now = int(time.time())
        algorithm = "token_bucket"

        with MetricsContext(algorithm=algorithm):
            try:
                # node_info = await self._get_node_for_key(key)
                node_info = await redis_connection.async_client.cluster_keyslot(key)
                logger.info(
                    f"Key '{key}' will be handled by node: {node_info}")

                result = await redis_connection.async_client.evalsha(
                    redis_connection.script_shas['token_bucket'],
                    1,
                    key,
                    self.max_tokens,
                    self.tokens_per_second,
                    now,
                    self.tokens_per_request,
                    self.expiry_seconds,
                )
                redis_operations_total.labels(
                    operation="evalsha", status="success").inc()
            except redis.exceptions.NoScriptError:
                logger.warning(
                    "Token bucket script not found in Redis, reloading...")
                redis_script_errors.labels(
                    script_name="token_bucket", error_type="NoScriptError").inc()

                token_bucket_sha = await redis_connection.async_client.script_load(TOKEN_BUCKET_SCRIPT)
                redis_connection.script_shas['token_bucket'] = token_bucket_sha

                result = await redis_connection.async_client.evalsha(
                    redis_connection.script_shas['token_bucket'],
                    1,
                    key,
                    self.max_tokens,
                    self.tokens_per_second,
                    now,
                    self.tokens_per_request,
                    self.expiry_seconds,
                )
                redis_operations_total.labels(
                    operation="evalsha", status="success").inc()
            except redis.exceptions.RedisError as e:
                logger.error(f"Redis error during rate limit check: {e}")
                redis_operations_total.labels(
                    operation="evalsha", status="error").inc()
                return True
            except Exception as e:
                logger.error(f"Unexpected error during rate limit check: {e}")
                redis_operations_total.labels(
                    operation="evalsha", status="error").inc()
                return True

            allowed, remaining_tokens = result

            token_bucket_tokens_remaining.labels(
                user_id=key).set(remaining_tokens)

            if allowed == 1:
                rate_limit_allowed.labels(
                    algorithm=algorithm, endpoint="token_bucket").inc()
                rate_limit_requests_total.labels(
                    algorithm=algorithm, result="allowed", endpoint="token_bucket").inc()
                logger.debug(
                    f"Request allowed for key: {key}, remaining tokens: {remaining_tokens}")
            else:
                rate_limit_rejected.labels(
                    algorithm=algorithm, endpoint="token_bucket").inc()
                rate_limit_requests_total.labels(
                    algorithm=algorithm, result="rejected", endpoint="token_bucket").inc()
                logger.debug(
                    f"Rate limit exceeded for key: {key}, remaining tokens: {remaining_tokens}")

            return allowed == 1

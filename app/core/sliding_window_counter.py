import logging
import time

import redis

from app.database.redis import redis_connection
from app.core.base import RateLimiterStrategy
from app.core.metrics import (
    MetricsContext, rate_limit_requests_total, rate_limit_allowed,
    rate_limit_rejected, redis_operations_total, redis_script_errors,
    sliding_window_request_count
)

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
        algorithm = "sliding_window_counter"

        try:
            node_info = await redis_connection.async_client.cluster_keyslot(key)
            logger.debug(f"Key '{key}' will be handled by node: {node_info}")
        except Exception as e:
            logger.warning(f"Could not determine node for key '{key}': {e}")

        now = time.time()

        with MetricsContext(algorithm=algorithm):
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
                redis_operations_total.labels(
                    operation="evalsha", status="success").inc()

            except redis.exceptions.NoScriptError:
                logger.error(f"Lua script not loaded. Reloading...")
                redis_script_errors.labels(
                    script_name="sliding_window_counter", error_type="NoScriptError").inc()

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
                redis_operations_total.labels(
                    operation="evalsha", status="success").inc()
            except redis.exceptions.RedisError as e:
                logger.error(f"Redis error during rate limit check: {e}")
                redis_operations_total.labels(
                    operation="evalsha", status="error").inc()
                return True
            except Exception as e:
                logger.error(
                    f"Error in SlidingWindowCounterRateLimiter for key '{key}': {e}")
                redis_operations_total.labels(
                    operation="evalsha", status="error").inc()
                return True

            allowed, request_count = result

            sliding_window_request_count.labels(user_id=key).set(request_count)

            if allowed == 1:
                rate_limit_allowed.labels(
                    algorithm=algorithm, endpoint="sliding_window_counter").inc()
                rate_limit_requests_total.labels(
                    algorithm=algorithm, result="allowed", endpoint="sliding_window_counter").inc()
                logger.debug(
                    f"Request allowed for key: {key}, count: {request_count}/{self.max_requests}")
            else:
                rate_limit_rejected.labels(
                    algorithm=algorithm, endpoint="sliding_window_counter").inc()
                rate_limit_requests_total.labels(
                    algorithm=algorithm, result="rejected", endpoint="sliding_window_counter").inc()
                logger.info(
                    f"Rate limit exceeded for key: {key}, count: {request_count}/{self.max_requests}")

            return allowed == 1

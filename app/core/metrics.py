import time

from prometheus_client import Counter, Histogram, Gauge

# Rate limiter metrics
rate_limit_requests_total = Counter(
    'rate_limiter_requests_total',
    'Total number of rate limit checks',
    ['algorithm', 'result', 'endpoint']
)

rate_limit_allowed = Counter(
    'rate_limiter_allowed_total',
    'Total number of allowed requests',
    ['algorithm', 'endpoint']
)

rate_limit_rejected = Counter(
    'rate_limiter_rejected_total',
    'Total number of rejected requests',
    ['algorithm', 'endpoint']
)

rate_limit_errors = Counter(
    'rate_limiter_errors_total',
    'Total number of rate limiter errors',
    ['algorithm', 'error_type']
)

rate_limit_check_duration = Histogram(
    'rate_limiter_check_duration_seconds',
    'Time spent checking rate limits',
    ['algorithm'],
    buckets=(0.001, 0.0025, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0)
)

# Redis metrics
redis_operations_total = Counter(
    'redis_operations_total',
    'Total number of Redis operations',
    ['operation', 'status']
)

redis_connection_errors = Counter(
    'redis_connection_errors_total',
    'Total number of Redis connection errors',
    ['error_type']
)

redis_script_errors = Counter(
    'redis_script_errors_total',
    'Total number of Redis Lua script errors',
    ['script_name', 'error_type']
)

# Active connections gauge
active_redis_connections = Gauge(
    'redis_active_connections',
    'Number of active Redis connections'
)

# Token bucket specific metrics
token_bucket_tokens_remaining = Gauge(
    'token_bucket_tokens_remaining',
    'Number of tokens remaining in bucket',
    ['user_id']
)

# Sliding window specific metrics
sliding_window_request_count = Gauge(
    'sliding_window_request_count',
    'Current request count in sliding window',
    ['user_id']
)


class MetricsContext:
    """Context manager for tracking metrics"""

    def __init__(self, algorithm: str, operation: str = "check"):
        self.algorithm = algorithm
        self.operation = operation
        self.start_time = None

    def __enter__(self):
        self.start_time = time.time()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        duration = time.time() - self.start_time
        rate_limit_check_duration.labels(
            algorithm=self.algorithm).observe(duration)

        if exc_type is not None:
            error_type = exc_type.__name__
            rate_limit_errors.labels(
                algorithm=self.algorithm,
                error_type=error_type
            ).inc()

        return False

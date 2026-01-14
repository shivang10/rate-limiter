# Rate Limiter Observability

## Metrics Implementation

This project now includes comprehensive observability with Prometheus metrics, Grafana dashboards, and Loki logging.

### Custom Metrics

#### Rate Limiter Metrics
- **`rate_limiter_requests_total`**: Counter for total rate limit checks (labels: algorithm, result, endpoint)
- **`rate_limiter_allowed_total`**: Counter for allowed requests (labels: algorithm, endpoint)
- **`rate_limiter_rejected_total`**: Counter for rejected requests (labels: algorithm, endpoint)
- **`rate_limiter_errors_total`**: Counter for rate limiter errors (labels: algorithm, error_type)
- **`rate_limiter_check_duration_seconds`**: Histogram of rate limit check latencies (labels: algorithm)

#### Redis Metrics
- **`redis_operations_total`**: Counter for Redis operations (labels: operation, status)
- **`redis_connection_errors_total`**: Counter for Redis connection errors (labels: error_type)
- **`redis_script_errors_total`**: Counter for Lua script errors (labels: script_name, error_type)
- **`redis_active_connections`**: Gauge for active Redis connections

#### Algorithm-Specific Metrics
- **`token_bucket_tokens_remaining`**: Gauge for remaining tokens (labels: user_id)
- **`sliding_window_request_count`**: Gauge for current request count (labels: user_id)

### Accessing Dashboards

1. **Prometheus**: http://localhost:9090
   - Query and explore raw metrics
   - View targets and service health

2. **Grafana**: http://localhost:3000
   - Default credentials: admin/admin
   - Pre-configured "Rate Limiter Observability Dashboard"
   - Visualizes:
     - Request rates by algorithm
     - Rejection rates
     - Latency percentiles (p95, p99)
     - Error rates
     - Redis operations
     - Requests by endpoint

3. **Loki**: http://localhost:3100
   - Log aggregation and querying
   - Integrated with Grafana for log exploration

### Dashboard Features

The Grafana dashboard includes:
- **Request Rate Monitoring**: Real-time view of requests per second by algorithm
- **Rejection Rate Gauge**: Visual indicator of rate limiting effectiveness
- **Latency Tracking**: p95 and p99 latency metrics for performance monitoring
- **Error Monitoring**: Track and alert on errors in the rate limiting system
- **Redis Health**: Monitor Redis operations and script execution
- **Endpoint Breakdown**: Bar chart showing traffic distribution

### Querying Metrics

Example PromQL queries:

```promql
# Rate of allowed requests
rate(rate_limiter_allowed_total[5m])

# Rejection percentage
rate(rate_limiter_rejected_total[5m]) / rate(rate_limiter_requests_total[5m])

# 95th percentile latency
histogram_quantile(0.95, rate(rate_limiter_check_duration_seconds_bucket[5m]))

# Redis error rate
rate(redis_operations_total{status="error"}[1m])
```

### Alerting

Consider setting up alerts for:
- High rejection rates (> 50%)
- High latency (p95 > 100ms)
- Redis errors or script failures
- Rate limiter errors

### Log Integration

Logs are collected by Promtail and sent to Loki. View logs in Grafana by:
1. Navigate to Explore
2. Select Loki as datasource
3. Query logs by container: `{container_name="rate_limiter_1"}`

## Configuration

All observability services are configured in `docker-compose.yml`:
- Prometheus scrapes metrics every 5 seconds from the rate_limiter service
- Grafana auto-provisions datasources and dashboards
- Loki receives logs from Promtail via Docker socket monitoring

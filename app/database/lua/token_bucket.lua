-- Token Bucket Rate Limiter
-- KEYS[1] = rate limit key
-- ARGV[1] = bucket_capacity
-- ARGV[2] = refill_rate
-- ARGV[3] = now (epoch seconds)
-- ARGV[4] = cost
-- ARGV[5] = ttl_seconds

local key = KEYS[1]

local bucket_capacity = tonumber(ARGV[1])
local refill_rate = tonumber(ARGV[2])
local now = tonumber(ARGV[3])
local cost = tonumber(ARGV[4])
local ttl_seconds = tonumber(ARGV[5])


local data = redis.call("HMGET", key, "tokens", "timestamp")
local tokens = tonumber(data[1])
local last_timestamp = tonumber(data[2])

if tokens == nil or last_timestamp == nil then
    tokens = bucket_capacity
    last_timestamp = now
end

local elapsed = math.max(0, now - last_timestamp)
local refill = elapsed * refill_rate
tokens = math.min(bucket_capacity, tokens + refill)

if tokens < cost then
    redis.call("HSET", key,
    "tokens", tokens,
    "timestamp", now)
    redis.call("EXPIRE", key, ttl_seconds)
    return {0, tokens}
end

tokens = tokens - cost

redis.call("HSET", key, "tokens", tokens, "timestamp", now)

redis.call("EXPIRE", key, ttl_seconds)

return {1, tokens}
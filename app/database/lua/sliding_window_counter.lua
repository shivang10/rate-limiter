-- Sliding Window Counter Rate Limiter
-- KEYS[1] = rate limit key
-- ARGV[1] = window_size (seconds)
-- ARGV[2] = max_requests
-- ARGV[3] = now (epoch seconds)
-- ARGV[4] = ttl_seconds

local key = KEYS[1]

local window_size = tonumber(ARGV[1])
local max_requests = tonumber(ARGV[2])
local now = tonumber(ARGV[3])
local ttl_seconds = tonumber(ARGV[4])

local current_window = math.floor(now / window_size)
local data = redis.call("HMGET", key, "current_count", "previous_count", "window")

local current_count = tonumber(data[1]) or 0
local previous_count = tonumber(data[2]) or 0
local stored_window = tonumber(data[3])

-- If moving to a new window
if stored_window == nil or current_window ~= stored_window then
    -- Current window becomes previous, start fresh current
    if stored_window ~= nil and current_window == stored_window + 1 then
        -- Moving to next consecutive window
        previous_count = current_count
    elseif stored_window ~= nil and current_window > stored_window + 1 then
        -- Skipped windows, reset previous count
        previous_count = 0
    end
    current_count = 0
end

-- Calculate weighted count based on sliding window
local window_elapsed = (now % window_size) / window_size
local effective_count = current_count + (previous_count * (1 - window_elapsed))

if effective_count < max_requests then
    current_count = current_count + 1
    redis.call("HSET", key, "current_count", current_count, "previous_count", previous_count, "window", current_window)
    redis.call("EXPIRE", key, ttl_seconds)
    return {1, math.floor(effective_count + 1)}
else
    redis.call("HSET", key, "current_count", current_count, "previous_count", previous_count, "window", current_window)
    redis.call("EXPIRE", key, ttl_seconds)
    return {0, math.floor(effective_count)}
end

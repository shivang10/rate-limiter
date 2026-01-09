from fastapi import Request, HTTPException

from rate_limiters.key_builder import get_user_key
from rate_limiters.limiter import get_token_bucket


async def token_bucket_rate_limit_dependency(request: Request):
    user_id = request.headers.get("user_id")

    key = get_user_key(user_id)
    token_bucket_limiter = get_token_bucket()

    if not await token_bucket_limiter.allow_request(key):
        raise HTTPException(status_code=429, detail="Too many requests, rate limit reached")

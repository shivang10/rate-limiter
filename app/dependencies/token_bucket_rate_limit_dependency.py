import logging

from fastapi import Request, HTTPException, status

from app.rate_limiters.key_builder import get_user_key
from app.rate_limiters.limiter import get_token_bucket

logger = logging.getLogger(__name__)


async def token_bucket_rate_limit_dependency(request: Request):
    user_id = request.headers.get("user_id")

    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="user_id header is required"
        )

    key = get_user_key(user_id)
    token_bucket_limiter = get_token_bucket()

    if not await token_bucket_limiter.allow_request(key):
        logger.info(f"Rate limit exceeded for user: {user_id}")
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded. Please try again later."
        )

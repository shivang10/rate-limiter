import logging

from fastapi import Request, HTTPException, status

from app.core.key_builder import build_user_rate_limit_key
from app.core.factory import get_rate_limiter

logger = logging.getLogger(__name__)


async def enforce_rate_limit(request: Request):
    user_id = request.headers.get("user_id")

    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="user_id header is required"
        )

    if not user_id:
        logger.warning("Rate limit check attempted without user_id header")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="user_id header is required"
        )

    key = build_user_rate_limit_key(user_id)
    rate_limiter = get_rate_limiter()

    if not await rate_limiter.is_request_allowed(key):
        logger.info(f"Rate limit exceeded for user: {user_id}")
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded. Please try again later."
        )

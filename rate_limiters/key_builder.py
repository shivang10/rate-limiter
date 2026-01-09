def get_user_key(user_id: str) -> str:
    return f"rate_limit:user_id:{user_id}"

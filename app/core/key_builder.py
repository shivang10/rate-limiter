def build_user_rate_limit_key(user_id: str) -> str:
    sanitized_user_id = user_id.replace("{", "").replace("}", "")
    return f"rate_limit:{{user:{sanitized_user_id}}}"

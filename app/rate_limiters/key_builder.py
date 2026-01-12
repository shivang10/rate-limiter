def get_user_key(user_id: str) -> str:
    safe_user_id = user_id.replace("{", "").replace("}", "")
    return f"rate_limit:{{user:{safe_user_id}}}"

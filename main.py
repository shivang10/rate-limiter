from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.params import Depends

from db.lua import load_lua_script

from db.redis_session import connect_async_redis, close_redis, redis_db
from dependencies.token_bucket_rate_limit_dependency import token_bucket_rate_limit_dependency


@asynccontextmanager
async def lifespan(app_: FastAPI):
    await connect_async_redis()
    lua_script = load_lua_script("token_bucket.lua")
    redis_db.token_bucket_lua_sha = await redis_db.async_client.script_load(
        lua_script
    )
    yield
    await close_redis()


app = FastAPI(lifespan=lifespan)


@app.get("/token-bucket")
def token_bucket(dep=Depends(token_bucket_rate_limit_dependency)):
    return "message: TokenBucketOk"

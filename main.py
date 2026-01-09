from contextlib import asynccontextmanager

from fastapi import FastAPI

from redis_session import connect_async_redis, close_redis


@asynccontextmanager
async def lifespan(app_: FastAPI):
    await connect_async_redis()
    yield
    await close_redis()


app = FastAPI(lifespan=lifespan)


@app.get("/")
def main():
    return "Rate Limiter"

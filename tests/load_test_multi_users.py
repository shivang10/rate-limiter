import asyncio
import aiohttp
import time
import os
from dotenv import load_dotenv
from collections import Counter

load_dotenv()

URL = os.getenv("API_URL", "http://0.0.0.0:80/token-bucket")
USERS = 25000
REQUESTS_PER_USER = 1
CONCURRENCY = 500


async def hit(session, user_id):
    headers = {"user_id": user_id}
    async with session.get(URL, headers=headers) as resp:
        return resp.status


async def main():
    connector = aiohttp.TCPConnector(limit=CONCURRENCY)
    async with aiohttp.ClientSession(connector=connector) as session:
        tasks = []
        start = time.time()
        for u in range(USERS):
            for _ in range(REQUESTS_PER_USER):
                tasks.append(hit(session, f"user-{u}"))

        results = await asyncio.gather(*tasks)
        elapsed = time.time() - start

    print(Counter(results))
    print("Elapsed:", round(elapsed, 2), "seconds")

if __name__ == "__main__":
    asyncio.run(main())

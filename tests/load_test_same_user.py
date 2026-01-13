import asyncio
import aiohttp
import time
import os
from dotenv import load_dotenv
from collections import Counter

load_dotenv()

URL = os.getenv("API_URL", "http://0.0.0.0:80/token-bucket")
TOTAL_REQUESTS = 2000
CONCURRENCY = 200
USER_ID = "user-123"

headers = {
    "user_id": USER_ID
}


async def hit(session, i):
    async with session.get(URL, headers=headers) as resp:
        return resp.status


async def main():
    connector = aiohttp.TCPConnector(limit=CONCURRENCY)
    async with aiohttp.ClientSession(connector=connector) as session:
        start = time.time()

        tasks = [hit(session, i) for i in range(TOTAL_REQUESTS)]
        results = await asyncio.gather(*tasks)

        elapsed = time.time() - start

    counts = Counter(results)
    print("Results:", counts)
    print("Elapsed:", round(elapsed, 2), "seconds")

if __name__ == "__main__":
    asyncio.run(main())

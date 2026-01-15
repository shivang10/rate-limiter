import asyncio
import os
import sys
import time
from collections import Counter

import aiohttp
from dotenv import load_dotenv

load_dotenv()

# Get algorithm from command line argument or environment variable
ALGORITHM = sys.argv[1] if len(sys.argv) > 1 else os.getenv(
    "RATE_LIMIT_ALGORITHM", "token-bucket")

# Map algorithm names to endpoints
ENDPOINTS = {
    "token-bucket": "/token-bucket",
    "sliding-window": "/sliding-window-counter",
    "sliding-window-counter": "/sliding-window-counter"
}

BASE_URL = os.getenv("BASE_URL", "http://0.0.0.0:80")
ENDPOINT = ENDPOINTS.get(ALGORITHM, "/token-bucket")
URL = f"{BASE_URL}{ENDPOINT}"

TOTAL_REQUESTS = 20000
CONCURRENCY = 200
USER_ID = "user-123"

headers = {
    "user_id": USER_ID
}


async def hit(session, i):
    async with session.get(URL, headers=headers) as resp:
        return resp.status


async def main():
    print(f"Testing endpoint: {URL}")
    print(f"Algorithm: {ALGORITHM}")
    print(f"Total requests: {TOTAL_REQUESTS}, Concurrency: {CONCURRENCY}")
    print("-" * 50)

    connector = aiohttp.TCPConnector(limit=CONCURRENCY)
    async with aiohttp.ClientSession(connector=connector) as session:
        start = time.time()

        tasks = [hit(session, i) for i in range(TOTAL_REQUESTS)]
        results = await asyncio.gather(*tasks)

        elapsed = time.time() - start

    counts = Counter(results)
    print("\nResults:", counts)
    print("Elapsed:", round(elapsed, 2), "seconds")
    print(f"Throughput: {round(TOTAL_REQUESTS / elapsed, 2)} req/s")


if __name__ == "__main__":
    asyncio.run(main())

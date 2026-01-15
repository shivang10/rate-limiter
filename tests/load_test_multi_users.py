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

USERS = 25000
REQUESTS_PER_USER = 5
CONCURRENCY = 200


async def hit(session, user_id):
    headers = {"user_id": user_id}
    async with session.get(URL, headers=headers) as resp:
        return resp.status


async def main():
    print(f"Testing endpoint: {URL}")
    print(f"Algorithm: {ALGORITHM}")
    print(
        f"Users: {USERS}, Requests per user: {REQUESTS_PER_USER}, Concurrency: {CONCURRENCY}")
    print("-" * 50)

    connector = aiohttp.TCPConnector(limit=CONCURRENCY)
    async with aiohttp.ClientSession(connector=connector) as session:
        tasks = []
        start = time.time()
        for u in range(USERS):
            for _ in range(REQUESTS_PER_USER):
                tasks.append(hit(session, f"user-{u}"))

        results = await asyncio.gather(*tasks)
        elapsed = time.time() - start

    counts = Counter(results)
    total_requests = USERS * REQUESTS_PER_USER

    print("\nResults:", counts)
    print("Elapsed:", round(elapsed, 2), "seconds")
    print(f"Throughput: {round(total_requests / elapsed, 2)} req/s")


if __name__ == "__main__":
    asyncio.run(main())

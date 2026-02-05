import asyncio
import statistics
import time

import httpx
import structlog

# Configure logger
logger = structlog.get_logger(__name__)

# Configuration
BASE_URL = "http://localhost:8000"
API_KEY = "dev-api-key-change-in-production"  # From settings  # pragma: allowlist secret
CONCURRENT_USERS = 5
REQUESTS_PER_USER = 5
TOTAL_REQUESTS = CONCURRENT_USERS * REQUESTS_PER_USER

headers = {"X-API-Key": API_KEY, "Content-Type": "application/json"}


async def send_request(client: httpx.AsyncClient, user_id: str, thread_id: str):
    """Send a single graph invoke request and measure latency."""
    payload = {
        "message": f"Stress test message from {user_id}",
        "thread_id": thread_id,
        "user_id": user_id,
        "language": "az",
    }

    start_time = time.perf_counter()
    try:
        response = await client.post(
            f"{BASE_URL}/api/v1/graph/invoke", json=payload, headers=headers, timeout=60.0
        )
        end_time = time.perf_counter()

        latency = end_time - start_time

        if response.status_code == 200:
            return {"success": True, "latency": latency}
        else:
            logger.error("request_failed", status=response.status_code, text=response.text[:100])
            return {"success": False, "latency": latency, "error": response.status_code}
    except Exception as e:
        end_time = time.perf_counter()
        logger.error("request_exception", error=str(e))
        return {"success": False, "latency": end_time - start_time, "error": str(e)}


async def user_session(user_id: str):
    """Simulate a single user with multiple sequential requests."""
    latencies = []
    success_count = 0

    async with httpx.AsyncClient(timeout=60.0) as client:
        # 1. Create a thread via the API
        try:
            thread_resp = await client.post(
                f"{BASE_URL}/api/v1/threads",
                json={"metadata": {"user_id": user_id}},
                headers=headers,
            )
            if thread_resp.status_code != 200:
                logger.error(
                    "thread_creation_failed", status=thread_resp.status_code, text=thread_resp.text
                )
                return {"user_id": user_id, "success_rate": 0, "latencies": []}
            thread_id = thread_resp.json()["thread_id"]
        except Exception as e:
            logger.error("thread_creation_exception", error=str(e), type=type(e).__name__)
            return {"user_id": user_id, "success_rate": 0, "latencies": []}

        # 2. Run sequential requests
        for i in range(REQUESTS_PER_USER):
            logger.info(
                "user_sending_request", user_id=user_id, request_num=i + 1, thread_id=thread_id
            )
            result = await send_request(client, user_id, thread_id)
            if result["success"]:
                success_count += 1
                latencies.append(result["latency"])

            # Small delay between requests
            await asyncio.sleep(0.5)

    return {
        "user_id": user_id,
        "success_rate": success_count / REQUESTS_PER_USER,
        "latencies": latencies,
    }


async def run_stress_test():
    """Run concurrent user sessions and aggregate results."""
    print("🚀 Starting PostgreSQL Stress Test & Performance Benchmark")
    print(f"   - Concurrent Users: {CONCURRENT_USERS}")
    print(f"   - Requests per User: {REQUESTS_PER_USER}")
    print(f"   - Total Requests: {TOTAL_REQUESTS}")
    print("-" * 50)

    start_time = time.perf_counter()

    tasks = [user_session(f"stress_user_{i}") for i in range(CONCURRENT_USERS)]
    results = await asyncio.gather(*tasks)

    end_time = time.perf_counter()
    duration = end_time - start_time

    # Aggregate stats
    all_latencies = []
    total_success = 0
    for res in results:
        all_latencies.extend(res["latencies"])
        total_success += res["success_rate"] * REQUESTS_PER_USER

    success_percentage = (total_success / TOTAL_REQUESTS) * 100

    print("\n📊 Stress Test Results")
    print("-" * 50)
    print(f"Total Duration:    {duration:.2f}s")
    print(f"Requests/Second:   {TOTAL_REQUESTS / duration:.2f} req/s")
    print(f"Success Rate:      {success_percentage:.1f}% ({int(total_success)}/{TOTAL_REQUESTS})")

    if all_latencies:
        print(f"Min Latency:       {min(all_latencies):.2f}s")
        print(f"Max Latency:       {max(all_latencies):.2f}s")
        print(f"Avg Latency:       {statistics.mean(all_latencies):.2f}s")
        if len(all_latencies) > 1:
            print(f"P95 Latency:       {statistics.quantiles(all_latencies, n=20)[18]:.2f}s")
    print("-" * 50)


if __name__ == "__main__":
    asyncio.run(run_stress_test())

#!/usr/bin/env python3
"""
Test Meaningful Conversation with ALİM Agent
"""

import asyncio

import httpx

LANGGRAPH_URL = "http://127.0.0.1:2024"


async def test():
    print("\n=== ALİM Agent - Meaningful Conversation Test ===\n")

    # Create thread
    async with httpx.AsyncClient(timeout=30.0) as client:
        print("[1] Creating thread...")
        response = await client.post(f"{LANGGRAPH_URL}/threads", json={})
        if response.status_code in [200, 201]:
            thread_data = response.json()
            thread_id = thread_data.get("thread_id") or thread_data.get("id")
            print(f"    Thread created: {thread_id}")
        else:
            print(f"    Error: {response.text}")
            return

        # Test conversation
        print("\n[2] Sending agricultural query in Azerbaijani...")
        query = "Bu il qabaqları nə zaman əkmələyim? Masallı rayonunda ideal vaxt nədir?"
        print(f"    Query: {query}")

        print("\n[3] Invoking agent...")
        response = await client.post(
            f"{LANGGRAPH_URL}/threads/{thread_id}/runs",
            json={
                "assistant_id": "alim_agent",
                "input": {"messages": [{"role": "user", "content": query}]},
            },
        )

        if response.status_code == 200:
            result = response.json()
            print("    Status: SUCCESS")
            print(f"    Response status: {response.status_code}")
            if isinstance(result, dict):
                print(f"    Response keys: {list(result.keys())[:5]}")
        else:
            print("    Status: FAILED")
            print(f"    Error: {response.text}")


if __name__ == "__main__":
    asyncio.run(test())
    print("\nTest completed.\n")

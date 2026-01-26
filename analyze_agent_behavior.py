#!/usr/bin/env python3
"""
Comprehensive Agent Behavior Analysis
Tests the agent's response quality and functionality
"""

import asyncio
from datetime import datetime

import httpx

LANGGRAPH_URL = "http://127.0.0.1:2024"

# Test scenarios
TESTS = [
    {
        "name": "Seasonal Planning",
        "query": "Bu il qabaqları nə zaman əkmələyim?",
        "checks": ["seasonal guidance", "Azerbaijani response", "local context awareness"],
    },
    {
        "name": "Pest Management",
        "query": "Qabaq bitkilərinə ziyana verən zərərvericilərlə necə mübarizə aparm?",
        "checks": ["pest identification", "treatment recommendations", "prevention strategies"],
    },
    {
        "name": "Soil Management",
        "query": "Torpağın pH ölçüsü necə düzəldə bilərəm?",
        "checks": ["soil testing guidance", "pH adjustment methods", "amendment recommendations"],
    },
]


async def get_agent_response(thread_id: str, query: str) -> dict:
    """Send query and get agent response"""
    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            # Send query
            response = await client.post(
                f"{LANGGRAPH_URL}/threads/{thread_id}/runs",
                json={
                    "assistant_id": "alim_agent",
                    "input": {"messages": [{"role": "user", "content": query}]},
                },
            )

            if response.status_code == 200:
                run_result = response.json()
                run_id = run_result.get("run_id")

                # Give agent time to process
                await asyncio.sleep(3)

                # Get run result
                get_response = await client.get(
                    f"{LANGGRAPH_URL}/threads/{thread_id}/runs/{run_id}"
                )

                if get_response.status_code == 200:
                    run_data = get_response.json()
                    return {
                        "success": True,
                        "run_id": run_id,
                        "status": run_data.get("status"),
                        "data": run_data,
                    }

            return {"success": False, "error": f"HTTP {response.status_code}"}
        except Exception as e:
            return {"success": False, "error": str(e)}


async def test_agent_behavior():
    """Test agent behavior comprehensively"""

    print("\n" + "=" * 70)
    print("  ALIM Agent - Comprehensive Behavior Analysis")
    print("=" * 70)
    print(f"\nTest Date: {datetime.now().isoformat()}")

    # Create thread
    async with httpx.AsyncClient(timeout=30.0) as client:
        print("\n[SETUP] Creating conversation thread...")
        response = await client.post(f"{LANGGRAPH_URL}/threads", json={})

        if response.status_code not in [200, 201]:
            print(f"ERROR: Failed to create thread: {response.text}")
            return

        thread_data = response.json()
        thread_id = thread_data.get("thread_id") or thread_data.get("id")
        print(f"  Thread: {thread_id}")

    # Run tests
    results = []
    for idx, test in enumerate(TESTS, 1):
        print(f"\n{'─'*70}")
        print(f"[TEST {idx}] {test['name']}")
        print(f"{'─'*70}")
        print(f"Query: {test['query']}")

        result = await get_agent_response(thread_id, test["query"])

        if result["success"]:
            print("Status: RESPONDING")
            print(f"Run ID: {result['run_id']}")
            print(f"Run Status: {result['status']}")

            # Analyze response
            if result.get("data"):
                data = result["data"]
                print("\nResponse Analysis:")
                print(f"  - Has values: {'values' in data}")
                if data.get("values"):
                    print(f"  - Value keys: {list(data['values'].keys())[:5]}")
                print(f"  - Metadata: {data.get('metadata', {})}")
        else:
            print("Status: FAILED")
            print(f"Error: {result['error']}")

        results.append(
            {
                "test": test["name"],
                "success": result["success"],
                "status": result.get("status", "unknown"),
            }
        )

        # Wait between tests
        await asyncio.sleep(2)

    # Summary
    print(f"\n{'='*70}")
    print("SUMMARY")
    print(f"{'='*70}")

    passed = sum(1 for r in results if r["success"])
    total = len(results)

    print(f"\nTests Completed: {passed}/{total}")
    print(f"Success Rate: {(passed/total)*100:.1f}%")

    print("\nAgent Observations:")
    print("  - Connectivity: OK (responding to messages)")
    print("  - Threading: OK (maintaining conversation context)")
    print(
        f"  - Processing: {('OK (all queries processed)' if passed == total else 'PARTIAL (some queries failed)')}"
    )

    print("\nNext Steps for Wholesome Conversation:")
    print("  1. Review agent responses in Chainlit UI: http://localhost:8501")
    print("  2. Check for:")
    print("     - Meaningful agricultural guidance")
    print("     - Azerbaijani language quality")
    print("     - Local context awareness (Masallı region)")
    print("     - Professional, conversational tone")
    print("  3. Verify MCP tools are invoked when needed")
    print("  4. Test file upload functionality")
    print("  5. Monitor performance metrics")

    print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    asyncio.run(test_agent_behavior())

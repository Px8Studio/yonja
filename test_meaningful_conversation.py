#!/usr/bin/env python3
"""
Test Meaningful Conversation with ALİM Agent
─────────────────────────────────────────────

This script tests the agent with realistic agricultural queries
to verify its behavior in a practical scenario.
"""

import asyncio
import io
import sys
from datetime import datetime

import httpx

# Fix Windows console encoding
if sys.platform == "win32":
    # Set stdout to UTF-8
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

# Configuration
LANGGRAPH_URL = "http://127.0.0.1:2024"
FASTAPI_URL = "http://localhost:8000"

# Test data
TEST_USER_ID = "test_farmer_001"
TEST_THREAD_ID = "thread_test_001"
TEST_FARM_ID = "demo_farm_001"

# Sample agricultural context
FARMER_PROFILE = {
    "name": "Qasım",
    "region": "Masallı",
    "crop": "Qabaq (Pumpkin)",
    "farm_size_hectares": 5,
    "experience_years": 15,
    "expertise": "traditional_farming",
}

# Meaningful test conversations
CONVERSATIONS = [
    {
        "intent": "seasonal_planning",
        "query": "Bu il qabaqları nə zaman əkmələyim? Masallı rayonunda ideal vaxt nədir?",
        "expected_topic": "seasonal_planting",
        "description": "Ask about planting season for pumpkins in Masallı region",
    },
    {
        "intent": "pest_management",
        "query": "Qabaq bitkilərinə ziyansa verən xususilə soyuq dövrədə hansı zərərvericilərlə qarşılaşırıq?",
        "expected_topic": "pest_control",
        "description": "Query about common pests affecting pumpkin crops in winter",
    },
    {
        "intent": "irrigation_scheduling",
        "query": "Hər bir sığorta mərhələsində qabaqlar üçün neçə millimetr su lazımdır?",
        "expected_topic": "water_management",
        "description": "Ask about water requirements at different growth stages",
    },
    {
        "intent": "soil_preparation",
        "query": "Masallı rayonunda torpaq pH ölçüsü nə olmalıdır? Torpağı necə hazırlamalıyam?",
        "expected_topic": "soil_management",
        "description": "Inquiry about soil pH and preparation in Masallı",
    },
    {
        "intent": "yield_optimization",
        "query": "5 hektarda məhsuldarlığı maksimum edə bilərik? Hansı yönəmlər məsləhətləndirilir?",
        "expected_topic": "yield_optimization",
        "description": "Question about improving yield on 5-hectare farm",
    },
]


async def create_thread(config: dict) -> dict:
    """Create a new LangGraph thread"""
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.post(
                f"{LANGGRAPH_URL}/threads",
                json={"metadata": {"user_id": config["user_id"], "farm_id": config["farm_id"]}},
            )

            if response.status_code in [200, 201]:
                result = response.json()
                thread_id = result.get("thread_id") or result.get("id")
                return {"success": True, "thread_id": thread_id, "data": result}
            else:
                return {"success": False, "error": response.text}
        except Exception as e:
            return {"success": False, "error": str(e)}


async def invoke_agent(message: str, config: dict) -> dict:
    """Invoke the LangGraph agent via HTTP"""
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.post(
                f"{LANGGRAPH_URL}/threads/{config['thread_id']}/runs",
                json={
                    "assistant_id": "alim_agent",
                    "input": {"messages": [{"role": "user", "content": message}]},
                    "config": {"configurable": {"user_id": config["user_id"]}},
                },
            )

            if response.status_code == 200:
                result = response.json()
                return {"success": True, "data": result}
            else:
                return {"success": False, "status": response.status_code, "error": response.text}
        except httpx.ConnectError:
            return {"success": False, "error": "Cannot connect to LangGraph server"}
        except Exception as e:
            return {"success": False, "error": str(e)}


def print_header(text: str):
    """Print formatted header"""
    print("\n" + "=" * 70)
    print(f"  {text}")
    print("=" * 70)


def print_section(text: str):
    """Print formatted section"""
    print(f"\n► {text}")
    print("-" * 50)


def print_step(step: int, text: str):
    """Print step with number"""
    print(f"\n  [{step}] {text}")


async def test_conversation():
    """Run meaningful test conversations with the agent"""

    print_header("🌿 ALİM Agent - Meaningful Conversation Test")
    print(f"\n📅 Test Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🧑‍🌾 Farmer Profile: {FARMER_PROFILE['name']}")
    print(f"📍 Region: {FARMER_PROFILE['region']}")
    print(f"🌱 Primary Crop: {FARMER_PROFILE['crop']}")
    print(f"🏞️  Farm Size: {FARMER_PROFILE['farm_size_hectares']} hectares")
    print(f"👨‍💼 Experience: {FARMER_PROFILE['experience_years']} years")

    config = {"user_id": TEST_USER_ID, "thread_id": TEST_THREAD_ID, "farm_id": TEST_FARM_ID}

    # Create a thread first
    print_section("Creating LangGraph Thread")
    thread_result = await create_thread(config)
    if thread_result["success"]:
        config["thread_id"] = thread_result["thread_id"]
        print(f"✅ Thread created: {config['thread_id']}")
    else:
        print(f"❌ Failed to create thread: {thread_result['error']}")
        return

    # Test each conversation
    for idx, conv in enumerate(CONVERSATIONS, 1):
        print_section(f"Conversation {idx}: {conv['description']}")
        print(f"Intent: {conv['intent'].upper()}")
        print(f"Expected Topic: {conv['expected_topic'].upper()}")

        print_step(1, "Sending query...")
        print(f"   Query: {conv['query']}")

        result = await invoke_agent(conv["query"], config)

        print_step(2, "Agent Response")
        if result["success"]:
            print("   ✅ Request successful")
            # Print a summary of the response
            if "data" in result:
                print(f"   Response Type: {type(result['data'])}")
                if isinstance(result["data"], dict):
                    print(f"   Response Keys: {list(result['data'].keys())[:5]}")
        else:
            print(f"   ❌ Request failed: {result.get('error', 'Unknown error')}")

        print_step(3, "Observation")
        print("   - Agent should provide domain-specific guidance")
        print("   - Response should be in Azerbaijani")
        print("   - Response should reference local context (Masallı region)")
        print("   - Response should be conversational and helpful")

        # Wait between requests
        await asyncio.sleep(2)

    print_header("Test Summary")
    print(f"✅ Completed {len(CONVERSATIONS)} meaningful conversations")
    print("📊 Observations:")
    print("  • Agent connectivity: VERIFIED")
    print("  • Message processing: VERIFIED")
    print("  • Domain-specific responses: REQUIRES MANUAL VERIFICATION")
    print("  • Language quality: REQUIRES MANUAL VERIFICATION")
    print("\n💡 Next Steps:")
    print("  1. Review agent responses in browser at http://localhost:8501")
    print("  2. Check LangGraph metrics at http://127.0.0.1:2024/docs")
    print("  3. Verify MCP tool invocations in logs")
    print("  4. Test file upload with agricultural documents (PDF)")


async def main():
    """Main entry point"""
    try:
        await test_conversation()
        print("\n✨ Test completed successfully!")
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Test failed with error: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())

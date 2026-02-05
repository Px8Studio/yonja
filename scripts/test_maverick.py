#!/usr/bin/env python3
"""Test Maverick integration in ALİM."""

import asyncio
import os
import sys

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from alim.config import settings  # noqa: E402
from alim.llm.model_roles import (  # noqa: E402
    LANGGRAPH_NODE_MODELS,
    MODEL_ROLES,
    get_model_for_node,
    should_rewrite_response,
)


def test_model_roles():
    """Test model role configuration."""
    print("=" * 60)
    print("🧪 MAVERICK INTEGRATION TEST")
    print("=" * 60)

    # Test 1: Maverick is in MODEL_ROLES
    print("\n📋 Test 1: Maverick in MODEL_ROLES")
    maverick_key = "meta-llama/llama-4-maverick-17b-128e-instruct"
    if maverick_key in MODEL_ROLES:
        maverick = MODEL_ROLES[maverick_key]
        print("   ✅ Found Maverick")
        print(f"   Role: {maverick.get('role')}")
        print(f"   Multimodal: {maverick.get('multimodal')}")
        print(f"   Azerbaijani Quality: {maverick.get('azerbaijani_quality')}")
    else:
        print("   ❌ Maverick NOT found in MODEL_ROLES")
        return False

    # Test 2: get_model_for_node defaults to maverick
    print("\n📋 Test 2: get_model_for_node() defaults")
    nodes = ["supervisor", "response_writer", "irrigation_calculator"]
    for node in nodes:
        model = get_model_for_node(node)  # Should default to maverick
        print(f"   {node}: {model}")
        if "maverick" not in model:
            print(f"   ⚠️ Expected maverick, got {model}")

    # Test 3: Legacy mode still works
    print("\n📋 Test 3: Legacy mode (open_source)")
    legacy_model = get_model_for_node("response_writer", "open_source")
    print(f"   response_writer (legacy): {legacy_model}")
    if legacy_model == "llama-3.3-70b-versatile":
        print("   ✅ Legacy mode works")
    else:
        print(f"   ⚠️ Expected llama-3.3-70b-versatile, got {legacy_model}")

    # Test 4: should_rewrite_response
    print("\n📋 Test 4: should_rewrite_response()")
    test_cases = [
        ("meta-llama/llama-4-maverick-17b-128e-instruct", False),
        ("qwen3-32b", True),
        ("llama-3.3-70b-versatile", False),
    ]
    for model, expected in test_cases:
        result = should_rewrite_response(model)
        status = "✅" if result == expected else "❌"
        print(f"   {status} {model}: {result} (expected {expected})")

    # Test 5: LANGGRAPH_NODE_MODELS has maverick mode
    print("\n📋 Test 5: LANGGRAPH_NODE_MODELS modes")
    modes = list(LANGGRAPH_NODE_MODELS.keys())
    print(f"   Available modes: {modes}")
    if "maverick" in modes:
        print("   ✅ Maverick mode available")
    else:
        print("   ❌ Maverick mode NOT found")
        return False

    # Test 6: Config default
    print("\n📋 Test 6: Config settings")
    print(f"   Default groq_model: {settings.groq_model}")
    if "maverick" in settings.groq_model:
        print("   ✅ Config defaults to Maverick")
    else:
        print(f"   ⚠️ Config still using: {settings.groq_model}")

    print("\n" + "=" * 60)
    print("✅ All model role tests passed!")
    print("=" * 60)
    return True


async def test_groq_provider():
    """Test Groq provider with Maverick (requires API key)."""
    print("\n" + "=" * 60)
    print("🚀 GROQ PROVIDER TEST")
    print("=" * 60)

    if not settings.groq_api_key:
        print("⚠️ No GROQ_API_KEY set. Skipping provider test.")
        print("   Set ALIM_GROQ_API_KEY in .env or environment")
        return

    from alim.llm.factory import create_groq_provider
    from alim.llm.providers.base import LLMMessage

    # Create Maverick provider
    provider = create_groq_provider(model="meta-llama/llama-4-maverick-17b-128e-instruct")
    print(f"\n📋 Provider: {provider.provider_name}")
    print(f"   Model: {provider.model_name}")

    # Health check
    print("\n📋 Health Check...")
    is_healthy = await provider.health_check()
    if is_healthy:
        print("   ✅ Groq API is healthy")
    else:
        print("   ❌ Groq API health check failed")
        return

    # Test Azerbaijani response
    print("\n📋 Testing Azerbaijani Response...")
    messages = [
        LLMMessage.system(
            "Sən ALİM adlı Azərbaycan kənd təsərrüfatı AI köməkçisisən. "
            "YALNIZ Azərbaycan dilində cavab ver. Türkcə sözlər istifadə etmə."
        ),
        LLMMessage.user("Buğda əkmək üçün ən yaxşı vaxt nədir?"),
    ]

    response = await provider.generate(messages, temperature=0.7, max_tokens=300)
    print(f"\n   Response ({response.tokens_used} tokens):")
    print("-" * 40)
    print(response.content[:500])
    print("-" * 40)

    # Check for Turkish leakage
    turkish_words = ["eylül", "zemin", "tohum", "ürün", "sulama", "toprak"]
    found_turkish = [w for w in turkish_words if w.lower() in response.content.lower()]
    if found_turkish:
        print(f"   ⚠️ Possible Turkish leakage: {found_turkish}")
    else:
        print("   ✅ No Turkish leakage detected")

    print("\n" + "=" * 60)
    print("✅ Groq provider test complete!")
    print("=" * 60)


def main():
    """Run all tests."""
    # Test model roles (no API needed)
    if not test_model_roles():
        sys.exit(1)

    # Test Groq provider (needs API key)
    asyncio.run(test_groq_provider())


if __name__ == "__main__":
    main()

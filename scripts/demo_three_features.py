#!/usr/bin/env python
"""
Demo: NL-to-SQL + SQL Execution + Vision Analysis + Multimodal Images

Run with:
    python scripts/demo_three_features.py
"""

import asyncio
import tempfile
from pathlib import Path

from PIL import Image, ImageDraw


async def main():
    print("=" * 70)
    print("🎯 ALEM THREE NEW FEATURES DEMO")
    print("=" * 70)
    print()

    # Feature 1: Create a synthetic test image
    print("✨ FEATURE 1: Multimodal Image Support")
    print("-" * 70)
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create a simple test image (crop with issue)
        img = Image.new("RGB", (200, 200), color="green")
        draw = ImageDraw.Draw(img)
        draw.text((50, 90), "Affected\nCrop", fill="red")
        img_path = Path(tmpdir) / "crop.jpg"
        img.save(img_path)
        print(f"✅ Created test image: {img_path}")

        # Test multimodal message creation
        from yonca.llm.multimodal import create_multimodal_message

        msg = create_multimodal_message(
            "This crop looks diseased. What should I do?", [str(img_path)]
        )
        print(f"✅ Created multimodal message: {type(msg).__name__}")
        print(f"   Content type: {type(msg.content)}")
        if isinstance(msg.content, list):
            print(f"   Content parts: {len(msg.content)} (text + image)")
        print()

    # Feature 2: NL-to-SQL Generation
    print("✨ FEATURE 2: Natural Language to SQL")
    print("-" * 70)
    from yonca.agent.nodes.nl_to_sql import nl_to_sql_node
    from yonca.agent.state import AgentState, UserIntent

    state: AgentState = {
        "current_input": "Sahəsi 50 hektardan çox olan fermləri göstər",
        "nodes_visited": [],
        "intent": UserIntent.DATA_QUERY,
        "messages": [],
    }

    result = await nl_to_sql_node(state)
    print(f"Input: {state['current_input']}")
    print(f"Generated SQL:\n  {result['current_response']}")
    print()

    # Feature 3: Vision Analysis (text-based for now)
    print("✨ FEATURE 3: Vision-to-Action Analysis")
    print("-" * 70)
    from yonca.agent.nodes.vision_to_action import vision_to_action_node

    state = {
        "current_input": "Bu şəkildə pomidor bitkilərində sarı ləkələr var. Buna nə dəmir?",
        "nodes_visited": [],
        "messages": [],
    }

    result = await vision_to_action_node(state)
    print(f"Input: {state['current_input']}")
    print(f"Analysis:\n{result['current_response']}")
    print()

    # Feature 4: SQL Execution (read-only demo)
    print("✨ FEATURE 4: SQL Execution & Results")
    print("-" * 70)
    print("Note: SQL executor requires live database connection.")
    print("In production, this would query the Yonca App DB and format results.")
    print()

    # Feature 5: API Route
    print("✨ FEATURE 5: FastAPI Vision Endpoint")
    print("-" * 70)
    print("POST /api/vision/analyze")
    print("  - Upload image files")
    print("  - Returns analysis + action plan")
    print("  - Integrated with Langfuse for tracing")
    print()

    print("=" * 70)
    print("🎉 ALL THREE FEATURES READY!")
    print("=" * 70)
    print()
    print("Next steps:")
    print("1. Start FastAPI: poetry run uvicorn src.yonca.api.main:app")
    print(
        "2. Upload image: curl -X POST -F 'files=@image.jpg' http://localhost:8000/api/vision/analyze"
    )
    print("3. Start demo UI: cd demo-ui && chainlit run app.py")
    print()


if __name__ == "__main__":
    asyncio.run(main())

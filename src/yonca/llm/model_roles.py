# Yonca AI - Model Role Configuration
# Open-Source vs Proprietary Model Strategy

"""
MODEL ARCHITECTURE IN YONCA AI (2026 UPDATE)
=============================================

2026 GOLD STANDARD: LLAMA 4 MAVERICK
------------------------------------
Meta's Llama 4 Maverick is a Mixture-of-Experts (MoE) model with 17B active
parameters and 128 experts. It replaces the previous two-model stack:

 OLD STACK (Deprecated):
   - Qwen 3-32B → Logic/Math calculations
   - Llama 3.3-70B → Azerbaijani language cleanup
   - Problem: Two-pass system, double token cost, Turkish leakage risk

 NEW STACK (2026):
   - Llama 4 Maverick → ALL tasks (logic + language + vision)
   - Benefit: Single-pass, native Azerbaijani, multimodal support

OPEN-SOURCE MODELS (via Groq or self-hosted):
- Maverick, Llama, Qwen, Mistral, Mixtral - fully open-source
- Can be self-hosted with appropriate hardware (GPU clusters, LPU)
- Groq demonstrates enterprise-grade performance these models can achieve
- With proper infrastructure: 200-300 tokens/sec, production-ready

PROPRIETARY CLOUD MODELS:
- Gemini (Google) - closed-source, cloud-only
- Cannot be self-hosted
- Vendor lock-in

Philosophy:
-----------
We prioritize open-source models to demonstrate:
1. Enterprise-readiness with proper infrastructure
2. No vendor lock-in
3. Full control over deployment
4. Transparency and auditability

Groq serves as proof-of-concept that open-source models can match or exceed
proprietary performance when given the right hardware.
"""

# ============================================================
# Model Role Definitions
# ====================== (Open-Source on Groq)
# ============================================================

MODEL_ROLES = {
    # ===== 2026 GOLD STANDARD: LLAMA 4 MAVERICK =====
    # Single model replaces the Qwen + Llama stack
    
    "meta-llama/llama-4-maverick-17b-128e-instruct": {
        "provider": "groq",
        "license": "Llama 4 Community License (open-source)",
        "role": "master",  # All-in-one: reasoning + chat + vision
        "strength": "all_rounder",
        "azerbaijani_quality": "superior",  # Native, no Turkish leakage
        "math_logic_quality": "excellent",  # 400B-equivalent reasoning
        "speed": "ultra_fast (~300 tok/s on Groq)",
        "self_hostable": True,
        "recommended_hardware": "4x A100 GPUs or Groq LPU",
        "multimodal": True,  # NEW: Can process images!
        "context_window": 128000,
        "use_for": [
            "ALL_TASKS",  # Single node replaces entire stack
            "farmer_conversation",
            "irrigation_schedule_calculation",
            "fertilization_dosage_calculation",
            "pest_risk_scoring",
            "harvest_timing_logic",
            "image_analysis",  # NEW: Crop disease from photos
            "final_response_generation",
        ],
        "avoid_for": [],  # Can handle everything
        "notes": "2026 Gold Standard. MoE architecture (17B active, 128 experts). "
                 "Replaces Qwen+Llama two-pass system. Native Azerbaijani."
    },
    
    # ===== LEGACY MODELS (Still Supported) =====
    
    "llama-3.3-70b-versatile": {
        "provider": "groq",
        "license": "Llama 3 Community License (open-source)",
        "role": "chat",  # User-facing conversation
        "strength": "language_quality",
        "azerbaijani_quality": "high",
        "math_logic_quality": "medium-high",
        "speed": "fast (200+ tok/s on Groq infrastructure)",
        "self_hostable": True,
        "recommended_hardware": "8x A100 GPUs or Groq LPU",
        "use_for": [
            "final_response_generation",
            "farmer_conversation",
            "greeting_farewell",
            "explanation_rewriting"
        ],
        "avoid_for": [
            "complex_calculations",
            "precise_numeric_schedules"
        ],
        "notes": "Best for final user-facing responses. Less Turkish leakage. Open-source."
    },
    
    "qwen3-32b": {
        "provider": "groq",
        "license": "Apache 2.0 (fully open-source)",
        "role": "reasoning",  # Internal logic, hidden from user
        "strength": "math_logic",
        "azerbaijani_quality": "medium",  # Some Turkish leakage
        "math_logic_quality": "very_high",
        "speed": "very_fast (250-300 tok/s on Groq)",
        "self_hostable": True,
        "recommended_hardware": "4x A100 GPUs or optimized inference server",
        "use_for": [
            "irrigation_schedule_calculation",
            "fertilization_dosage_calculation",
            "pest_risk_scoring",
            "harvest_timing_logic",
            "internal_reasoning_nodes"
        ],
        "avoid_for": [
            "direct_farmer_responses",
            "conversational_chat"
        ],
        "notes": "Use for internal calculations. Output rewritten by Llama. Open-source."
    },
    
    "llama-3.1-8b-instant": {
        "provider": "groq",
        "license": "Llama 3 Community License (open-source)",
        "role": "chat",
        "strength": "balanced",
        "azerbaijani_quality": "medium-high",
        "math_logic_quality": "medium",
        "speed": "very_fast (300+ tok/s on Groq)",
        "self_hostable": True,
        "recommended_hardware": "2x A100 GPUs or single H100",
        "use_for": [
            "quick_responses",
            "simple_questions",
            "fallback_chat"
        ],
        "notes": "Fast and capable. Open-source. Good default."
    },
    
    "mixtral-8x7b-32768": {
        "provider": "groq",
        "license": "Apache 2.0 (fully open-source)",
        "role": "chat_complex",
        "strength": "large_context",
        "azerbaijani_quality": "medium-high",
        "math_logic_quality": "high",
        "speed": "fast (180+ tok/s on Groq)",
        "self_hostable": True,
        "recommended_hardware": "8x A100 GPUs (MoE architecture)",
        "use_for": [
            "complex_multi_turn_conversations",
            "large_context_analysis",
            "document_understanding"
        ],
        "notes": "Mixture-of-Experts architecture. Open-source. 32k context."
    },
}


# ============================================================
# LangGraph Node → Model Mapping
# ============================================================

LANGGRAPH_NODE_MODELS = {
    # ===== 2026 MAVERICK MODE (Recommended) =====
    # Single Maverick model handles ALL nodes - simplest architecture
    "maverick": {
        "supervisor": "meta-llama/llama-4-maverick-17b-128e-instruct",
        "intent_classifier": "meta-llama/llama-4-maverick-17b-128e-instruct",
        "irrigation_calculator": "meta-llama/llama-4-maverick-17b-128e-instruct",
        "fertilization_calculator": "meta-llama/llama-4-maverick-17b-128e-instruct",
        "pest_analyzer": "meta-llama/llama-4-maverick-17b-128e-instruct",
        "weather_interpreter": "meta-llama/llama-4-maverick-17b-128e-instruct",
        "response_writer": "meta-llama/llama-4-maverick-17b-128e-instruct",
        "rule_validator": "meta-llama/llama-4-maverick-17b-128e-instruct",
        "image_analyzer": "meta-llama/llama-4-maverick-17b-128e-instruct",  # NEW!
    },
    
    # ===== LEGACY OPEN-SOURCE DEPLOYMENT (Qwen + Llama stack) =====
    # Deprecated: Use maverick mode instead
    "open_source": {
        "supervisor": "llama-3.3-70b-versatile",  # Route conversations
        "intent_classifier": "llama-3.1-8b-instant",  # Fast classification
        "irrigation_calculator": "qwen3-32b",  # Math-heavy
        "fertilization_calculator": "qwen3-32b",  # Dosage calculations
        "pest_analyzer": "qwen3-32b",  # Risk scoring
        "weather_interpreter": "llama-3.3-70b-versatile",  # Language-heavy
        "response_writer": "llama-3.3-70b-versatile",  # Final farmer-facing output
        "rule_validator": "qwen3-32b",  # Logic validation
    },
    
    # ===== PROPRIETARY CLOUD (Gemini) =====
    "proprietary": {
        "supervisor": "gemini-2.0-flash-exp",
        "intent_classifier": "gemini-2.0-flash-exp",
        "irrigation_calculator": "gemini-2.0-flash-exp",
        "fertilization_calculator": "gemini-2.0-flash-exp",
        "pest_analyzer": "gemini-2.0-flash-exp",
        "weather_interpreter": "gemini-2.0-flash-exp",
        "response_writer": "gemini-2.0-flash-exp",
        "rule_validator": "gemini-2.0-flash-exp",
    },
}


# ============================================================
# System Prompt Strategy by Model
# ============================================================

SYSTEM_PROMPT_STRATEGY = {
    # 2026 Gold Standard
    "meta-llama/llama-4-maverick-17b-128e-instruct": {
        "prompt_file": "prompts/system/master_v1.0.0_az_strict.txt",
        "linguistic_anchors": True,  # Belt-and-suspenders (though native Azerbaijani)
        "format_instructions": True,  # Include response formatting
        "few_shot_examples": 3,  # Include examples
        "notes": "Full system prompt. Maverick has native Azerbaijani - minimal leakage risk."
    },
    
    # Legacy models
    "llama-3.3-70b-versatile": {
        "prompt_file": "prompts/system/master_v1.0.0_az_strict.txt",
        "linguistic_anchors": True,  # Include negative constraints
        "format_instructions": True,  # Include response formatting
        "few_shot_examples": 3,  # Include examples
        "notes": "Full system prompt with strict Azerbaijani rules"
    },
    
    "qwen3-32b": {
        "prompt_file": "prompts/system/reasoning_node.txt",
        "linguistic_anchors": False,  # Output will be rewritten anyway
        "format_instructions": False,  # Just need the logic
        "few_shot_examples": 1,  # Minimal examples
        "notes": "Stripped-down prompt for internal reasoning. Output not shown to user."
    },
    
    "atllama": {
        "prompt_file": "prompts/system/master_v1.0.0_az_strict.txt",
        "linguistic_anchors": True,  # Belt-and-suspenders
        "format_instructions": True,
        "few_shot_examples": 3,
        "notes": "Same as Llama. ATLLaMA is already trained to avoid Turkish."
    },
    
    "qwen3:4b": {
        "prompt_file": "prompts/system/reasoning_node.txt",
        "linguistic_anchors": False,
        "format_instructions": False,
        "few_shot_examples": 0,
        "notes": "Local reasoning node. Output rewritten by ATLLaMA."
    },
}


# ============================================================
# Helper Functions
# ============================================================

def get_model_for_node(node_name: str, deployment_mode: str = "maverick") -> str:
    """
    Get the recommended model for a LangGraph node.
    
    Args:
        node_name: Name of the LangGraph node
        deployment_mode: "maverick" (2026 default), "open_source" (legacy), or "proprietary"
    
    Returns:
        Model name string
    
    Example:
        >>> get_model_for_node("response_writer")  # Uses maverick by default
        'meta-llama/llama-4-maverick-17b-128e-instruct'
        
        >>> get_model_for_node("response_writer", "open_source")  # Legacy
        'llama-3.3-70b-versatile'
        
        >>> get_model_for_node("response_writer", "proprietary")
        'gemini-2.0-flash-exp'
    """
    default_model = (
        "meta-llama/llama-4-maverick-17b-128e-instruct" 
        if deployment_mode == "maverick" 
        else "llama-3.1-8b-instant" if deployment_mode == "open_source" 
        else "gemini-2.0-flash-exp"
    )
    return LANGGRAPH_NODE_MODELS.get(deployment_mode, {}).get(node_name, default_model)


def get_system_prompt_for_model(model_name: str) -> dict:
    """
    Get system prompt strategy for a specific model.
    
    Args:
        model_name: Name of the model
    
    Returns:
        Dictionary with prompt configuration
    """
    return SYSTEM_PROMPT_STRATEGY.get(
        model_name,
        {
            "prompt_file": "prompts/system/master_v1.0.0_az_strict.txt",
            "linguistic_anchors": True,
            "format_instructions": True,
            "few_shot_examples": 2,
        }
    )


def should_rewrite_response(source_model: str, target_model: str | None = None) -> bool:
    """
    Determine if a response from source_model needs to be rewritten
    by a language-focused model.
    
    NOTE: With Maverick (2026), rewriting is rarely needed since it handles
    both logic AND language natively. This function is kept for legacy support.
    
    Args:
        source_model: The model that generated the response
        target_model: Optional target model for rewriting
    
    Returns:
        True if rewriting is recommended
    
    Example:
        >>> should_rewrite_response("qwen3-32b")
        True  # Qwen output should be rewritten by Llama
        
        >>> should_rewrite_response("meta-llama/llama-4-maverick-17b-128e-instruct")
        False  # Maverick handles everything - no rewrite needed
        
        >>> should_rewrite_response("llama-3.3-70b-versatile")
        False  # Already language-optimized
    """
    # Maverick never needs rewriting - it's the all-in-one solution
    if "maverick" in source_model.lower():
        return False
    
    # Legacy Qwen models still need rewriting for Turkish leakage
    reasoning_models = ["qwen3-32b", "qwen/qwen3-32b"]
    return source_model in reasoning_models


# ============================================================
# Testing Checklist
# ============================================================

"""
LANGUAGE QUALITY TESTS
======================

Test each model with this prompt to check for Turkish leakage:

Prompt: "Buğda əkmək üçün ən yaxşı vaxt nədir?"

Expected Response Quality:
---------------------------
✅ CORRECT (Azerbaijani):
   "Buğda əkini üçün ən yaxşı vaxt Sentyabr və Oktyabr aylarıdır.
    Torpağı əvvəlcədən hazırlamaq lazımdır..."

❌ WRONG (Turkish leakage):
   "Buğday ekimi için en iyi zaman Eylül ayıdır.
    Zemin hazırlığı yapmalısınız..."

Test Phrases to Check:
----------------------
- Month names: Sentyabr (NOT eylül)
- Soil: torpaq (NOT zemin)
- Irrigation: suvarma (NOT sulama)
- Seed: toxum (NOT tohum)
- Crop: məhsul (NOT ürün)

Run these tests:
1. Simple question test (above)
2. Complex calculation test (fertilization dosage)
3. Multi-turn conversation test
4. Edge case test (asking in Turkish, expecting Azerbaijani response)
"""

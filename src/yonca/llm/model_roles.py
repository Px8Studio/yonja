# Yonca AI - Model Role Configuration
# Dual-Strategy Approach for Language Quality + Logic Accuracy

"""
MODEL ROLES IN YONCA AI ARCHITECTURE
=====================================

Based on 2026 benchmarks and Azerbaijani language testing, we use a dual-model
strategy to balance linguistic quality with mathematical/logical reasoning.

Background:
-----------
Azerbaijani is linguistically close to Turkish, causing "language interference"
in general-purpose models. Models trained with Turkish data often "leak" Turkish
vocabulary when uncertain (e.g., "eylül" instead of "Sentyabr", "zemin" instead
of "torpaq").

The Solution: Role-Based Model Selection
-----------------------------------------
Different models excel at different tasks:
- Llama models: Better multilingual balance, less Turkish leakage
- Qwen models: Superior math/logic, but higher Turkish interference
- ATLLaMA (local): Fine-tuned specifically for Azerbaijani

Strategy:
---------
1. LOGIC/CALCULATION Nodes → Use Qwen (output hidden from user)
2. LANGUAGE/CHAT Nodes → Use Llama or ATLLaMA (user-facing)
3. OFFLINE Mode → Always use ATLLaMA (best Azerbaijani quality)
"""

# ============================================================
# Model Role Definitions
# ============================================================

MODEL_ROLES = {
    # ===== CLOUD MODELS (Groq) =====
    "llama-3.3-70b-versatile": {
        "provider": "groq",
        "role": "chat",  # User-facing conversation
        "strength": "language_quality",
        "azerbaijani_quality": "high",
        "math_logic_quality": "medium-high",
        "speed": "fast",
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
        "notes": "Best for final user-facing responses. Less Turkish leakage."
    },
    
    "qwen3-32b": {
        "provider": "groq",
        "role": "reasoning",  # Internal logic, hidden from user
        "strength": "math_logic",
        "azerbaijani_quality": "medium",  # Some Turkish leakage
        "math_logic_quality": "very_high",
        "speed": "very_fast",
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
        "notes": "Use for internal LangGraph nodes where output is rewritten by Llama"
    },
    
    "llama-3.1-8b-instant": {
        "provider": "groq",
        "role": "chat",
        "strength": "balanced",
        "azerbaijani_quality": "medium-high",
        "math_logic_quality": "medium",
        "speed": "very_fast",
        "use_for": [
            "quick_responses",
            "simple_questions",
            "fallback_chat"
        ],
        "notes": "Fast and capable, good default for Groq"
    },
    
    # ===== LOCAL MODELS (Ollama) =====
    "atllama": {
        "provider": "ollama",
        "role": "offline_expert",  # Best Azerbaijani, slow but accurate
        "strength": "azerbaijani_native",
        "azerbaijani_quality": "very_high",  # Fine-tuned specifically
        "math_logic_quality": "medium",
        "speed": "slow",  # CPU-dependent
        "use_for": [
            "offline_mode",
            "azerbaijani_quality_critical",
            "when_cloud_unavailable",
            "final_response_when_local"
        ],
        "notes": "Fine-tuned on Azerbaijani. ALWAYS use when offline. No Turkish leakage."
    },
    
    "qwen3:4b": {
        "provider": "ollama",
        "role": "local_reasoning",
        "strength": "math_logic",
        "azerbaijani_quality": "medium",
        "math_logic_quality": "high",
        "speed": "medium",  # Faster than atllama on CPU
        "use_for": [
            "local_calculations",
            "offline_reasoning",
            "when_atllama_unavailable"
        ],
        "notes": "Good for local reasoning, but rewrite output with ATLLaMA for language"
    },
}


# ============================================================
# LangGraph Node → Model Mapping
# ============================================================

LANGGRAPH_NODE_MODELS = {
    # ===== CLOUD MODE (Groq Available) =====
    "cloud": {
        "supervisor": "llama-3.3-70b-versatile",  # Route conversations
        "intent_classifier": "llama-3.1-8b-instant",  # Fast classification
        "irrigation_calculator": "qwen3-32b",  # Math-heavy
        "fertilization_calculator": "qwen3-32b",  # Dosage calculations
        "pest_analyzer": "qwen3-32b",  # Risk scoring
        "weather_interpreter": "llama-3.3-70b-versatile",  # Language-heavy
        "response_writer": "llama-3.3-70b-versatile",  # Final farmer-facing output
        "rule_validator": "qwen3-32b",  # Logic validation
    },
    
    # ===== LOCAL MODE (Offline/No API Keys) =====
    "local": {
        "supervisor": "atllama",  # Best Azerbaijani
        "intent_classifier": "atllama",
        "irrigation_calculator": "qwen3:4b",  # Calculate, then rewrite
        "fertilization_calculator": "qwen3:4b",
        "pest_analyzer": "qwen3:4b",
        "weather_interpreter": "atllama",
        "response_writer": "atllama",  # ALWAYS use for final response
        "rule_validator": "qwen3:4b",
    },
}


# ============================================================
# System Prompt Strategy by Model
# ============================================================

SYSTEM_PROMPT_STRATEGY = {
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

def get_model_for_node(node_name: str, deployment_mode: str = "cloud") -> str:
    """
    Get the recommended model for a LangGraph node.
    
    Args:
        node_name: Name of the LangGraph node
        deployment_mode: "cloud" or "local"
    
    Returns:
        Model name string
    
    Example:
        >>> get_model_for_node("response_writer", "cloud")
        'llama-3.3-70b-versatile'
        
        >>> get_model_for_node("response_writer", "local")
        'atllama'
    """
    return LANGGRAPH_NODE_MODELS.get(deployment_mode, {}).get(
        node_name,
        "llama-3.1-8b-instant" if deployment_mode == "cloud" else "atllama"
    )


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
    
    Args:
        source_model: The model that generated the response
        target_model: Optional target model for rewriting
    
    Returns:
        True if rewriting is recommended
    
    Example:
        >>> should_rewrite_response("qwen3-32b")
        True  # Qwen output should be rewritten by Llama/ATLLaMA
        
        >>> should_rewrite_response("llama-3.3-70b-versatile")
        False  # Already language-optimized
    """
    reasoning_models = ["qwen3-32b", "qwen3:4b"]
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

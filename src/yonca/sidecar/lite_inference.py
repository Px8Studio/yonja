"""
Yonca AI - Lite-Inference Engine
================================

Edge-optimized inference for low-bandwidth rural areas.
Supports GGUF quantization for offline/edge deployment.

Modes:
- STANDARD: Full Qwen2.5-7B inference via Ollama
- LITE: Quantized GGUF (Q4_K_M) for reduced memory/bandwidth
- OFFLINE: Pure rule-based fallback with no network dependency

Design Goals:
- <2GB memory footprint in LITE mode
- Sub-second response time for rule-based queries
- Graceful degradation when network unavailable
"""

import time
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Optional
from datetime import datetime

from pydantic import BaseModel, Field


class InferenceMode(str, Enum):
    """Available inference modes."""
    STANDARD = "standard"      # Full model via Ollama API
    LITE = "lite"              # Quantized GGUF for edge
    OFFLINE = "offline"        # Pure rule-based, no LLM
    AUTO = "auto"              # Automatically select based on conditions


class InferenceCapability(BaseModel):
    """Describes the capabilities of current inference mode."""
    mode: InferenceMode
    has_llm: bool
    has_network: bool
    memory_mb: int
    supports_multilingual: bool
    supports_rag: bool
    estimated_latency_ms: int


@dataclass 
class GGUFModelConfig:
    """Configuration for GGUF quantized models."""
    model_name: str
    gguf_filename: str
    quantization: str  # Q4_K_M, Q5_K_M, Q8_0, etc.
    context_length: int
    memory_required_mb: int
    download_url: Optional[str] = None
    
    # Performance characteristics
    tokens_per_second: float = 10.0  # Expected generation speed
    
    @property
    def is_available(self) -> bool:
        """Check if the GGUF file exists locally."""
        models_dir = Path.home() / ".cache" / "yonca" / "models"
        return (models_dir / self.gguf_filename).exists()


# Pre-defined GGUF configurations for Azerbaijani language support
GGUF_MODELS = {
    "qwen2.5-7b-q4": GGUFModelConfig(
        model_name="qwen2.5:7b",
        gguf_filename="qwen2.5-7b-instruct-q4_k_m.gguf",
        quantization="Q4_K_M",
        context_length=4096,
        memory_required_mb=4500,
        tokens_per_second=15.0,
    ),
    "qwen2.5-7b-q5": GGUFModelConfig(
        model_name="qwen2.5:7b",
        gguf_filename="qwen2.5-7b-instruct-q5_k_m.gguf",
        quantization="Q5_K_M",
        context_length=4096,
        memory_required_mb=5500,
        tokens_per_second=12.0,
    ),
    "qwen2.5-3b-q4": GGUFModelConfig(
        model_name="qwen2.5:3b",
        gguf_filename="qwen2.5-3b-instruct-q4_k_m.gguf",
        quantization="Q4_K_M",
        context_length=4096,
        memory_required_mb=2000,
        tokens_per_second=25.0,
    ),
    # Ultra-lite for very constrained devices
    "qwen2.5-1.5b-q4": GGUFModelConfig(
        model_name="qwen2.5:1.5b",
        gguf_filename="qwen2.5-1.5b-instruct-q4_k_m.gguf",
        quantization="Q4_K_M",
        context_length=2048,
        memory_required_mb=1200,
        tokens_per_second=40.0,
    ),
}


class NetworkCondition(BaseModel):
    """Current network condition assessment."""
    is_available: bool
    latency_ms: Optional[int] = None
    bandwidth_kbps: Optional[int] = None
    is_metered: bool = False


class LiteInferenceEngine:
    """
    Lite-Inference Engine for Edge and Low-Bandwidth Scenarios.
    
    Automatic mode selection:
    1. Check network availability
    2. Check available memory
    3. Select optimal inference mode
    4. Fallback gracefully if needed
    """
    
    # Thresholds for mode selection
    LITE_BANDWIDTH_THRESHOLD_KBPS = 500  # Below this, use LITE mode
    OFFLINE_TIMEOUT_MS = 5000  # If network latency exceeds this, go OFFLINE
    MIN_MEMORY_MB = 1500  # Minimum memory for any LLM inference
    
    def __init__(
        self,
        preferred_mode: InferenceMode = InferenceMode.AUTO,
        gguf_config: Optional[GGUFModelConfig] = None,
        ollama_base_url: str = "http://localhost:11434",
    ):
        """
        Initialize the Lite-Inference Engine.
        
        Args:
            preferred_mode: Preferred inference mode (AUTO for automatic selection)
            gguf_config: GGUF model configuration for LITE mode
            ollama_base_url: Base URL for Ollama API
        """
        self.preferred_mode = preferred_mode
        self.gguf_config = gguf_config or GGUF_MODELS.get("qwen2.5-3b-q4")
        self.ollama_base_url = ollama_base_url
        
        self._current_mode: Optional[InferenceMode] = None
        self._llm = None
        self._last_capability_check: Optional[datetime] = None
    
    def check_network_condition(self) -> NetworkCondition:
        """Assess current network conditions."""
        import socket
        
        # Quick connectivity check
        try:
            socket.setdefaulttimeout(3)
            socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect(("8.8.8.8", 53))
            is_available = True
        except (socket.error, OSError):
            is_available = False
        
        if not is_available:
            return NetworkCondition(is_available=False)
        
        # Check Ollama availability
        latency_ms = None
        try:
            import urllib.request
            start = time.time()
            urllib.request.urlopen(f"{self.ollama_base_url}/api/tags", timeout=3)
            latency_ms = int((time.time() - start) * 1000)
        except Exception:
            # Ollama not running, but network is available
            latency_ms = None
        
        return NetworkCondition(
            is_available=True,
            latency_ms=latency_ms,
            bandwidth_kbps=None,  # Would need actual bandwidth test
            is_metered=False,
        )
    
    def check_available_memory(self) -> int:
        """Check available system memory in MB."""
        try:
            import psutil
            return int(psutil.virtual_memory().available / (1024 * 1024))
        except ImportError:
            # psutil not available, estimate conservatively
            return 4000  # Assume 4GB available
    
    def select_optimal_mode(self) -> InferenceMode:
        """
        Automatically select the optimal inference mode.
        
        Decision tree:
        1. If network + Ollama available + sufficient memory → STANDARD
        2. If network limited but GGUF available → LITE
        3. If no network or insufficient resources → OFFLINE
        """
        if self.preferred_mode != InferenceMode.AUTO:
            return self.preferred_mode
        
        network = self.check_network_condition()
        memory_mb = self.check_available_memory()
        
        # Check STANDARD mode feasibility
        if (
            network.is_available and
            network.latency_ms is not None and
            network.latency_ms < self.OFFLINE_TIMEOUT_MS and
            memory_mb >= self.MIN_MEMORY_MB
        ):
            return InferenceMode.STANDARD
        
        # Check LITE mode feasibility
        if (
            memory_mb >= self.gguf_config.memory_required_mb and
            self.gguf_config.is_available
        ):
            return InferenceMode.LITE
        
        # Fallback to OFFLINE
        return InferenceMode.OFFLINE
    
    def get_capability(self) -> InferenceCapability:
        """Get current inference capabilities."""
        mode = self.select_optimal_mode()
        memory = self.check_available_memory()
        network = self.check_network_condition()
        
        if mode == InferenceMode.STANDARD:
            return InferenceCapability(
                mode=mode,
                has_llm=True,
                has_network=True,
                memory_mb=memory,
                supports_multilingual=True,
                supports_rag=True,
                estimated_latency_ms=500,
            )
        elif mode == InferenceMode.LITE:
            return InferenceCapability(
                mode=mode,
                has_llm=True,
                has_network=network.is_available,
                memory_mb=memory,
                supports_multilingual=True,
                supports_rag=True,
                estimated_latency_ms=int(1000 / self.gguf_config.tokens_per_second * 100),
            )
        else:  # OFFLINE
            return InferenceCapability(
                mode=mode,
                has_llm=False,
                has_network=False,
                memory_mb=memory,
                supports_multilingual=False,  # Rule-based only supports pre-defined languages
                supports_rag=False,
                estimated_latency_ms=50,  # Very fast rule evaluation
            )
    
    def initialize_llm(self, mode: Optional[InferenceMode] = None):
        """
        Initialize the LLM for the selected mode.
        
        Args:
            mode: Mode to initialize for (None = use selected optimal mode)
        """
        target_mode = mode or self.select_optimal_mode()
        self._current_mode = target_mode
        
        if target_mode == InferenceMode.OFFLINE:
            self._llm = None
            return
        
        if target_mode == InferenceMode.STANDARD:
            try:
                from langchain_ollama import ChatOllama
                self._llm = ChatOllama(
                    model=self.gguf_config.model_name,
                    base_url=self.ollama_base_url,
                    temperature=0.7,
                )
            except ImportError:
                # Fallback to OFFLINE if langchain not available
                self._current_mode = InferenceMode.OFFLINE
                self._llm = None
        
        elif target_mode == InferenceMode.LITE:
            # For LITE mode with GGUF, we use llama-cpp-python or similar
            try:
                self._llm = self._create_gguf_llm()
            except Exception:
                self._current_mode = InferenceMode.OFFLINE
                self._llm = None
    
    def _create_gguf_llm(self):
        """Create an LLM instance from GGUF file."""
        try:
            from llama_cpp import Llama
            
            models_dir = Path.home() / ".cache" / "yonca" / "models"
            model_path = models_dir / self.gguf_config.gguf_filename
            
            if not model_path.exists():
                raise FileNotFoundError(f"GGUF model not found: {model_path}")
            
            llm = Llama(
                model_path=str(model_path),
                n_ctx=self.gguf_config.context_length,
                n_threads=4,  # Adjust based on CPU
                n_gpu_layers=0,  # CPU-only for edge devices
            )
            
            return LlamaCppWrapper(llm)
            
        except ImportError:
            # llama-cpp-python not installed, try langchain wrapper
            try:
                from langchain_community.llms import LlamaCpp
                
                models_dir = Path.home() / ".cache" / "yonca" / "models"
                model_path = models_dir / self.gguf_config.gguf_filename
                
                return LlamaCpp(
                    model_path=str(model_path),
                    n_ctx=self.gguf_config.context_length,
                    max_tokens=512,
                    temperature=0.7,
                )
            except ImportError:
                raise ImportError(
                    "GGUF inference requires either llama-cpp-python or langchain-community. "
                    "Install with: pip install llama-cpp-python"
                )
    
    @property
    def llm(self):
        """Get the current LLM instance (initializes if needed)."""
        if self._llm is None and self._current_mode != InferenceMode.OFFLINE:
            self.initialize_llm()
        return self._llm
    
    @property
    def current_mode(self) -> InferenceMode:
        """Get the current inference mode."""
        if self._current_mode is None:
            self._current_mode = self.select_optimal_mode()
        return self._current_mode
    
    def generate(
        self,
        prompt: str,
        max_tokens: int = 512,
        temperature: float = 0.7,
    ) -> tuple[str, dict]:
        """
        Generate a response using the current inference mode.
        
        Args:
            prompt: The input prompt
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            
        Returns:
            Tuple of (response_text, metadata_dict)
        """
        mode = self.current_mode
        start_time = time.time()
        
        metadata = {
            "mode": mode.value,
            "model": None,
            "tokens_generated": 0,
            "latency_ms": 0,
        }
        
        if mode == InferenceMode.OFFLINE:
            # No LLM generation in offline mode
            response = "[OFFLINE_MODE] Yalnız qayda əsaslı tövsiyələr mövcuddur."
            metadata["model"] = "rulebook-only"
        
        elif mode == InferenceMode.LITE:
            if self._llm is None:
                self.initialize_llm(InferenceMode.LITE)
            
            if self._llm:
                try:
                    result = self._llm.invoke(prompt)
                    response = result if isinstance(result, str) else str(result)
                    metadata["model"] = self.gguf_config.gguf_filename
                    metadata["tokens_generated"] = len(response.split())
                except Exception as e:
                    response = f"[LITE_ERROR] Xəta baş verdi: {str(e)}"
            else:
                response = "[LITE_UNAVAILABLE] GGUF model mövcud deyil."
        
        else:  # STANDARD
            if self._llm is None:
                self.initialize_llm(InferenceMode.STANDARD)
            
            if self._llm:
                try:
                    result = self._llm.invoke(prompt)
                    response = result.content if hasattr(result, 'content') else str(result)
                    metadata["model"] = self.gguf_config.model_name
                    metadata["tokens_generated"] = len(response.split())
                except Exception as e:
                    response = f"[STANDARD_ERROR] Xəta baş verdi: {str(e)}"
            else:
                response = "[STANDARD_UNAVAILABLE] Ollama xidməti mövcud deyil."
        
        metadata["latency_ms"] = int((time.time() - start_time) * 1000)
        
        return response, metadata
    
    def get_model_info(self) -> dict:
        """Get information about the current model configuration."""
        return {
            "current_mode": self.current_mode.value,
            "gguf_config": {
                "model_name": self.gguf_config.model_name,
                "quantization": self.gguf_config.quantization,
                "context_length": self.gguf_config.context_length,
                "memory_mb": self.gguf_config.memory_required_mb,
                "is_available": self.gguf_config.is_available,
            },
            "ollama_url": self.ollama_base_url,
            "capability": self.get_capability().model_dump(),
        }


class LlamaCppWrapper:
    """Wrapper to make llama-cpp-python compatible with langchain interface."""
    
    def __init__(self, llama_instance):
        self._llama = llama_instance
    
    def invoke(self, prompt: str, **kwargs) -> str:
        """Generate a response."""
        output = self._llama(
            prompt,
            max_tokens=kwargs.get("max_tokens", 512),
            temperature=kwargs.get("temperature", 0.7),
            stop=kwargs.get("stop", ["\n\n"]),
        )
        return output["choices"][0]["text"]


class EdgeDeploymentConfig(BaseModel):
    """Configuration for edge deployment scenarios."""
    
    # Device constraints
    max_memory_mb: int = Field(default=2000, description="Maximum memory available")
    has_gpu: bool = Field(default=False, description="GPU available for inference")
    
    # Network constraints
    expected_bandwidth_kbps: int = Field(default=256, description="Expected bandwidth")
    is_intermittent: bool = Field(default=True, description="Network connectivity intermittent")
    
    # Model preferences
    preferred_quantization: str = Field(default="Q4_K_M", description="Preferred GGUF quantization")
    max_context_length: int = Field(default=2048, description="Maximum context window")
    
    # Fallback behavior
    enable_offline_cache: bool = Field(default=True, description="Cache responses for offline use")
    rule_only_threshold_ms: int = Field(default=5000, description="Latency threshold to fall back to rules")
    
    def get_recommended_model(self) -> GGUFModelConfig:
        """Get the recommended GGUF model for this device configuration."""
        # Sort models by memory requirement
        suitable = [
            config for config in GGUF_MODELS.values()
            if config.memory_required_mb <= self.max_memory_mb
            and config.context_length <= self.max_context_length
        ]
        
        if not suitable:
            # Return smallest model even if over memory
            return min(GGUF_MODELS.values(), key=lambda c: c.memory_required_mb)
        
        # Prefer models with matching quantization
        preferred = [c for c in suitable if c.quantization == self.preferred_quantization]
        if preferred:
            return max(preferred, key=lambda c: c.context_length)
        
        return max(suitable, key=lambda c: c.context_length)


def create_lite_engine_for_edge(config: EdgeDeploymentConfig) -> LiteInferenceEngine:
    """
    Factory function to create a LiteInferenceEngine optimized for edge deployment.
    
    Args:
        config: Edge deployment configuration
        
    Returns:
        Configured LiteInferenceEngine instance
    """
    recommended_model = config.get_recommended_model()
    
    # Determine preferred mode based on network conditions
    if config.is_intermittent:
        preferred_mode = InferenceMode.AUTO  # Will adapt based on conditions
    elif config.expected_bandwidth_kbps < 100:
        preferred_mode = InferenceMode.OFFLINE
    elif config.expected_bandwidth_kbps < 500:
        preferred_mode = InferenceMode.LITE
    else:
        preferred_mode = InferenceMode.STANDARD
    
    return LiteInferenceEngine(
        preferred_mode=preferred_mode,
        gguf_config=recommended_model,
    )

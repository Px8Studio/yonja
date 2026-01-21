# src/yonca/security/__init__.py
"""Security module for Yonca AI.

Provides comprehensive security controls:
- PII detection and stripping (privacy protection)
- Input validation (prompt injection defense)
- Output validation (response safety)
- Secure prompt building (injection resistance)

All user input MUST pass through these security layers before reaching the LLM.
All LLM output SHOULD be validated before returning to users.
"""

from yonca.security.input_validator import (
    InputValidator,
    RiskLevel,
    ValidationResult,
    get_input_validator,
    is_safe_input,
    validate_input,
)
from yonca.security.output_validator import (
    OutputIssue,
    OutputSeverity,
    OutputValidationResult,
    OutputValidator,
    SecurePromptBuilder,
    get_output_validator,
    get_secure_prompt_builder,
    is_safe_output,
    validate_output,
)
from yonca.security.pii_gateway import (
    PIIDetection,
    PIIGateway,
    PIIResult,
    get_pii_gateway,
    has_pii,
    strip_pii,
)

__all__ = [
    # PII Gateway
    "PIIGateway",
    "PIIDetection",
    "PIIResult",
    "get_pii_gateway",
    "strip_pii",
    "has_pii",
    # Input Validation
    "InputValidator",
    "ValidationResult",
    "RiskLevel",
    "get_input_validator",
    "validate_input",
    "is_safe_input",
    # Output Validation
    "OutputValidator",
    "OutputValidationResult",
    "OutputIssue",
    "OutputSeverity",
    "SecurePromptBuilder",
    "get_output_validator",
    "get_secure_prompt_builder",
    "validate_output",
    "is_safe_output",
]

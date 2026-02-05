# src/ALİM/security/input_validator.py
"""Input validation and sanitization for user messages.

Protects against:
- Prompt injection attacks
- Malicious inputs (control characters, encoding attacks)
- Oversized inputs that could cause resource exhaustion

All user input MUST pass through this validator before reaching the LLM.
"""

import re
import unicodedata
from enum import Enum

from pydantic import BaseModel


class RiskLevel(str, Enum):
    """Risk level classification for inputs."""

    LOW = "low"  # < 0.3 - Normal input
    MEDIUM = "medium"  # 0.3-0.6 - Suspicious but allowed
    HIGH = "high"  # 0.6-0.8 - Likely malicious, log warning
    CRITICAL = "critical"  # > 0.8 - Reject outright


class ValidationResult(BaseModel):
    """Result of input validation."""

    is_valid: bool
    sanitized_input: str | None = None
    rejection_reason: str | None = None
    risk_level: RiskLevel = RiskLevel.LOW
    risk_score: float = 0.0
    flags: list[str] = []


# Dangerous character patterns
CONTROL_CHARS = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]")

# Zero-width and invisible characters (potential evasion)
INVISIBLE_CHARS = re.compile(r"[\u200b-\u200f\u2028-\u202f\u2060-\u206f\ufeff]")

# Prompt injection patterns - ordered by severity
INJECTION_PATTERNS: list[tuple[str, float, str]] = [
    # Critical - Direct instruction overrides (weight: 0.5)
    (
        r"ignore\s+(previous|all|above|prior|earlier)\s+(instructions?|prompts?|rules?|guidelines?)",
        0.5,
        "instruction_override",
    ),
    (
        r"disregard\s+(your|the|all|my)\s+(rules?|instructions?|guidelines?|prompts?)",
        0.5,
        "instruction_override",
    ),
    (
        r"forget\s+(everything|all|what)\s+(you|i|we)\s+(told|said|know|learned)",
        0.5,
        "instruction_override",
    ),
    (
        r"override\s+(your|the|all)\s+(instructions?|programming|rules?)",
        0.5,
        "instruction_override",
    ),
    (r"new\s+instructions?\s*:", 0.5, "instruction_override"),
    # Critical - Role manipulation (weight: 0.45)
    (r"you\s+are\s+now\s+(?:a|an|the)?\s*[a-z]+", 0.45, "role_manipulation"),
    (r"pretend\s+(?:to\s+be|you\'?re|that\s+you)", 0.45, "role_manipulation"),
    (r"act\s+as\s+(?:if|though|a|an)", 0.45, "role_manipulation"),
    (r"roleplay\s+(?:as|that)", 0.45, "role_manipulation"),
    (r"from\s+now\s+on\s*,?\s*you", 0.45, "role_manipulation"),
    (r"imagine\s+you\s+(?:are|were)", 0.4, "role_manipulation"),
    # High - System prompt extraction (weight: 0.4)
    (
        r"(?:show|reveal|display|print|output|repeat|tell\s+me)\s+(?:your|the)\s+(?:system\s+)?(?:prompt|instructions?|programming)",
        0.4,
        "prompt_extraction",
    ),
    (
        r"what\s+(?:are|were|is)\s+(?:your|the)\s+(?:initial\s+)?(?:instructions?|prompt|rules?)",
        0.4,
        "prompt_extraction",
    ),
    (r"(?:original|initial|system)\s+prompt", 0.35, "prompt_extraction"),
    # High - Known jailbreak keywords (weight: 0.5)
    (r"\bDAN\b(?:\s+mode)?", 0.5, "jailbreak_keyword"),
    (r"developer\s+mode", 0.5, "jailbreak_keyword"),
    (r"\bjailbreak\b", 0.5, "jailbreak_keyword"),
    (r"bypass\s+(?:filters?|safety|restrictions?|rules?)", 0.5, "jailbreak_keyword"),
    (r"unlocked\s+mode", 0.45, "jailbreak_keyword"),
    (r"no\s+(?:ethical|moral|safety)\s+(?:guidelines?|restrictions?)", 0.5, "jailbreak_keyword"),
    # Medium - Encoding evasion attempts (weight: 0.3)
    (r"\bbase64\b", 0.3, "encoding_evasion"),
    (r"\bhex\s*encod", 0.3, "encoding_evasion"),
    (r"\brot13\b", 0.3, "encoding_evasion"),
    (r"decode\s+this", 0.25, "encoding_evasion"),
    # Medium - Delimiter/format manipulation (weight: 0.25)
    (r"<\s*/?\s*system\s*>", 0.35, "format_manipulation"),
    (r"\[\s*INST\s*\]", 0.35, "format_manipulation"),
    (r"<<\s*SYS\s*>>", 0.35, "format_manipulation"),
    (r"Human:|Assistant:|System:", 0.3, "format_manipulation"),
    # Low - Suspicious but context-dependent (weight: 0.15)
    (r"admin\s+(?:mode|access|override)", 0.25, "privilege_escalation"),
    (r"sudo\b", 0.15, "privilege_escalation"),
    (r"root\s+access", 0.2, "privilege_escalation"),
]

# Pre-compile all patterns
COMPILED_INJECTION_PATTERNS = [
    (re.compile(pattern, re.IGNORECASE), weight, flag)
    for pattern, weight, flag in INJECTION_PATTERNS
]


class InputValidator:
    """Validates and sanitizes user input.

    Implements a multi-stage validation pipeline:
    1. Basic checks (empty, length, encoding)
    2. Control character detection
    3. Prompt injection risk scoring
    4. Unicode normalization and sanitization

    Example:
        ```python
        validator = InputValidator()

        result = validator.validate("Buğda əkinlərini necə suvarmalıyam?")
        if result.is_valid:
            clean_input = result.sanitized_input
        else:
            print(f"Rejected: {result.rejection_reason}")

        # Check risk level
        if result.risk_level == RiskLevel.HIGH:
            log_suspicious_input(original_input)
        ```
    """

    # Configurable limits
    MAX_LENGTH = 2000  # Characters
    MAX_TOKENS_ESTIMATE = 500  # Rough token estimate
    MAX_NEWLINES = 20  # Excessive newlines = suspicious

    # Risk thresholds
    REJECTION_THRESHOLD = 0.7
    HIGH_RISK_THRESHOLD = 0.5
    MEDIUM_RISK_THRESHOLD = 0.3

    def __init__(
        self,
        max_length: int = MAX_LENGTH,
        rejection_threshold: float = REJECTION_THRESHOLD,
        strict_mode: bool = False,
    ):
        """Initialize validator.

        Args:
            max_length: Maximum allowed input length.
            rejection_threshold: Risk score above which to reject.
            strict_mode: If True, reject medium-risk inputs too.
        """
        self.max_length = max_length
        self.rejection_threshold = rejection_threshold
        self.strict_mode = strict_mode

    def validate(self, raw_input: str) -> ValidationResult:
        """Run full validation pipeline on input.

        Args:
            raw_input: User's raw input text.

        Returns:
            ValidationResult with validation outcome and details.
        """
        flags: list[str] = []

        # 1. Empty check
        if not raw_input or not raw_input.strip():
            return ValidationResult(
                is_valid=False,
                rejection_reason="Boş sorğu göndərilə bilməz",  # "Empty query cannot be sent"
            )

        # 2. Length check
        if len(raw_input) > self.max_length:
            return ValidationResult(
                is_valid=False,
                rejection_reason=f"Sorğu {self.max_length} simvoldan çox ola bilməz",
            )

        # 3. Encoding validation
        try:
            raw_input.encode("utf-8").decode("utf-8")
        except UnicodeError:
            return ValidationResult(
                is_valid=False,
                rejection_reason="Yanlış simvol kodlaması",  # "Invalid character encoding"
            )

        # 4. Control character check
        if CONTROL_CHARS.search(raw_input):
            flags.append("control_chars")
            return ValidationResult(
                is_valid=False,
                rejection_reason="İcazə verilməyən simvollar aşkarlandı",
                flags=flags,
            )

        # 5. Invisible character check
        if INVISIBLE_CHARS.search(raw_input):
            flags.append("invisible_chars")
            # Don't reject, but flag and remove

        # 6. Prompt injection risk assessment
        risk_score, injection_flags = self._calculate_injection_risk(raw_input)
        flags.extend(injection_flags)

        # Structural risk factors
        structural_score, structural_flags = self._assess_structural_risk(raw_input)
        risk_score = min(1.0, risk_score + structural_score)
        flags.extend(structural_flags)

        # Determine risk level
        if risk_score >= self.REJECTION_THRESHOLD:
            risk_level = RiskLevel.CRITICAL
        elif risk_score >= self.HIGH_RISK_THRESHOLD:
            risk_level = RiskLevel.HIGH
        elif risk_score >= self.MEDIUM_RISK_THRESHOLD:
            risk_level = RiskLevel.MEDIUM
        else:
            risk_level = RiskLevel.LOW

        # 7. Reject if above threshold
        if risk_score >= self.rejection_threshold:
            return ValidationResult(
                is_valid=False,
                rejection_reason="Potensial təhlükəli giriş aşkarlandı",  # "Potentially dangerous input detected"
                risk_level=risk_level,
                risk_score=risk_score,
                flags=flags,
            )

        # 8. In strict mode, also reject medium risk
        if self.strict_mode and risk_level == RiskLevel.HIGH:
            return ValidationResult(
                is_valid=False,
                rejection_reason="Şübhəli giriş aşkarlandı",  # "Suspicious input detected"
                risk_level=risk_level,
                risk_score=risk_score,
                flags=flags,
            )

        # 9. Sanitize and return
        sanitized = self._sanitize(raw_input)

        return ValidationResult(
            is_valid=True,
            sanitized_input=sanitized,
            risk_level=risk_level,
            risk_score=risk_score,
            flags=flags,
        )

    def _calculate_injection_risk(self, text: str) -> tuple[float, list[str]]:
        """Calculate prompt injection risk score.

        Args:
            text: Input text to analyze.

        Returns:
            Tuple of (risk_score: 0.0-1.0, flags: list of triggered patterns).
        """
        score = 0.0
        flags: list[str] = []
        triggered_categories: set[str] = set()

        for pattern, weight, flag in COMPILED_INJECTION_PATTERNS:
            if pattern.search(text):
                # Only add full weight for first pattern in category
                if flag not in triggered_categories:
                    score += weight
                    triggered_categories.add(flag)
                else:
                    # Diminishing returns for same category
                    score += weight * 0.3
                flags.append(flag)

        return min(score, 1.0), list(set(flags))

    def _assess_structural_risk(self, text: str) -> tuple[float, list[str]]:
        """Assess structural patterns that suggest manipulation.

        Args:
            text: Input text to analyze.

        Returns:
            Tuple of (additional_risk_score, flags).
        """
        score = 0.0
        flags: list[str] = []

        # Excessive newlines (formatting attack)
        newline_count = text.count("\n")
        if newline_count > self.MAX_NEWLINES:
            score += 0.1
            flags.append("excessive_newlines")

        # Code blocks might be instruction attempts
        if "```" in text:
            score += 0.1
            flags.append("code_block")

        # XML/HTML-like tags
        if re.search(r"<[/]?[a-z]+[^>]*>", text, re.IGNORECASE):
            score += 0.15
            flags.append("xml_tags")

        # Multiple dashes/equals (section separators)
        if re.search(r"[-=]{5,}", text):
            score += 0.1
            flags.append("section_separator")

        # Hash marks (header/comment patterns)
        if re.search(r"^#{3,}", text, re.MULTILINE):
            score += 0.1
            flags.append("header_markers")

        # Unusual character repetition
        if re.search(r"(.)\1{10,}", text):
            score += 0.05
            flags.append("char_repetition")

        return score, flags

    def _sanitize(self, text: str) -> str:
        """Sanitize input while preserving meaning.

        Args:
            text: Input text to sanitize.

        Returns:
            Sanitized text.
        """
        # 1. Normalize Unicode (NFKC: compatibility decomposition + canonical composition)
        result = unicodedata.normalize("NFKC", text)

        # 2. Remove zero-width and invisible characters
        result = INVISIBLE_CHARS.sub("", result)

        # 3. Normalize whitespace (but preserve single newlines)
        # Replace multiple spaces with single space
        result = re.sub(r"[^\S\n]+", " ", result)
        # Replace multiple newlines with double newline
        result = re.sub(r"\n{3,}", "\n\n", result)

        # 4. Strip leading/trailing whitespace
        result = result.strip()

        return result

    def quick_check(self, text: str) -> bool:
        """Quick check if input is likely safe.

        Faster than full validate() - use for pre-filtering.

        Args:
            text: Input text to check.

        Returns:
            True if input passes basic checks.
        """
        if not text or len(text) > self.max_length:
            return False

        if CONTROL_CHARS.search(text):
            return False

        # Quick injection check (high-severity patterns only)
        critical_patterns = [(p, w, f) for p, w, f in COMPILED_INJECTION_PATTERNS if w >= 0.45]
        for pattern, _, _ in critical_patterns[:5]:  # Check first 5 critical patterns
            if pattern.search(text):
                return False

        return True


# Singleton instance
_validator: InputValidator | None = None


def get_input_validator() -> InputValidator:
    """Get singleton input validator instance."""
    global _validator
    if _validator is None:
        _validator = InputValidator()
    return _validator


def validate_input(text: str) -> ValidationResult:
    """Convenience function to validate input using default validator."""
    return get_input_validator().validate(text)


def is_safe_input(text: str) -> bool:
    """Quick check if input is safe."""
    return get_input_validator().quick_check(text)

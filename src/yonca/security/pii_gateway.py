# src/yonca/security/pii_gateway.py
"""PII (Personally Identifiable Information) detection and stripping.

Ensures no real personal data reaches the LLM. Uses Azerbaijani-specific
patterns for names, phone numbers, FIN codes, etc.

The AI NEVER sees real PII - all detected PII is replaced with placeholders.
"""

import re
from dataclasses import dataclass, field
from typing import Optional

from pydantic import BaseModel


@dataclass
class PIIDetection:
    """Detected PII instance with details for logging/auditing."""
    
    pii_type: str
    original: str
    replacement: str
    start_pos: int
    end_pos: int
    
    def __repr__(self) -> str:
        return f"PIIDetection({self.pii_type}: '{self.original[:3]}...' -> '{self.replacement}')"


class PIIResult(BaseModel):
    """Result of PII detection and stripping."""
    
    cleaned_text: str
    has_pii: bool
    detection_count: int
    pii_types_found: list[str] = []


class PIIGateway:
    """Detects and strips PII from text.
    
    Implements Azerbaijani-specific PII patterns:
    - Phone numbers (local and international format)
    - FIN codes (7-character alphanumeric)
    - ID card numbers
    - Full names (common Azerbaijani name patterns)
    - Email addresses
    - IBAN account numbers
    - GPS coordinates
    - Real parcel/cadastral IDs
    
    Example:
        ```python
        gateway = PIIGateway()
        
        # Check and clean user input
        result = gateway.strip_pii("Mənim nömrəm +994 50 123 45 67")
        print(result.cleaned_text)  # "Mənim nömrəm [TELEFON]"
        print(result.has_pii)       # True
        
        # Quick check
        if gateway.has_pii("Some text"):
            print("Contains PII!")
        ```
    """
    
    # Azerbaijani-specific PII patterns
    # Each pattern: (regex_pattern, replacement_placeholder)
    PATTERNS: dict[str, tuple[str, str]] = {
        # Phone numbers - must be processed before FIN to avoid conflicts
        "phone_az_intl": (
            r'\+994\s*[\-\.]?\s*\(?\d{2}\)?\s*[\-\.]?\s*\d{3}\s*[\-\.]?\s*\d{2}\s*[\-\.]?\s*\d{2}',
            "[TELEFON]"
        ),
        "phone_az_local": (
            r'\b0\d{2}\s*[\-\.]?\s*\d{3}\s*[\-\.]?\s*\d{2}\s*[\-\.]?\s*\d{2}\b',
            "[TELEFON]"
        ),
        "phone_simple": (
            # Catches standalone phone-like sequences (7 digits with separators)
            r'(?<![+\d])\b\d{3}[\s\-\.]\d{2}[\s\-\.]\d{2}\b(?!\d)',
            "[TELEFON]"
        ),
        
        # Government IDs
        "fin_code": (
            # FIN: 7 characters, must have at least one letter AND one digit
            # More specific to avoid matching random 7-char sequences
            r'\b(?=[A-Z0-9]*[A-Z])(?=[A-Z0-9]*\d)[A-Z0-9]{7}\b',
            "[FİN]"
        ),
        "id_card": (
            # Azerbaijani ID cards: AZE or AA followed by 7-8 digits
            r'\b(?:AZE|AA)\d{7,8}\b',
            "[ŞV_NÖMRƏSİ]"
        ),
        "voen": (
            # VOEN (Tax ID): 10 digits
            r'\bVOEN\s*:?\s*\d{10}\b',
            "[VOEN]"
        ),
        
        # Personal names - common Azerbaijani name patterns
        # First names (extended list)
        "name_full": (
            r'\b(?:'
            # Male first names
            r'Əli|Vəli|Məmməd|Rəsul|Elçin|Orxan|Tural|Namiq|Rəşad|Cavid|'
            r'Farid|Samir|Elşən|Rauf|Fikrət|İlham|Ramil|Anar|Zaur|Ramin|'
            r'Şahin|Emin|Seymur|Nicat|Elvin|Ceyhun|Murad|Ruslan|Akif|'
            # Female first names  
            r'Nigar|Aynur|Günay|Leyla|Sevinc|Aysel|Günel|Lalə|Nərgiz|Samirə|'
            r'Sevil|Fidan|Aytən|Nuray|Könül|Arzu|Vüsalə|Səbinə|Röya|Ülviyyə'
            r')\s+'
            # Patronymic surnames
            r'(?:Məmmədov|Əliyev|Həsənov|Hüseynov|Quliyev|Rəhimov|İsmayılov|'
            r'Mustafayev|Babayev|Nəsirov|Süleymanov|Kazımov|Məmmədova|Əliyeva|'
            r'Həsənova|Hüseynova|Quliyeva|Rəhimova|İsmayılova|Mustafayeva)'
            # Optional patronymic suffix
            r'(?:\s+(?:oğlu|qızı))?',
            "[ŞƏXS]"
        ),
        
        # Standalone common surnames (less specific, lower priority)
        "surname_only": (
            r'\b(?:Məmmədov|Əliyev|Həsənov|Hüseynov|Quliyev|Rəhimov|'
            r'İsmayılov|Mustafayev|Babayev|Nəsirov|Süleymanov|Kazımov|'
            r'Məmmədova|Əliyeva|Həsənova|Hüseynova|Quliyeva)a?\b',
            "[ŞƏXS]"
        ),
        
        # Digital identifiers
        "email": (
            r'[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}',
            "[EMAIL]"
        ),
        "iban_az": (
            # Azerbaijani IBAN: AZ + 2 check digits + 4 bank code + 16-20 account digits
            # Total length: 24-28 characters
            r'\bAZ\d{2}[A-Z]{4}\d{16,20}\b',
            "[IBAN]"
        ),
        "card_number": (
            # Credit/debit card numbers
            r'\b(?:\d{4}[\s\-]?){3}\d{4}\b',
            "[KART]"
        ),
        
        # Location identifiers
        "gps_coordinates": (
            # Latitude/longitude pairs (Azerbaijan is roughly 38-42°N, 44-51°E)
            r'\b(?:3[89]|4[0-2])\.\d{4,8}\s*,\s*(?:4[4-9]|5[01])\.\d{4,8}\b',
            "[GPS]"
        ),
        "real_parcel_id": (
            # Real cadastral parcel IDs (not synthetic)
            r'\bAZ-[A-Z]{2,3}-\d{4,8}\b(?!.*syn)',
            "[SAHƏ_ID]"
        ),
        
        # Addresses with specific patterns
        "address_detailed": (
            # Street address patterns (Küçə = street, Mənzil = apartment)
            r'(?:Küçə|Prospekt|Bulvar)\s+[\w\s]+,?\s*(?:ev|bina|blok)\s*\d+,?\s*(?:m|mənzil)?\s*\d+',
            "[ÜNVAN]"
        ),
    }
    
    def __init__(self, additional_patterns: Optional[dict[str, tuple[str, str]]] = None):
        """Initialize PII Gateway.
        
        Args:
            additional_patterns: Extra patterns to detect, format: {name: (regex, replacement)}
        """
        patterns = self.PATTERNS.copy()
        if additional_patterns:
            patterns.update(additional_patterns)
        
        # Compile all patterns (case-insensitive for most)
        self._compiled_patterns: dict[str, tuple[re.Pattern, str]] = {}
        for name, (pattern, replacement) in patterns.items():
            # Some patterns should be case-sensitive (FIN, IBAN, etc.)
            case_sensitive = name in {"fin_code", "id_card", "iban_az", "real_parcel_id"}
            flags = 0 if case_sensitive else re.IGNORECASE
            self._compiled_patterns[name] = (re.compile(pattern, flags), replacement)
    
    def detect_pii(self, text: str) -> list[PIIDetection]:
        """Detect all PII instances in text without modifying it.
        
        Args:
            text: Input text to scan.
            
        Returns:
            List of PIIDetection objects with details about each detection.
        """
        detections: list[PIIDetection] = []
        
        for pii_type, (pattern, replacement) in self._compiled_patterns.items():
            for match in pattern.finditer(text):
                detections.append(PIIDetection(
                    pii_type=pii_type,
                    original=match.group(),
                    replacement=replacement,
                    start_pos=match.start(),
                    end_pos=match.end(),
                ))
        
        # Sort by position for consistent ordering
        detections.sort(key=lambda d: d.start_pos)
        return detections
    
    def strip_pii(self, text: str) -> PIIResult:
        """Detect and strip all PII from text.
        
        Args:
            text: Input text that may contain PII.
            
        Returns:
            PIIResult with cleaned text and detection metadata.
        """
        if not text:
            return PIIResult(
                cleaned_text="",
                has_pii=False,
                detection_count=0,
            )
        
        cleaned = text
        pii_types: set[str] = set()
        total_detections = 0
        
        # Apply patterns in order (more specific first)
        # Order matters: full names before surnames, specific phone before generic
        pattern_order = [
            "name_full", "phone_az_intl", "phone_az_local", "iban_az", 
            "id_card", "voen", "gps_coordinates", "real_parcel_id",
            "address_detailed", "email", "card_number",
            "phone_simple", "surname_only", "fin_code",
        ]
        
        for pii_type in pattern_order:
            if pii_type not in self._compiled_patterns:
                continue
            pattern, replacement = self._compiled_patterns[pii_type]
            
            # Count matches before replacing
            matches = pattern.findall(cleaned)
            if matches:
                total_detections += len(matches)
                pii_types.add(pii_type)
            
            # Replace all occurrences
            cleaned = pattern.sub(replacement, cleaned)
        
        return PIIResult(
            cleaned_text=cleaned,
            has_pii=total_detections > 0,
            detection_count=total_detections,
            pii_types_found=list(pii_types),
        )
    
    def has_pii(self, text: str) -> bool:
        """Quick check if text contains any PII.
        
        More efficient than strip_pii when you only need to know if PII exists.
        
        Args:
            text: Text to check.
            
        Returns:
            True if any PII pattern matches.
        """
        if not text:
            return False
            
        for pattern, _ in self._compiled_patterns.values():
            if pattern.search(text):
                return True
        return False
    
    def mask_for_logging(self, text: str, mask_char: str = "*") -> str:
        """Create a masked version suitable for logging.
        
        Keeps first and last characters of PII visible for debugging.
        
        Args:
            text: Original text.
            mask_char: Character to use for masking.
            
        Returns:
            Masked text safe for logging.
        """
        if not text:
            return ""
        
        result = text
        for pattern, _ in self._compiled_patterns.values():
            def mask_match(m: re.Match) -> str:
                original = m.group()
                if len(original) <= 4:
                    return mask_char * len(original)
                # Keep first and last char, mask middle
                return original[0] + mask_char * (len(original) - 2) + original[-1]
            
            result = pattern.sub(mask_match, result)
        
        return result


# Singleton instance for easy import
_gateway: Optional[PIIGateway] = None


def get_pii_gateway() -> PIIGateway:
    """Get singleton PII gateway instance."""
    global _gateway
    if _gateway is None:
        _gateway = PIIGateway()
    return _gateway


def strip_pii(text: str) -> PIIResult:
    """Convenience function to strip PII using default gateway."""
    return get_pii_gateway().strip_pii(text)


def has_pii(text: str) -> bool:
    """Convenience function to check for PII using default gateway."""
    return get_pii_gateway().has_pii(text)

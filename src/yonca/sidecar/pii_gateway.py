"""
Yonca AI - PII-Stripping Gateway
================================

Zero-Trust Data Sanitization Layer for Sidecar Intelligence.
Ensures ZERO access to real farmer PII while enabling AI recommendations.

Design Principles:
1. All incoming data is treated as potentially containing PII
2. Synthetic tokens replace any identifiable information
3. Reversible mapping for response personalization
4. Audit trail for compliance
"""

import hashlib
import re
import secrets
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional
from uuid import uuid4

from pydantic import BaseModel, Field


class PIIFieldType(str, Enum):
    """Types of PII that can be detected and stripped."""
    NAME = "name"
    PHONE = "phone"
    EMAIL = "email"
    ADDRESS = "address"
    NATIONAL_ID = "national_id"
    FARM_ID = "farm_id"
    COORDINATES = "coordinates"
    FINANCIAL = "financial"
    UNKNOWN = "unknown"


@dataclass
class PIIToken:
    """A token representing stripped PII with reversible mapping."""
    token_id: str
    field_type: PIIFieldType
    original_hash: str  # SHA-256 of original value (for audit, not reversal)
    synthetic_value: str  # The replacement value
    created_at: datetime = field(default_factory=datetime.now)
    
    def __post_init__(self):
        if not self.token_id:
            self.token_id = f"pii_{secrets.token_hex(8)}"


class SanitizedRequest(BaseModel):
    """A request with all PII stripped and replaced with synthetic tokens."""
    request_id: str = Field(default_factory=lambda: f"req_{uuid4().hex[:12]}")
    
    # Synthetic identifiers (no real data)
    synthetic_farm_id: str
    synthetic_farmer_id: str
    synthetic_region_code: str
    
    # Safe contextual data (non-identifying)
    farm_type: str
    crops: list[str] = Field(default_factory=list)
    livestock_types: list[str] = Field(default_factory=list)
    area_hectares: float
    
    # Anonymized environmental data
    soil_type: Optional[str] = None
    soil_moisture_percent: Optional[int] = None
    soil_nutrients: Optional[dict[str, float]] = None
    
    # Weather context (region-level, not GPS)
    climate_zone: str = "temperate"
    current_season: str = "spring"
    temperature_range: tuple[float, float] = (10.0, 25.0)
    precipitation_expected: bool = False
    
    # Query intent (in Azerbaijani or English)
    user_query: str = ""
    detected_intent: Optional[str] = None
    language: str = "az"
    
    # Timestamp (anonymized to day-level)
    request_date: str = Field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d"))
    
    # Token mapping reference (stored separately, never in response)
    _token_mapping_id: Optional[str] = None


class SanitizedResponse(BaseModel):
    """A response ready to be re-personalized through the gateway."""
    request_id: str
    
    # Recommendations (using synthetic IDs)
    recommendations: list[dict[str, Any]] = Field(default_factory=list)
    
    # Confidence and validation
    overall_confidence: float = Field(ge=0.0, le=1.0)
    rulebook_validation_score: float = Field(ge=0.0, le=1.0)
    validation_notes: list[str] = Field(default_factory=list)
    
    # Metadata
    inference_mode: str = "standard"  # standard, lite, offline
    processing_time_ms: int = 0
    model_version: str = "qwen2.5-7b"


class PIIGateway:
    """
    Zero-Trust PII Gateway for Sidecar Intelligence Architecture.
    
    Flow:
    1. INGEST: Raw request → PIIGateway.sanitize() → SanitizedRequest
    2. PROCESS: SanitizedRequest → RAG Engine → SanitizedResponse
    3. EGRESS: SanitizedResponse → PIIGateway.personalize() → Final Response
    
    The gateway NEVER stores or logs original PII values.
    Only SHA-256 hashes are retained for audit compliance.
    """
    
    # Azerbaijani name patterns
    AZ_NAME_PATTERNS = [
        r'\b[A-Z][a-zəöüçşğı]+\s+[A-Z][a-zəöüçşğı]+(?:\s+[A-Z][a-zəöüçşğı]+)?\b',  # Name Surname
        r'\b[A-Z][a-zəöüçşğı]+\s+oğlu\b',  # ... oğlu (son of)
        r'\b[A-Z][a-zəöüçşğı]+\s+qızı\b',  # ... qızı (daughter of)
    ]
    
    # Phone patterns (Azerbaijan)
    PHONE_PATTERNS = [
        r'\+994\s?\d{2}\s?\d{3}\s?\d{2}\s?\d{2}',
        r'0\d{2}[-\s]?\d{3}[-\s]?\d{2}[-\s]?\d{2}',
        r'\b\d{10,11}\b',
    ]
    
    # Email pattern
    EMAIL_PATTERN = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
    
    # GPS coordinates
    COORDS_PATTERN = r'\b\d{1,2}\.\d{4,},?\s*\d{1,3}\.\d{4,}\b'
    
    # Synthetic name components for replacement
    SYNTHETIC_NAMES = [
        "Fermer A", "Fermer B", "Fermer C", "Təsərrüfat 1", "Təsərrüfat 2",
        "Sahə Alpha", "Sahə Beta", "Region X", "Region Y"
    ]
    
    # Region code mapping (real region → anonymized code)
    REGION_CODES = {
        "Aran": "RGN-01",
        "Şəki-Zaqatala": "RGN-02", 
        "Lənkəran": "RGN-03",
        "Abşeron": "RGN-04",
        "Gəncə-Qazax": "RGN-05",
        "Mil-Muğan": "RGN-06",
        "Şirvan": "RGN-07",
        "Quba-Xaçmaz": "RGN-08",
    }
    
    def __init__(self, enable_audit_log: bool = True):
        """
        Initialize the PII Gateway.
        
        Args:
            enable_audit_log: If True, maintain hash-based audit trail
        """
        self.enable_audit_log = enable_audit_log
        self._token_store: dict[str, dict[str, PIIToken]] = {}  # request_id → field → token
        self._audit_log: list[dict] = []
    
    def _hash_value(self, value: str) -> str:
        """Create SHA-256 hash of a value for audit purposes."""
        return hashlib.sha256(value.encode('utf-8')).hexdigest()[:16]
    
    def _generate_synthetic_id(self, prefix: str = "syn") -> str:
        """Generate a synthetic identifier."""
        return f"{prefix}_{secrets.token_hex(6)}"
    
    def _detect_and_strip_pii(self, text: str, request_id: str) -> tuple[str, list[PIIToken]]:
        """
        Detect and strip PII from text, replacing with synthetic tokens.
        
        Returns:
            Tuple of (sanitized_text, list of PIITokens)
        """
        tokens: list[PIIToken] = []
        sanitized = text
        
        # Strip names
        for pattern in self.AZ_NAME_PATTERNS:
            matches = re.findall(pattern, text)
            for match in matches:
                synthetic = f"[ŞƏXS_{len(tokens)+1}]"
                token = PIIToken(
                    token_id=self._generate_synthetic_id("name"),
                    field_type=PIIFieldType.NAME,
                    original_hash=self._hash_value(match),
                    synthetic_value=synthetic
                )
                tokens.append(token)
                sanitized = sanitized.replace(match, synthetic)
        
        # Strip phone numbers
        for pattern in self.PHONE_PATTERNS:
            matches = re.findall(pattern, text)
            for match in matches:
                synthetic = "[TELEFON]"
                token = PIIToken(
                    token_id=self._generate_synthetic_id("phone"),
                    field_type=PIIFieldType.PHONE,
                    original_hash=self._hash_value(match),
                    synthetic_value=synthetic
                )
                tokens.append(token)
                sanitized = sanitized.replace(match, synthetic)
        
        # Strip emails
        matches = re.findall(self.EMAIL_PATTERN, text)
        for match in matches:
            synthetic = "[EMAİL]"
            token = PIIToken(
                token_id=self._generate_synthetic_id("email"),
                field_type=PIIFieldType.EMAIL,
                original_hash=self._hash_value(match),
                synthetic_value=synthetic
            )
            tokens.append(token)
            sanitized = sanitized.replace(match, synthetic)
        
        # Strip GPS coordinates
        matches = re.findall(self.COORDS_PATTERN, text)
        for match in matches:
            synthetic = "[KOORDİNAT]"
            token = PIIToken(
                token_id=self._generate_synthetic_id("coords"),
                field_type=PIIFieldType.COORDINATES,
                original_hash=self._hash_value(match),
                synthetic_value=synthetic
            )
            tokens.append(token)
            sanitized = sanitized.replace(match, synthetic)
        
        return sanitized, tokens
    
    def _anonymize_region(self, region: str) -> str:
        """Convert real region name to anonymized code."""
        return self.REGION_CODES.get(region, f"RGN-{self._hash_value(region)[:4].upper()}")
    
    def sanitize(
        self,
        farm_id: str,
        farmer_id: str,
        region: str,
        farm_type: str,
        crops: list[str],
        livestock_types: list[str],
        area_hectares: float,
        user_query: str,
        soil_data: Optional[dict] = None,
        weather_context: Optional[dict] = None,
        language: str = "az"
    ) -> SanitizedRequest:
        """
        Sanitize an incoming request, stripping all PII.
        
        This is the ONLY entry point for data into the Sidecar Intelligence.
        All identifiable information is replaced with synthetic tokens.
        
        Args:
            farm_id: Real farm identifier (will be anonymized)
            farmer_id: Real farmer identifier (will be anonymized)
            region: Real region name (will be coded)
            farm_type: Type of farm (safe - categorical)
            crops: List of crop types (safe - categorical)
            livestock_types: List of livestock types (safe - categorical)
            area_hectares: Farm area (safe - numerical, no location tie)
            user_query: User's question (will be scanned for PII)
            soil_data: Soil information (safe - environmental)
            weather_context: Weather info (safe - regional aggregate)
            language: Query language code
            
        Returns:
            SanitizedRequest with all PII stripped
        """
        request_id = f"req_{uuid4().hex[:12]}"
        
        # Generate synthetic identifiers
        synthetic_farm_id = self._generate_synthetic_id("farm")
        synthetic_farmer_id = self._generate_synthetic_id("farmer")
        synthetic_region = self._anonymize_region(region)
        
        # Store token mappings for this request
        self._token_store[request_id] = {
            "farm_id": PIIToken(
                token_id=synthetic_farm_id,
                field_type=PIIFieldType.FARM_ID,
                original_hash=self._hash_value(farm_id),
                synthetic_value=synthetic_farm_id
            ),
            "farmer_id": PIIToken(
                token_id=synthetic_farmer_id,
                field_type=PIIFieldType.FARM_ID,
                original_hash=self._hash_value(farmer_id),
                synthetic_value=synthetic_farmer_id
            ),
        }
        
        # Sanitize user query for any embedded PII
        sanitized_query, query_tokens = self._detect_and_strip_pii(user_query, request_id)
        
        # Add query tokens to store
        for i, token in enumerate(query_tokens):
            self._token_store[request_id][f"query_pii_{i}"] = token
        
        # Audit log entry (hashes only, no original values)
        if self.enable_audit_log:
            self._audit_log.append({
                "timestamp": datetime.now().isoformat(),
                "request_id": request_id,
                "pii_fields_detected": len(query_tokens) + 2,  # farm_id, farmer_id, plus query PII
                "field_types": [t.field_type.value for t in query_tokens],
            })
        
        # Build sanitized request
        request = SanitizedRequest(
            request_id=request_id,
            synthetic_farm_id=synthetic_farm_id,
            synthetic_farmer_id=synthetic_farmer_id,
            synthetic_region_code=synthetic_region,
            farm_type=farm_type,
            crops=crops,
            livestock_types=livestock_types,
            area_hectares=area_hectares,
            user_query=sanitized_query,
            language=language,
        )
        
        # Add soil data if provided
        if soil_data:
            request.soil_type = soil_data.get("soil_type")
            request.soil_moisture_percent = soil_data.get("moisture_percent")
            request.soil_nutrients = {
                "nitrogen": soil_data.get("nitrogen_level", 0),
                "phosphorus": soil_data.get("phosphorus_level", 0),
                "potassium": soil_data.get("potassium_level", 0),
            }
        
        # Add weather context if provided
        if weather_context:
            request.climate_zone = weather_context.get("climate_zone", "temperate")
            request.current_season = weather_context.get("season", "spring")
            request.temperature_range = (
                weather_context.get("temp_min", 10),
                weather_context.get("temp_max", 25)
            )
            request.precipitation_expected = weather_context.get("rain_expected", False)
        
        request._token_mapping_id = request_id
        
        return request
    
    def personalize(
        self,
        response: SanitizedResponse,
        original_farm_id: str,
        original_farmer_name: Optional[str] = None
    ) -> dict:
        """
        Re-personalize a sanitized response for delivery to farmer.
        
        This is the ONLY exit point for data from the Sidecar Intelligence.
        Synthetic tokens are replaced with appropriate identifiers.
        
        Note: Original PII is NOT stored in the gateway. The caller must
        provide the original identifiers for personalization.
        
        Args:
            response: The sanitized response from RAG engine
            original_farm_id: The real farm ID to use in response
            original_farmer_name: Optional farmer name for personalized greeting
            
        Returns:
            Personalized response dict ready for API delivery
        """
        personalized = {
            "farm_id": original_farm_id,
            "request_id": response.request_id,
            "recommendations": [],
            "confidence": response.overall_confidence,
            "accuracy_score": response.rulebook_validation_score,
            "validation_notes": response.validation_notes,
            "metadata": {
                "inference_mode": response.inference_mode,
                "processing_time_ms": response.processing_time_ms,
                "model": response.model_version,
            }
        }
        
        # Personalize recommendations
        for rec in response.recommendations:
            personalized_rec = rec.copy()
            # Replace any remaining synthetic tokens
            if original_farmer_name:
                for key in ["title", "title_az", "description", "description_az"]:
                    if key in personalized_rec and isinstance(personalized_rec[key], str):
                        personalized_rec[key] = personalized_rec[key].replace(
                            "[ŞƏXS_1]", original_farmer_name
                        )
            personalized["recommendations"].append(personalized_rec)
        
        return personalized
    
    def get_audit_summary(self) -> dict:
        """Get summary of PII detection audit log."""
        if not self._audit_log:
            return {"total_requests": 0, "pii_detections": 0}
        
        total_pii = sum(entry["pii_fields_detected"] for entry in self._audit_log)
        field_type_counts = {}
        for entry in self._audit_log:
            for ft in entry["field_types"]:
                field_type_counts[ft] = field_type_counts.get(ft, 0) + 1
        
        return {
            "total_requests": len(self._audit_log),
            "total_pii_fields_stripped": total_pii,
            "pii_types_detected": field_type_counts,
            "last_processed": self._audit_log[-1]["timestamp"] if self._audit_log else None,
        }
    
    def clear_token_store(self, request_id: Optional[str] = None):
        """
        Clear token mappings (for security/memory management).
        
        Args:
            request_id: If provided, only clear that request. Otherwise clear all.
        """
        if request_id:
            self._token_store.pop(request_id, None)
        else:
            self._token_store.clear()

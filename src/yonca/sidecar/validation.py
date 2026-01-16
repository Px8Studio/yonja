"""
Yonca AI - Agronomist-in-the-Loop Validation System
====================================================

Human Expert Validation Layer for AI-generated recommendations.
Ensures agricultural advice is verified before reaching farmers.

Design Principles:
1. AI can hallucinate - all high-stakes advice requires validation
2. Validation can be async (expert reviews later) or sync (pre-approved rules)
3. Farmers see validation status: ✓ Expert Verified, ⏳ Pending Review, ⚡ Rule-Based

Validation Tiers:
- Tier 1: Automatic (rule-based, pre-approved by agronomists)
- Tier 2: Async Review (AI-generated, queued for expert review)
- Tier 3: Sync Review (high-stakes, requires real-time expert approval)
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Optional
from uuid import uuid4

from pydantic import BaseModel, Field

from yonca.sidecar.rules_registry import get_pre_approved_rule_ids


class ValidationTier(str, Enum):
    """Validation tier levels for recommendations."""
    AUTOMATIC = "automatic"      # Pre-approved rule-based advice
    ASYNC_REVIEW = "async"       # Queued for expert review
    SYNC_REVIEW = "sync"         # Requires real-time approval
    REJECTED = "rejected"        # Rejected by expert


class ValidationStatus(str, Enum):
    """Current validation status of a recommendation."""
    VERIFIED = "verified"        # ✓ Expert or rule verified
    PENDING = "pending"          # ⏳ Awaiting expert review
    RULE_BASED = "rule_based"    # ⚡ Automatic rule-based
    FLAGGED = "flagged"          # ⚠ Needs urgent review
    REJECTED = "rejected"        # ✗ Expert rejected


class ExpertiseArea(str, Enum):
    """Areas of agronomist expertise."""
    IRRIGATION = "irrigation"
    SOIL_SCIENCE = "soil_science"
    PEST_MANAGEMENT = "pest_management"
    CROP_SCIENCE = "crop_science"
    LIVESTOCK = "livestock"
    ORGANIC_FARMING = "organic_farming"
    CLIMATE_ADAPTATION = "climate_adaptation"


@dataclass
class AgronomistProfile:
    """Profile of a validating agronomist."""
    id: str
    name: str
    expertise: list[ExpertiseArea]
    region_specialization: list[str]  # Azerbaijan regions
    certification: str
    years_experience: int
    validation_count: int = 0
    approval_rate: float = 0.95
    
    def can_validate(self, category: str, region: str) -> bool:
        """Check if agronomist can validate this type of recommendation."""
        # Map category to expertise
        expertise_map = {
            "irrigation": ExpertiseArea.IRRIGATION,
            "fertilization": ExpertiseArea.SOIL_SCIENCE,
            "pest_control": ExpertiseArea.PEST_MANAGEMENT,
            "disease_management": ExpertiseArea.PEST_MANAGEMENT,
            "harvest": ExpertiseArea.CROP_SCIENCE,
            "livestock": ExpertiseArea.LIVESTOCK,
            "soil_management": ExpertiseArea.SOIL_SCIENCE,
        }
        
        required_expertise = expertise_map.get(category)
        if required_expertise and required_expertise not in self.expertise:
            return False
        
        # Check region specialization (empty = all regions)
        if self.region_specialization and region not in self.region_specialization:
            return False
        
        return True


class ValidationDecision(BaseModel):
    """An expert's validation decision."""
    decision_id: str = Field(default_factory=lambda: f"vd_{uuid4().hex[:8]}")
    recommendation_id: str
    agronomist_id: str
    status: ValidationStatus
    
    # Decision details
    is_approved: bool
    confidence_adjustment: float = Field(default=0.0, ge=-0.5, le=0.5)
    
    # Expert notes
    expert_notes: str = ""
    expert_notes_az: str = ""
    suggested_modification: Optional[str] = None
    
    # Metadata
    decision_timestamp: datetime = Field(default_factory=datetime.now)
    review_duration_seconds: int = 0


class ValidationQueueItem(BaseModel):
    """An item in the validation queue."""
    queue_id: str = Field(default_factory=lambda: f"vq_{uuid4().hex[:8]}")
    recommendation_id: str
    farm_id: str
    region: str
    category: str
    
    # The recommendation content
    recommendation_title: str
    recommendation_description: str
    confidence_score: float
    
    # Queue metadata
    tier: ValidationTier
    priority: int = Field(default=5, ge=1, le=10)  # 1=lowest, 10=highest
    
    # Timing
    queued_at: datetime = Field(default_factory=datetime.now)
    expires_at: Optional[datetime] = None
    assigned_to: Optional[str] = None  # Agronomist ID
    
    # Context for expert
    farm_context: dict = Field(default_factory=dict)
    triggered_rules: list[str] = Field(default_factory=list)
    ai_reasoning: str = ""


class ValidationResult(BaseModel):
    """Result of validation process."""
    recommendation_id: str
    status: ValidationStatus
    tier: ValidationTier
    
    # Validation details
    is_validated: bool
    validated_by: str  # "rule:AZ-IRR-001" or "expert:agr_001"
    validation_timestamp: datetime
    
    # Confidence after validation
    original_confidence: float
    validated_confidence: float
    
    # Expert feedback (if any)
    expert_notes: Optional[str] = None
    expert_notes_az: Optional[str] = None
    
    # Display badge
    badge: str  # "✓ Expert Verified", "⚡ Rule-Based", "⏳ Pending"
    badge_az: str


# Pre-registered synthetic agronomist profiles (for demo)
DEMO_AGRONOMISTS = [
    AgronomistProfile(
        id="agr_001",
        name="Dr. Elçin Məmmədov",
        expertise=[ExpertiseArea.IRRIGATION, ExpertiseArea.SOIL_SCIENCE],
        region_specialization=["Aran", "Mil-Muğan", "Şirvan"],
        certification="Azərbaycan Kənd Təsərrüfatı Akademiyası",
        years_experience=15,
    ),
    AgronomistProfile(
        id="agr_002",
        name="Prof. Aynur Həsənova",
        expertise=[ExpertiseArea.CROP_SCIENCE, ExpertiseArea.PEST_MANAGEMENT],
        region_specialization=["Şəki-Zaqatala", "Quba-Xaçmaz"],
        certification="Moskva Kənd Təsərrüfatı Universiteti",
        years_experience=22,
    ),
    AgronomistProfile(
        id="agr_003",
        name="Fərid Əliyev",
        expertise=[ExpertiseArea.LIVESTOCK, ExpertiseArea.ORGANIC_FARMING],
        region_specialization=[],  # All regions
        certification="Gəncə Aqrar Universiteti",
        years_experience=10,
    ),
]


class AgronomistInTheLoopValidator:
    """
    Agronomist-in-the-Loop Validation System.
    
    Ensures AI recommendations are validated before reaching farmers.
    Supports three validation tiers:
    
    Tier 1 (Automatic): Rule-based recommendations that match pre-approved
                        patterns. Instant validation, no expert needed.
    
    Tier 2 (Async):     AI-generated recommendations queued for expert review.
                        Farmer receives advice with "⏳ Pending Review" badge.
    
    Tier 3 (Sync):      High-stakes recommendations (e.g., pesticide use)
                        that require real-time expert approval before delivery.
    """
    
    # Categories that require sync (real-time) expert validation
    SYNC_REQUIRED_CATEGORIES = ["pesticide", "chemical", "emergency"]
    
    # High-confidence threshold for automatic approval
    AUTO_APPROVE_THRESHOLD = 0.90
    
    # Categories that can be auto-approved if rule-based
    AUTO_APPROVE_CATEGORIES = ["irrigation", "fertilization", "harvest"]
    
    def __init__(self, agronomists: list[AgronomistProfile] = None):
        """
        Initialize the validator.
        
        Args:
            agronomists: List of registered agronomist profiles
        """
        self.agronomists = {a.id: a for a in (agronomists or DEMO_AGRONOMISTS)}
        self._validation_queue: list[ValidationQueueItem] = []
        self._validation_history: list[ValidationDecision] = []
        self._pre_approved_rules: set[str] = self._load_pre_approved_rules()
    
    def _load_pre_approved_rules(self) -> set[str]:
        """
        Load rule IDs that are pre-approved by agronomists.
        
        Now uses the centralized RulesRegistry which marks rules with
        `is_pre_approved=True` based on expert review.
        """
        return get_pre_approved_rule_ids()
    
    def determine_validation_tier(
        self,
        recommendation: dict,
        source: str,
        confidence: float
    ) -> ValidationTier:
        """
        Determine which validation tier applies to a recommendation.
        
        Args:
            recommendation: The recommendation dict
            source: Source of recommendation ("rulebook", "llm", "hybrid")
            confidence: Confidence score
            
        Returns:
            Appropriate ValidationTier
        """
        rec_type = recommendation.get("type", "").lower()
        rule_id = recommendation.get("rule_id")
        
        # Tier 3: Sync required for high-stakes categories
        if any(cat in rec_type for cat in self.SYNC_REQUIRED_CATEGORIES):
            return ValidationTier.SYNC_REVIEW
        
        # Tier 1: Automatic if from pre-approved rule with high confidence
        if (
            source == "rulebook" and
            rule_id in self._pre_approved_rules and
            confidence >= self.AUTO_APPROVE_THRESHOLD
        ):
            return ValidationTier.AUTOMATIC
        
        # Tier 1: Automatic if rule-based and category allows
        if (
            source == "rulebook" and
            rec_type in self.AUTO_APPROVE_CATEGORIES and
            confidence >= 0.85
        ):
            return ValidationTier.AUTOMATIC
        
        # Tier 2: Async review for everything else
        return ValidationTier.ASYNC_REVIEW
    
    def validate(
        self,
        recommendation: dict,
        farm_context: dict,
        source: str = "hybrid"
    ) -> ValidationResult:
        """
        Validate a recommendation through the appropriate tier.
        
        Args:
            recommendation: The recommendation to validate
            farm_context: Context about the farm for expert review
            source: Source of recommendation
            
        Returns:
            ValidationResult with status and badges
        """
        rec_id = recommendation.get("id", f"rec_{uuid4().hex[:8]}")
        confidence = recommendation.get("confidence", 0.5)
        rule_id = recommendation.get("rule_id")
        rec_type = recommendation.get("type", "general")
        
        # Determine tier
        tier = self.determine_validation_tier(recommendation, source, confidence)
        
        # Process based on tier
        if tier == ValidationTier.AUTOMATIC:
            return self._auto_validate(rec_id, confidence, rule_id)
        
        elif tier == ValidationTier.ASYNC_REVIEW:
            return self._queue_for_review(
                recommendation, farm_context, confidence
            )
        
        else:  # SYNC_REVIEW
            return self._require_sync_approval(
                recommendation, farm_context, confidence
            )
    
    def _auto_validate(
        self,
        rec_id: str,
        confidence: float,
        rule_id: Optional[str]
    ) -> ValidationResult:
        """Automatic validation for pre-approved rules."""
        return ValidationResult(
            recommendation_id=rec_id,
            status=ValidationStatus.RULE_BASED,
            tier=ValidationTier.AUTOMATIC,
            is_validated=True,
            validated_by=f"rule:{rule_id}" if rule_id else "auto:high_confidence",
            validation_timestamp=datetime.now(),
            original_confidence=confidence,
            validated_confidence=confidence,  # No change for rule-based
            badge="⚡ Rule-Based",
            badge_az="⚡ Qayda Əsaslı",
        )
    
    def _queue_for_review(
        self,
        recommendation: dict,
        farm_context: dict,
        confidence: float
    ) -> ValidationResult:
        """Queue recommendation for async expert review."""
        rec_id = recommendation.get("id")
        
        # Create queue item
        queue_item = ValidationQueueItem(
            recommendation_id=rec_id,
            farm_id=farm_context.get("farm_id", "unknown"),
            region=farm_context.get("region", "unknown"),
            category=recommendation.get("type", "general"),
            recommendation_title=recommendation.get("title", ""),
            recommendation_description=recommendation.get("description", ""),
            confidence_score=confidence,
            tier=ValidationTier.ASYNC_REVIEW,
            priority=self._calculate_priority(recommendation, confidence),
            expires_at=datetime.now() + timedelta(hours=24),
            farm_context=farm_context,
            triggered_rules=recommendation.get("triggered_rules", []),
            ai_reasoning=recommendation.get("reasoning", ""),
        )
        
        # Add to queue
        self._validation_queue.append(queue_item)
        
        # Assign to available expert
        self._assign_to_expert(queue_item)
        
        return ValidationResult(
            recommendation_id=rec_id,
            status=ValidationStatus.PENDING,
            tier=ValidationTier.ASYNC_REVIEW,
            is_validated=False,  # Not yet validated
            validated_by="pending:expert_review",
            validation_timestamp=datetime.now(),
            original_confidence=confidence,
            validated_confidence=confidence * 0.9,  # Slight penalty for pending
            badge="⏳ Pending Review",
            badge_az="⏳ Yoxlama Gözlənilir",
        )
    
    def _require_sync_approval(
        self,
        recommendation: dict,
        farm_context: dict,
        confidence: float
    ) -> ValidationResult:
        """Require synchronous expert approval (blocks until approved)."""
        rec_id = recommendation.get("id")
        
        # In production, this would wait for real-time expert input
        # For demo, we simulate a conservative rejection for safety
        
        return ValidationResult(
            recommendation_id=rec_id,
            status=ValidationStatus.FLAGGED,
            tier=ValidationTier.SYNC_REVIEW,
            is_validated=False,
            validated_by="sync:requires_approval",
            validation_timestamp=datetime.now(),
            original_confidence=confidence,
            validated_confidence=0.0,  # Cannot deliver without approval
            expert_notes="High-stakes recommendation requires expert approval before delivery.",
            expert_notes_az="Yüksək riskli tövsiyə çatdırılmadan əvvəl ekspert təsdiqi tələb edir.",
            badge="🔒 Requires Approval",
            badge_az="🔒 Təsdiq Tələb Olunur",
        )
    
    def _calculate_priority(self, recommendation: dict, confidence: float) -> int:
        """Calculate review priority (1-10)."""
        priority = 5  # Base priority
        
        # Higher priority for lower confidence
        if confidence < 0.6:
            priority += 2
        elif confidence < 0.75:
            priority += 1
        
        # Higher priority for critical categories
        rec_type = recommendation.get("type", "")
        if "emergency" in rec_type or "critical" in rec_type:
            priority += 3
        
        return min(10, priority)
    
    def _assign_to_expert(self, queue_item: ValidationQueueItem):
        """Assign a queue item to an available expert."""
        for agr_id, agronomist in self.agronomists.items():
            if agronomist.can_validate(queue_item.category, queue_item.region):
                queue_item.assigned_to = agr_id
                break
    
    def expert_review(
        self,
        queue_id: str,
        agronomist_id: str,
        is_approved: bool,
        notes: str = "",
        notes_az: str = "",
        confidence_adjustment: float = 0.0
    ) -> ValidationDecision:
        """
        Record an expert's review decision.
        
        Args:
            queue_id: ID of the queue item
            agronomist_id: ID of the reviewing agronomist
            is_approved: Whether the recommendation is approved
            notes: Expert notes in English
            notes_az: Expert notes in Azerbaijani
            confidence_adjustment: Adjustment to confidence (-0.5 to +0.5)
            
        Returns:
            ValidationDecision record
        """
        # Find queue item
        queue_item = next(
            (q for q in self._validation_queue if q.queue_id == queue_id),
            None
        )
        
        if not queue_item:
            raise ValueError(f"Queue item not found: {queue_id}")
        
        # Verify agronomist can validate this
        agronomist = self.agronomists.get(agronomist_id)
        if not agronomist:
            raise ValueError(f"Agronomist not found: {agronomist_id}")
        
        # Create decision
        decision = ValidationDecision(
            recommendation_id=queue_item.recommendation_id,
            agronomist_id=agronomist_id,
            status=ValidationStatus.VERIFIED if is_approved else ValidationStatus.REJECTED,
            is_approved=is_approved,
            confidence_adjustment=confidence_adjustment,
            expert_notes=notes,
            expert_notes_az=notes_az,
        )
        
        # Record decision
        self._validation_history.append(decision)
        
        # Remove from queue
        self._validation_queue = [
            q for q in self._validation_queue if q.queue_id != queue_id
        ]
        
        # Update agronomist stats
        agronomist.validation_count += 1
        
        return decision
    
    def get_queue_summary(self) -> dict:
        """Get summary of current validation queue."""
        return {
            "total_pending": len(self._validation_queue),
            "by_tier": {
                "async": len([q for q in self._validation_queue if q.tier == ValidationTier.ASYNC_REVIEW]),
                "sync": len([q for q in self._validation_queue if q.tier == ValidationTier.SYNC_REVIEW]),
            },
            "by_category": self._count_by_field("category"),
            "by_region": self._count_by_field("region"),
            "oldest_item": min(
                (q.queued_at for q in self._validation_queue),
                default=None
            ),
        }
    
    def _count_by_field(self, field: str) -> dict:
        """Count queue items by a field."""
        counts = {}
        for item in self._validation_queue:
            value = getattr(item, field, "unknown")
            counts[value] = counts.get(value, 0) + 1
        return counts
    
    def get_agronomist_stats(self, agronomist_id: str) -> dict:
        """Get validation statistics for an agronomist."""
        agronomist = self.agronomists.get(agronomist_id)
        if not agronomist:
            return {}
        
        decisions = [
            d for d in self._validation_history
            if d.agronomist_id == agronomist_id
        ]
        
        approved = len([d for d in decisions if d.is_approved])
        
        return {
            "agronomist": agronomist.name,
            "expertise": [e.value for e in agronomist.expertise],
            "total_validations": len(decisions),
            "approved": approved,
            "rejected": len(decisions) - approved,
            "approval_rate": approved / len(decisions) if decisions else 0,
            "avg_confidence_adjustment": (
                sum(d.confidence_adjustment for d in decisions) / len(decisions)
                if decisions else 0
            ),
        }

"""
Yonca AI - Temporal State Management
====================================

Farm timeline memory for contextual recommendations.
"Agriculture is not a static chat; it is a timeline."

This module maintains temporal context for farming activities:
- Tracks past actions (fertilization, irrigation, spraying)
- Remembers seasonal patterns
- Provides context-aware recommendations
- Enables "memory" features ("I fertilized 3 days ago")
"""

import hashlib
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Optional


class ActionType(str, Enum):
    """Types of farming actions tracked."""
    IRRIGATION = "irrigation"
    FERTILIZATION = "fertilization"
    PESTICIDE = "pesticide"
    PLANTING = "planting"
    HARVEST = "harvest"
    SOIL_TEST = "soil_test"
    PRUNING = "pruning"
    OBSERVATION = "observation"
    WEATHER_EVENT = "weather_event"
    LIVESTOCK_FEEDING = "livestock_feeding"
    VETERINARY = "veterinary"


class SeasonPhase(str, Enum):
    """Agricultural season phases in Azerbaijan."""
    EARLY_SPRING = "early_spring"      # February-March
    LATE_SPRING = "late_spring"        # April-May
    EARLY_SUMMER = "early_summer"      # June-July
    LATE_SUMMER = "late_summer"        # August-September
    EARLY_AUTUMN = "early_autumn"      # October-November
    LATE_AUTUMN = "late_autumn"        # November-December
    WINTER = "winter"                  # December-February


@dataclass
class FarmAction:
    """Record of a single farm action."""
    action_id: str
    action_type: ActionType
    timestamp: datetime
    crop_or_field: str
    details: dict = field(default_factory=dict)
    location: Optional[str] = None
    quantity: Optional[float] = None
    unit: Optional[str] = None
    notes: Optional[str] = None
    
    def days_ago(self) -> int:
        """Calculate how many days ago this action occurred."""
        delta = datetime.now() - self.timestamp
        return delta.days
    
    def to_context_string(self, language: str = "az") -> str:
        """Convert to a human-readable context string."""
        days = self.days_ago()
        
        action_labels_az = {
            ActionType.IRRIGATION: "suvarma",
            ActionType.FERTILIZATION: "gübrələmə",
            ActionType.PESTICIDE: "pestisid çiləmə",
            ActionType.PLANTING: "əkin",
            ActionType.HARVEST: "məhsul yığımı",
            ActionType.SOIL_TEST: "torpaq analizi",
            ActionType.PRUNING: "budama",
            ActionType.OBSERVATION: "müşahidə",
            ActionType.WEATHER_EVENT: "hava hadisəsi",
            ActionType.LIVESTOCK_FEEDING: "yemləmə",
            ActionType.VETERINARY: "baytarlıq",
        }
        
        action_labels_en = {
            ActionType.IRRIGATION: "irrigation",
            ActionType.FERTILIZATION: "fertilization",
            ActionType.PESTICIDE: "pesticide application",
            ActionType.PLANTING: "planting",
            ActionType.HARVEST: "harvest",
            ActionType.SOIL_TEST: "soil test",
            ActionType.PRUNING: "pruning",
            ActionType.OBSERVATION: "observation",
            ActionType.WEATHER_EVENT: "weather event",
            ActionType.LIVESTOCK_FEEDING: "feeding",
            ActionType.VETERINARY: "veterinary care",
        }
        
        if language == "az":
            label = action_labels_az.get(self.action_type, str(self.action_type))
            if days == 0:
                return f"Bu gün {self.crop_or_field} üçün {label}"
            elif days == 1:
                return f"Dünən {self.crop_or_field} üçün {label}"
            else:
                return f"{days} gün əvvəl {self.crop_or_field} üçün {label}"
        else:
            label = action_labels_en.get(self.action_type, str(self.action_type))
            if days == 0:
                return f"Today: {label} for {self.crop_or_field}"
            elif days == 1:
                return f"Yesterday: {label} for {self.crop_or_field}"
            else:
                return f"{days} days ago: {label} for {self.crop_or_field}"


@dataclass
class CropGrowthStage:
    """Current growth stage of a crop."""
    crop_name: str
    stage: str                    # e.g., "germination", "vegetative", "flowering"
    stage_start_date: datetime
    expected_harvest_date: Optional[datetime] = None
    days_in_stage: int = 0
    health_status: str = "healthy"
    notes: Optional[str] = None


@dataclass
class TemporalContext:
    """
    Full temporal context for a farm session.
    
    This is the "memory" that the AI uses to provide
    contextually aware recommendations.
    """
    session_id: str
    farmer_id_hash: str              # Anonymized farmer ID
    region: str
    current_season: SeasonPhase
    recent_actions: list[FarmAction] = field(default_factory=list)
    crop_stages: list[CropGrowthStage] = field(default_factory=list)
    last_interaction: Optional[datetime] = None
    pending_actions: list[dict] = field(default_factory=list)
    
    def get_relevant_context(
        self,
        action_type: Optional[ActionType] = None,
        crop: Optional[str] = None,
        days_lookback: int = 30
    ) -> list[FarmAction]:
        """
        Get relevant past actions for context.
        
        Args:
            action_type: Filter by action type
            crop: Filter by crop/field
            days_lookback: How far back to look
            
        Returns:
            List of relevant past actions
        """
        cutoff = datetime.now() - timedelta(days=days_lookback)
        
        relevant = [
            a for a in self.recent_actions
            if a.timestamp >= cutoff
        ]
        
        if action_type:
            relevant = [a for a in relevant if a.action_type == action_type]
        
        if crop:
            relevant = [
                a for a in relevant
                if crop.lower() in a.crop_or_field.lower()
            ]
        
        return sorted(relevant, key=lambda x: x.timestamp, reverse=True)
    
    def get_context_summary(self, language: str = "az") -> str:
        """Generate a summary of recent farm activity."""
        if not self.recent_actions:
            if language == "az":
                return "Əvvəlki fəaliyyət qeyd edilməyib."
            return "No previous activity recorded."
        
        summaries = []
        for action in self.recent_actions[:5]:  # Last 5 actions
            summaries.append(action.to_context_string(language))
        
        if language == "az":
            header = "Son fəaliyyətlər:"
        else:
            header = "Recent activities:"
        
        return f"{header}\n" + "\n".join(f"• {s}" for s in summaries)


class TemporalStateManager:
    """
    Manages temporal state for farm sessions.
    
    This is the "brain" that maintains context across
    conversations and provides timeline-aware features.
    """
    
    # Recommended intervals between actions (in days)
    ACTION_INTERVALS = {
        ActionType.IRRIGATION: {
            "buğda": 7,      # wheat
            "pomidor": 3,   # tomato
            "pambıq": 5,    # cotton
            "üzüm": 10,     # grape
            "default": 5,
        },
        ActionType.FERTILIZATION: {
            "buğda": 30,
            "pomidor": 14,
            "pambıq": 21,
            "default": 21,
        },
        ActionType.PESTICIDE: {
            "default": 14,  # Minimum 2 weeks between applications
        },
    }
    
    def __init__(self):
        """Initialize the temporal state manager."""
        # In-memory session storage (would be Redis/DB in production)
        self._sessions: dict[str, TemporalContext] = {}
    
    def _hash_id(self, farmer_id: str) -> str:
        """Create anonymized hash of farmer ID."""
        return hashlib.sha256(farmer_id.encode()).hexdigest()[:16]
    
    def _get_current_season(self) -> SeasonPhase:
        """Determine current agricultural season in Azerbaijan."""
        month = datetime.now().month
        
        if month in (2, 3):
            return SeasonPhase.EARLY_SPRING
        elif month in (4, 5):
            return SeasonPhase.LATE_SPRING
        elif month in (6, 7):
            return SeasonPhase.EARLY_SUMMER
        elif month in (8, 9):
            return SeasonPhase.LATE_SUMMER
        elif month == 10 or (month == 11 and datetime.now().day <= 15):
            return SeasonPhase.EARLY_AUTUMN
        elif month == 11 or (month == 12 and datetime.now().day <= 15):
            return SeasonPhase.LATE_AUTUMN
        else:
            return SeasonPhase.WINTER
    
    def get_or_create_context(
        self,
        session_id: str,
        farmer_id: str,
        region: str = "Aran"
    ) -> TemporalContext:
        """
        Get existing context or create new one.
        
        Args:
            session_id: Unique session identifier
            farmer_id: Farmer identifier (will be hashed)
            region: Farm region
            
        Returns:
            TemporalContext for the session
        """
        if session_id in self._sessions:
            context = self._sessions[session_id]
            context.last_interaction = datetime.now()
            return context
        
        context = TemporalContext(
            session_id=session_id,
            farmer_id_hash=self._hash_id(farmer_id),
            region=region,
            current_season=self._get_current_season(),
            last_interaction=datetime.now(),
        )
        
        self._sessions[session_id] = context
        return context
    
    def record_action(
        self,
        context: TemporalContext,
        action_type: ActionType,
        crop_or_field: str,
        details: Optional[dict] = None,
        timestamp: Optional[datetime] = None,
        quantity: Optional[float] = None,
        unit: Optional[str] = None,
        notes: Optional[str] = None
    ) -> FarmAction:
        """
        Record a farming action in the timeline.
        
        Args:
            context: The temporal context
            action_type: Type of action
            crop_or_field: Crop or field identifier
            details: Additional details
            timestamp: When action occurred (defaults to now)
            quantity: Amount/quantity
            unit: Unit of measurement
            notes: Free-text notes
            
        Returns:
            The recorded FarmAction
        """
        action_id = f"{context.session_id}_{len(context.recent_actions)}_{datetime.now().timestamp()}"
        
        action = FarmAction(
            action_id=action_id,
            action_type=action_type,
            timestamp=timestamp or datetime.now(),
            crop_or_field=crop_or_field,
            details=details or {},
            quantity=quantity,
            unit=unit,
            notes=notes,
        )
        
        context.recent_actions.append(action)
        context.last_interaction = datetime.now()
        
        return action
    
    def check_action_timing(
        self,
        context: TemporalContext,
        proposed_action: ActionType,
        crop: str
    ) -> dict:
        """
        Check if a proposed action is well-timed.
        
        Args:
            context: The temporal context
            proposed_action: Action being considered
            crop: Crop/field for the action
            
        Returns:
            Dict with timing advice and warnings
        """
        result = {
            "can_proceed": True,
            "warning": None,
            "days_since_last": None,
            "recommended_wait": None,
            "context_advice": None,
        }
        
        # Get last similar action
        last_actions = context.get_relevant_context(
            action_type=proposed_action,
            crop=crop,
            days_lookback=60
        )
        
        if last_actions:
            last_action = last_actions[0]
            days_since = last_action.days_ago()
            result["days_since_last"] = days_since
            
            # Get recommended interval
            intervals = self.ACTION_INTERVALS.get(proposed_action, {})
            recommended = intervals.get(
                crop.lower(),
                intervals.get("default", 7)
            )
            result["recommended_wait"] = recommended
            
            if days_since < recommended:
                result["can_proceed"] = False
                result["warning"] = self._generate_timing_warning(
                    proposed_action, crop, days_since, recommended
                )
        
        # Add seasonal context
        result["context_advice"] = self._get_seasonal_advice(
            context.current_season, proposed_action
        )
        
        return result
    
    def _generate_timing_warning(
        self,
        action: ActionType,
        crop: str,
        days_since: int,
        recommended: int
    ) -> str:
        """Generate a warning message for too-frequent actions."""
        wait_more = recommended - days_since
        
        warnings = {
            ActionType.IRRIGATION: f"⚠️ Diqqət: {crop} üçün son suvarma {days_since} gün əvvəl edilib. Növbəti suvarma üçün daha {wait_more} gün gözləmək tövsiyə olunur.",
            ActionType.FERTILIZATION: f"⚠️ Diqqət: {crop} artıq {days_since} gün əvvəl gübrələnib. Həddindən artıq gübrə bitkilərə zərər verə bilər. Daha {wait_more} gün gözləyin.",
            ActionType.PESTICIDE: f"⚠️ Diqqət: Son pestisid çiləməsi {days_since} gün əvvəl olub. Təkrar çiləmə üçün minimum {wait_more} gün gözləmək lazımdır.",
        }
        
        return warnings.get(
            action,
            f"⚠️ Bu əməliyyat {days_since} gün əvvəl edilib. Daha {wait_more} gün gözləmək tövsiyə olunur."
        )
    
    def _get_seasonal_advice(
        self,
        season: SeasonPhase,
        action: ActionType
    ) -> str:
        """Get seasonal context for an action."""
        seasonal_tips = {
            SeasonPhase.EARLY_SPRING: {
                ActionType.FERTILIZATION: "🌱 Erkən yaz gübrələmə üçün optimal vaxtdır. Azotlu gübrələrə üstünlük verin.",
                ActionType.PLANTING: "🌱 Yazlıq bitkilərin səpin vaxtı başlayır.",
                ActionType.IRRIGATION: "🌱 Torpaq nəmliyi yüksəkdir, suvarma tezliyini azaldın.",
            },
            SeasonPhase.LATE_SPRING: {
                ActionType.PESTICIDE: "🐛 Zərərvericilərin aktivləşmə dövrüdür. Profilaktik tədbirlər görün.",
                ActionType.IRRIGATION: "☀️ Temperatur artır, suvarma tezliyini artırın.",
            },
            SeasonPhase.EARLY_SUMMER: {
                ActionType.IRRIGATION: "☀️ Qızmar yay dövrü. Səhər tezdən və ya axşam suvarmaq tövsiyə olunur.",
                ActionType.PESTICIDE: "🐛 Həşərat aktivliyi maksimum səviyyədədir.",
            },
            SeasonPhase.LATE_SUMMER: {
                ActionType.HARVEST: "🌾 Məhsul yığımı dövrü. Optimal vaxtı gecikdirməyin.",
                ActionType.FERTILIZATION: "⚠️ Yay gübrələməsi ehtiyatla aparılmalıdır.",
            },
            SeasonPhase.EARLY_AUTUMN: {
                ActionType.PLANTING: "🌾 Payızlıq bitkilərin səpin vaxtı.",
                ActionType.SOIL_TEST: "🧪 Torpaq analizi üçün optimal vaxt.",
            },
            SeasonPhase.WINTER: {
                ActionType.IRRIGATION: "❄️ Qış dövrü suvarma minimuma endirilməlidir.",
                ActionType.PRUNING: "✂️ Meyvə ağaclarının budama dövrü.",
            },
        }
        
        season_tips = seasonal_tips.get(season, {})
        return season_tips.get(action, "")
    
    def get_pending_reminders(
        self,
        context: TemporalContext
    ) -> list[dict]:
        """
        Get pending action reminders based on timeline.
        
        Returns:
            List of reminder dicts
        """
        reminders = []
        now = datetime.now()
        
        # Check for crops that might need attention
        for stage in context.crop_stages:
            if stage.expected_harvest_date:
                days_to_harvest = (stage.expected_harvest_date - now).days
                if 0 < days_to_harvest <= 7:
                    reminders.append({
                        "type": "harvest_approaching",
                        "crop": stage.crop_name,
                        "days_remaining": days_to_harvest,
                        "message_az": f"🌾 {stage.crop_name} məhsul yığımına {days_to_harvest} gün qalıb!",
                        "message_en": f"🌾 {stage.crop_name} harvest in {days_to_harvest} days!",
                    })
        
        # Check for overdue regular actions
        for action_type in [ActionType.IRRIGATION, ActionType.FERTILIZATION]:
            last_actions = context.get_relevant_context(
                action_type=action_type,
                days_lookback=30
            )
            
            if last_actions:
                last = last_actions[0]
                days_since = last.days_ago()
                crop = last.crop_or_field
                
                intervals = self.ACTION_INTERVALS.get(action_type, {})
                recommended = intervals.get(crop.lower(), intervals.get("default", 7))
                
                if days_since > recommended:
                    overdue_days = days_since - recommended
                    if action_type == ActionType.IRRIGATION:
                        reminders.append({
                            "type": "overdue_irrigation",
                            "crop": crop,
                            "days_overdue": overdue_days,
                            "message_az": f"💧 {crop} üçün suvarma {overdue_days} gün gecikib!",
                            "message_en": f"💧 {crop} irrigation is {overdue_days} days overdue!",
                        })
                    elif action_type == ActionType.FERTILIZATION:
                        reminders.append({
                            "type": "consider_fertilization",
                            "crop": crop,
                            "days_since": days_since,
                            "message_az": f"🌿 {crop} üçün gübrələmə vaxtı ola bilər (son: {days_since} gün əvvəl).",
                            "message_en": f"🌿 {crop} may need fertilization (last: {days_since} days ago).",
                        })
        
        return reminders
    
    def generate_context_prompt(
        self,
        context: TemporalContext,
        language: str = "az"
    ) -> str:
        """
        Generate a context prompt for the AI to use.
        
        This provides the temporal context that makes
        recommendations more relevant.
        """
        parts = []
        
        # Season context
        season_names = {
            SeasonPhase.EARLY_SPRING: "Erkən Yaz" if language == "az" else "Early Spring",
            SeasonPhase.LATE_SPRING: "Gec Yaz" if language == "az" else "Late Spring",
            SeasonPhase.EARLY_SUMMER: "Erkən Yay" if language == "az" else "Early Summer",
            SeasonPhase.LATE_SUMMER: "Gec Yay" if language == "az" else "Late Summer",
            SeasonPhase.EARLY_AUTUMN: "Erkən Payız" if language == "az" else "Early Autumn",
            SeasonPhase.LATE_AUTUMN: "Gec Payız" if language == "az" else "Late Autumn",
            SeasonPhase.WINTER: "Qış" if language == "az" else "Winter",
        }
        
        if language == "az":
            parts.append(f"📅 Mövsüm: {season_names[context.current_season]}")
            parts.append(f"📍 Bölgə: {context.region}")
        else:
            parts.append(f"📅 Season: {season_names[context.current_season]}")
            parts.append(f"📍 Region: {context.region}")
        
        # Recent activity summary
        activity_summary = context.get_context_summary(language)
        if activity_summary:
            parts.append("")
            parts.append(activity_summary)
        
        # Pending reminders
        reminders = self.get_pending_reminders(context)
        if reminders:
            parts.append("")
            if language == "az":
                parts.append("⏰ Xatırlatmalar:")
            else:
                parts.append("⏰ Reminders:")
            
            for r in reminders:
                msg_key = "message_az" if language == "az" else "message_en"
                parts.append(f"  • {r[msg_key]}")
        
        return "\n".join(parts)

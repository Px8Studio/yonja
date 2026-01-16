"""
Yonca AI - Digital Umbrella Mock Backend
========================================

FastAPI-structured mock API for the Sidecar Intelligence architecture.
Simulates the headless backend that the Streamlit frontend consumes.

This module mimics the real API structure but uses synthetic data only.
The frontend is just a consumer of this structured API.
"""

from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from enum import Enum
from typing import Any, Optional
from uuid import uuid4
import random

from yonca.umbrella.scenario_manager import (
    FarmProfile as ScenarioFarmProfile,
    ScenarioProfile,
    scenario_manager,
)


class RecommendationType(str, Enum):
    """Types of recommendations."""
    IRRIGATION = "irrigation"
    FERTILIZATION = "fertilization"
    PEST_CONTROL = "pest_control"
    LIVESTOCK_CARE = "livestock_care"
    HARVEST = "harvest"
    VENTILATION = "ventilation"
    VACCINATION = "vaccination"
    GENERAL = "general"


class RecommendationPriority(str, Enum):
    """Priority levels."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class FarmProfileRequest:
    """
    POST request body for /recommend endpoint.
    
    This mimics what the mobile app would send to the real API.
    """
    farm_id: str
    farm_type: str
    region: str
    area_hectares: float
    
    # Environmental context
    soil_moisture_percent: Optional[int] = None
    soil_nitrogen: Optional[float] = None
    temperature_current: Optional[float] = None
    temperature_max: Optional[float] = None
    humidity_percent: Optional[int] = None
    is_rain_expected: bool = False
    
    # Crop context (for crop farms)
    crops: list[str] = field(default_factory=list)
    crop_stages: list[str] = field(default_factory=list)
    
    # Livestock context (for animal farms)
    livestock_types: list[str] = field(default_factory=list)
    livestock_counts: list[int] = field(default_factory=list)
    barn_humidity: Optional[int] = None
    
    # Query
    user_query: str = ""
    language: str = "az"  # az, en, ru
    
    # Options
    max_recommendations: int = 5
    include_why_section: bool = True


@dataclass
class RecommendationItem:
    """A single recommendation in the payload."""
    id: str
    type: RecommendationType
    priority: RecommendationPriority
    confidence: float  # 0.0 - 1.0
    
    # Main content (Azerbaijani)
    title: str
    description: str
    action: str
    
    # Trust-building "Why?" section
    why_title: str
    why_explanation: str
    
    # Technical metadata
    rule_id: Optional[str] = None
    source: str = "hybrid"  # llm, rulebook, hybrid
    
    # Timing
    suggested_time: Optional[str] = None  # "06:00-08:00"
    deadline: Optional[date] = None
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON response."""
        return {
            "id": self.id,
            "type": self.type.value,
            "priority": self.priority.value,
            "confidence": self.confidence,
            "title": self.title,
            "description": self.description,
            "action": self.action,
            "why": {
                "title": self.why_title,
                "explanation": self.why_explanation,
            },
            "metadata": {
                "rule_id": self.rule_id,
                "source": self.source,
                "suggested_time": self.suggested_time,
                "deadline": self.deadline.isoformat() if self.deadline else None,
            },
        }


@dataclass
class DailyRoutineItem:
    """A single item in the daily routine timeline."""
    time_slot: str  # "06:00"
    duration_minutes: int
    title: str
    description: str
    icon: str
    category: str
    priority: RecommendationPriority
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "time_slot": self.time_slot,
            "duration_minutes": self.duration_minutes,
            "title": self.title,
            "description": self.description,
            "icon": self.icon,
            "category": self.category,
            "priority": self.priority.value,
        }


@dataclass
class RecommendationPayload:
    """
    Response payload from /recommend endpoint.
    
    This is the structured JSON response that the frontend consumes.
    """
    request_id: str
    farm_id: str
    generated_at: datetime
    
    # Main recommendations
    recommendations: list[RecommendationItem]
    
    # Daily routine (timeline)
    daily_routine: list[DailyRoutineItem]
    
    # Summary stats
    critical_count: int
    total_count: int
    
    # Status
    status: str = "success"
    inference_engine: str = "qwen2.5-7b-simulated"
    processing_time_ms: int = 0
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to JSON-serializable dictionary."""
        return {
            "request_id": self.request_id,
            "farm_id": self.farm_id,
            "generated_at": self.generated_at.isoformat(),
            "status": self.status,
            "inference_engine": self.inference_engine,
            "processing_time_ms": self.processing_time_ms,
            "summary": {
                "critical_count": self.critical_count,
                "total_count": self.total_count,
            },
            "recommendations": [r.to_dict() for r in self.recommendations],
            "daily_routine": [r.to_dict() for r in self.daily_routine],
        }


class MockBackend:
    """
    FastAPI-structured mock backend for the Sidecar Intelligence module.
    
    Simulates POST requests to /recommend endpoint.
    Uses Qwen2.5-7B as the simulated inference engine.
    
    Usage:
        backend = MockBackend()
        request = FarmProfileRequest(...)
        response = backend.recommend(request)
    """
    
    def __init__(self, logic_guard=None):
        """
        Initialize the mock backend.
        
        Args:
            logic_guard: Optional AgronomyLogicGuard for rule validation
        """
        self._logic_guard = logic_guard
        self._request_counter = 0
    
    def recommend(self, request: FarmProfileRequest) -> RecommendationPayload:
        """
        POST /recommend endpoint simulation.
        
        Processes a farm profile and returns AI-driven recommendations.
        """
        start_time = datetime.now()
        self._request_counter += 1
        
        request_id = f"req-{uuid4().hex[:12]}"
        
        # Generate recommendations based on farm type
        recommendations = self._generate_recommendations(request)
        
        # Apply logic guard if available
        if self._logic_guard:
            recommendations = self._logic_guard.validate_recommendations(
                recommendations, request
            )
        
        # Generate daily routine
        daily_routine = self._generate_daily_routine(request, recommendations)
        
        # Calculate stats
        critical_count = sum(
            1 for r in recommendations 
            if r.priority == RecommendationPriority.CRITICAL
        )
        
        processing_time = (datetime.now() - start_time).microseconds // 1000
        
        return RecommendationPayload(
            request_id=request_id,
            farm_id=request.farm_id,
            generated_at=datetime.now(),
            recommendations=recommendations,
            daily_routine=daily_routine,
            critical_count=critical_count,
            total_count=len(recommendations),
            processing_time_ms=processing_time + random.randint(50, 200),
        )
    
    def _generate_recommendations(
        self, 
        request: FarmProfileRequest
    ) -> list[RecommendationItem]:
        """Generate recommendations based on farm profile."""
        recommendations = []
        
        # Route to specific generators based on farm type
        if request.farm_type in ("wheat", "taxıl"):
            recommendations.extend(self._wheat_recommendations(request))
        elif request.farm_type in ("livestock", "heyvandarlıq"):
            recommendations.extend(self._livestock_recommendations(request))
        elif request.farm_type in ("orchard", "bağ"):
            recommendations.extend(self._orchard_recommendations(request))
        elif request.farm_type in ("mixed", "qarışıq"):
            recommendations.extend(self._mixed_recommendations(request))
        elif request.farm_type in ("poultry", "quşçuluq"):
            recommendations.extend(self._poultry_recommendations(request))
        
        # Sort by priority
        priority_order = {
            RecommendationPriority.CRITICAL: 0,
            RecommendationPriority.HIGH: 1,
            RecommendationPriority.MEDIUM: 2,
            RecommendationPriority.LOW: 3,
        }
        recommendations.sort(key=lambda r: (priority_order[r.priority], -r.confidence))
        
        return recommendations[:request.max_recommendations]
    
    def _wheat_recommendations(
        self, 
        request: FarmProfileRequest
    ) -> list[RecommendationItem]:
        """
        Generate recommendations for wheat/grain farm.
        
        Scenario logic:
        - Soil moisture 12% → urgent irrigation needed
        - Satellite yellowing → nitrogen deficiency
        """
        recs = []
        
        # CRITICAL: Low soil moisture
        if request.soil_moisture_percent is not None and request.soil_moisture_percent < 20:
            recs.append(RecommendationItem(
                id=f"rec-{uuid4().hex[:8]}",
                type=RecommendationType.IRRIGATION,
                priority=RecommendationPriority.CRITICAL,
                confidence=0.94,
                title="🚨 Təcili Suvarma Tələb Olunur",
                description=f"Torpaq nəmliyi {request.soil_moisture_percent}% - kritik səviyyədədir. Buğda çiçəkləmə mərhələsində su stresindən ciddi məhsuldarlıq itkisi ola bilər.",
                action="Bu gün saat 06:00-08:00 arasında suvarmanı başlayın. Hər hektara 40-50mm su verin.",
                why_title="Niyə bu tövsiyə?",
                why_explanation="Çiçəkləmə mərhələsində torpaq nəmliyi 30%-dən aşağı düşdükdə, buğda bitkisi reproduktiv strresə məruz qalır. Bu, sünbüldə dənə sayının 20-40% azalmasına səbəb ola bilər. Peyk şəkilləri cənub-şərq sahəsində stress əlamətləri göstərir.",
                rule_id="AZ-IRR-001",
                source="hybrid",
                suggested_time="06:00-08:00",
                deadline=date.today(),
            ))
        
        # HIGH: Nitrogen deficiency (yellowing)
        if request.soil_nitrogen is not None and request.soil_nitrogen < 25:
            recs.append(RecommendationItem(
                id=f"rec-{uuid4().hex[:8]}",
                type=RecommendationType.FERTILIZATION,
                priority=RecommendationPriority.HIGH,
                confidence=0.88,
                title="🌾 Azot Gübrəsi Tövsiyəsi",
                description=f"Azot səviyyəsi {request.soil_nitrogen} kq/ha - optimal həddən (30-40 kq/ha) aşağıdır. Peyk görüntülərində sarılma anomaliyası aşkarlanıb.",
                action="Ammonium nitrat (NH₄NO₃) gübrəsini 80-100 kq/ha dozasında tətbiq edin. Suvarma ilə birlikdə daha effektivdir.",
                why_title="Niyə azot gübrəsi?",
                why_explanation="Sarı yarpaqlaar azot çatışmazlığının klassik əlamətidir. Çiçəkləmə dövründə azot çatışmazlığı zülal sintezini azaldır və dən keyfiyyətinə mənfi təsir göstərir. NDVI indeksi 0.35 (normal: 0.5-0.7) cənub-şərq sahəsində stress göstərir.",
                rule_id="AZ-FERT-003",
                source="hybrid",
                suggested_time="suvarma ilə birlikdə",
                deadline=date.today() + timedelta(days=3),
            ))
        
        # MEDIUM: Heat protection
        if request.temperature_max and request.temperature_max > 30:
            recs.append(RecommendationItem(
                id=f"rec-{uuid4().hex[:8]}",
                type=RecommendationType.GENERAL,
                priority=RecommendationPriority.MEDIUM,
                confidence=0.82,
                title="☀️ İsti Hava Tədbirləri",
                description=f"Gözlənilən maksimum temperatur {request.temperature_max}°C. Buğda çiçəkləmə dövründə 32°C-dən yuxarı temperatur tozlanmanı azaldır.",
                action="Səhər tezdən (05:00-07:00) suvarma planlaşdırın. Günorta saatlarında sahədə iş aparmayın.",
                why_title="İstilik stresi nədir?",
                why_explanation="32°C-dən yuxarı temperaturda buğda çiçəyi steril ola bilər. Tozlanma uğursuzluğu boş sünbüllərə səbəb olur. Səhər suvarması torpağı sərinlədir və bitki stresini azaldır.",
                rule_id="AZ-HEAT-001",
                source="rulebook",
            ))
        
        return recs
    
    def _livestock_recommendations(
        self, 
        request: FarmProfileRequest
    ) -> list[RecommendationItem]:
        """
        Generate recommendations for livestock farm.
        
        Scenario logic:
        - High humidity + high temp → heat stress + ventilation check
        - List respiratory disease symptoms
        """
        recs = []
        
        # CRITICAL: Heat stress risk
        barn_humidity = request.barn_humidity or request.humidity_percent or 75
        if barn_humidity > 70 and request.temperature_max and request.temperature_max > 32:
            recs.append(RecommendationItem(
                id=f"rec-{uuid4().hex[:8]}",
                type=RecommendationType.VENTILATION,
                priority=RecommendationPriority.CRITICAL,
                confidence=0.92,
                title="🌡️ Təcili Ventilyasiya Yoxlaması",
                description=f"Tövlədə yüksək rütubət ({barn_humidity}%) + yüksək temperatur ({request.temperature_max}°C) = istilik stresi riski. Mal-qara üçün kritik şərait.",
                action="1. Ventilyatorları maksimum gücə keçirin\n2. Tövlə qapılarını açın\n3. Əlavə su mənbələri qoyun\n4. Günorta yemlənməni təxirə salın",
                why_title="İstilik stresi nədir?",
                why_explanation="THI (Temperature-Humidity Index) 78-dən yuxarı olduqda mal-qara istilik stressinə məruz qalır. Bu, süd məhsuldarlığını 10-25% azaldır, immuniteti zəiflədir və respirator xəstəlik riskini artırır.",
                rule_id="AZ-LIVE-002",
                source="hybrid",
                suggested_time="dərhal",
                deadline=date.today(),
            ))
        
        # HIGH: Respiratory disease warning
        if barn_humidity > 70:
            recs.append(RecommendationItem(
                id=f"rec-{uuid4().hex[:8]}",
                type=RecommendationType.LIVESTOCK_CARE,
                priority=RecommendationPriority.HIGH,
                confidence=0.87,
                title="🫁 Respirator Xəstəlik Riski",
                description="Yüksək rütubət şəraitində respirator xəstəliklər (pnevmoniya, bronxit) riski artır.",
                action="Heyvanları bu simptomlara görə yoxlayın:\n• Öskürək və ya ağır tənəffüs\n• Burun axıntısı\n• Qızdırma (39.5°C+)\n• İştaha azalması\n• Süst davranış",
                why_title="Hansı xəstəliklərə diqqət?",
                why_explanation="Yüksək rütubətdə bakterial və viral patogenlər (Mannheimia, Pasteurella, IBR virusu) daha sürətlə yayılır. Erkən aşkarlama müalicə effektivliyini 70% artırır.",
                rule_id="AZ-LIVE-003",
                source="rulebook",
            ))
        
        # MEDIUM: Vaccination reminder
        recs.append(RecommendationItem(
            id=f"rec-{uuid4().hex[:8]}",
            type=RecommendationType.VACCINATION,
            priority=RecommendationPriority.MEDIUM,
            confidence=0.75,
            title="💉 Peyvənd Cədvəli Yoxlaması",
            description="Mal-qaranın son peyvənd tarixini yoxlayın. 6 aydan çox keçibsə, yeniləmə lazımdır.",
            action="Baytar həkiminizlə əlaqə saxlayın. Tövsiyə olunan peyvəndlər:\n• Şap xəstəliyi (FMD)\n• Brusellyoz\n• Anthrax (Şirpəncə)",
            why_title="Peyvənd niyə vacibdir?",
            why_explanation="Azərbaycanda şap xəstəliyi enzootik bölgələrdə mövcuddur. Vaxtında peyvənd 95% qoruma təmin edir və sürü sağlamlığını qoruyur.",
            rule_id="AZ-VACC-001",
            source="rulebook",
        ))
        
        return recs
    
    def _orchard_recommendations(
        self, 
        request: FarmProfileRequest
    ) -> list[RecommendationItem]:
        """Generate recommendations for orchard farm."""
        recs = []
        
        # Phosphorus for fruiting
        if request.soil_moisture_percent and request.soil_moisture_percent < 40:
            recs.append(RecommendationItem(
                id=f"rec-{uuid4().hex[:8]}",
                type=RecommendationType.IRRIGATION,
                priority=RecommendationPriority.HIGH,
                confidence=0.86,
                title="💧 Damcı Suvarma Optimallaşdırması",
                description=f"Torpaq nəmliyi {request.soil_moisture_percent}% - meyvə dolumu mərhələsi üçün optimal deyil.",
                action="Damcı suvarma sistemini gündə 2 saat işlədin. Hər ağaca 20-30 litr su təmin edin.",
                why_title="Meyvə dolumu nədir?",
                why_explanation="Meyvə dolumu mərhələsində su çatışmazlığı meyvə ölçüsünü kiçildir və şəkər toplanmasını azaldır. Quba almalarının premium qiyməti böyük ölçüdən asılıdır.",
                rule_id="AZ-IRR-005",
                source="hybrid",
                suggested_time="06:00-08:00, 18:00-20:00",
            ))
        
        # Pest monitoring
        recs.append(RecommendationItem(
            id=f"rec-{uuid4().hex[:8]}",
            type=RecommendationType.PEST_CONTROL,
            priority=RecommendationPriority.MEDIUM,
            confidence=0.80,
            title="🐛 Alma Güvəsi Monitorinqi",
            description="Yay mövsümündə alma güvəsi (Cydia pomonella) aktivliyi artır.",
            action="Feromon tələlərini yoxlayın. Həftədə 5-dən çox güvə tutulursa, müdaxilə lazımdır.",
                why_title="Alma güvəsi nə edir?",
                why_explanation="Güvə sürfələri meyvənin içinə girərək onu satışa yararsız edir. Vaxtında feromon tələ istifadəsi 60-80% zərəri azaldır.",
                rule_id="AZ-PEST-002",
                source="rulebook",
        ))
        
        return recs
    
    def _mixed_recommendations(
        self, 
        request: FarmProfileRequest
    ) -> list[RecommendationItem]:
        """Generate recommendations for mixed farm."""
        recs = []
        
        # Tomato harvest
        recs.append(RecommendationItem(
            id=f"rec-{uuid4().hex[:8]}",
            type=RecommendationType.HARVEST,
            priority=RecommendationPriority.HIGH,
            confidence=0.85,
            title="🍅 Pomidor Yığımı Vaxtı",
            description="Pomidorlar meyvəvermə mərhələsindədir. Yetişmiş meyvələri vaxtında yığın.",
            action="Hər gün səhər saat 07:00-10:00 arasında yetişmiş pomidorları yığın. Qırmızı rəngli, möhkəm meyvələri seçin.",
            why_title="Vaxtında yığım niyə vacib?",
            why_explanation="Həddən artıq yetişmiş pomidorlar daha tez xarab olur və bazar qiyməti düşür. Gündəlik yığım ümumi məhsuldarlığı 15-20% artırır.",
            rule_id="AZ-HARV-003",
            source="rulebook",
            suggested_time="07:00-10:00",
        ))
        
        # Integrated farm management
        recs.append(RecommendationItem(
            id=f"rec-{uuid4().hex[:8]}",
            type=RecommendationType.GENERAL,
            priority=RecommendationPriority.MEDIUM,
            confidence=0.78,
            title="♻️ İnteqrasiya olunmuş Təsərrüfat",
            description="İnək peyinini tərəvəz sahəsinə gübrə kimi istifadə edin.",
            action="Kompostlaşdırılmış peyini pomidor və xiyar sahələrinə tətbiq edin. Hər 100m² üçün 50kg.",
            why_title="Organik dövriyyə nədir?",
            why_explanation="Mal-qara peyini zəngin azot və fosfor mənbəyidir. Düzgün kompostlaşdırma ilə gübrə xərcini 40% azalda bilərsiniz.",
            rule_id="AZ-ORG-001",
            source="rulebook",
        ))
        
        return recs
    
    def _poultry_recommendations(
        self, 
        request: FarmProfileRequest
    ) -> list[RecommendationItem]:
        """Generate recommendations for poultry farm."""
        recs = []
        
        # Climate control
        if request.humidity_percent and request.humidity_percent > 70:
            recs.append(RecommendationItem(
                id=f"rec-{uuid4().hex[:8]}",
                type=RecommendationType.VENTILATION,
                priority=RecommendationPriority.HIGH,
                confidence=0.88,
                title="🐔 Kümes İqlim Nəzarəti",
                description=f"Kümes rütubəti {request.humidity_percent}% - optimal aralıqdan (50-70%) yuxarıdır.",
                action="1. Ventilyasiya sistemini yoxlayın\n2. Döşəmə materialını dəyişin\n3. Su sistemlərini sızdırmazlığa görə yoxlayın",
                why_title="Rütubət niyə əhəmiyyətlidir?",
                why_explanation="Yüksək rütubət ammonyak səviyyəsini artırır və tənəffüs xəstəlikləri riskini qaldırır. Optimal rütubət yumurta istehsalını 5-10% artırır.",
                rule_id="AZ-POULTRY-001",
                source="hybrid",
            ))
        
        # Feed optimization
        recs.append(RecommendationItem(
            id=f"rec-{uuid4().hex[:8]}",
            type=RecommendationType.LIVESTOCK_CARE,
            priority=RecommendationPriority.MEDIUM,
            confidence=0.82,
            title="🌾 Yem Optimallaşdırması",
            description="Yay aylarında yumurta toyuqları üçün kalsium əlavəsi vacibdir.",
            action="Yemə əlavə olaraq əzilmiş istiridyə qabığı (3-4%) və ya əhəng daşı tozu verin.",
            why_title="Kalsium niyə lazım?",
            why_explanation="İsti havada toyuqlar daha az yem yeyir, bu da kalsium çatışmazlığına səbəb olur. Nazik qabıqlı yumurtalar satış keyfiyyətini azaldır.",
            rule_id="AZ-POULTRY-002",
            source="rulebook",
        ))
        
        return recs
    
    def _generate_daily_routine(
        self,
        request: FarmProfileRequest,
        recommendations: list[RecommendationItem]
    ) -> list[DailyRoutineItem]:
        """Generate a daily routine timeline based on farm type."""
        routine = []
        
        # Base routines by farm type
        if request.farm_type in ("wheat", "taxıl"):
            routine = [
                DailyRoutineItem(
                    time_slot="05:30",
                    duration_minutes=30,
                    title="Sahə müayinəsi",
                    description="Buğda sahəsini gəzin, stress əlamətlərini yoxlayın",
                    icon="👁️",
                    category="monitoring",
                    priority=RecommendationPriority.MEDIUM,
                ),
                DailyRoutineItem(
                    time_slot="06:00",
                    duration_minutes=120,
                    title="Suvarma",
                    description="Arxlı suvarma sistemini işə salın",
                    icon="💧",
                    category="irrigation",
                    priority=RecommendationPriority.HIGH,
                ),
                DailyRoutineItem(
                    time_slot="09:00",
                    duration_minutes=60,
                    title="Gübrə tətbiqi",
                    description="Azot gübrəsini suvarma ilə birlikdə verin",
                    icon="🌱",
                    category="fertilization",
                    priority=RecommendationPriority.HIGH,
                ),
                DailyRoutineItem(
                    time_slot="11:00",
                    duration_minutes=180,
                    title="İstirahət",
                    description="Günorta istisindən qaçının",
                    icon="☀️",
                    category="break",
                    priority=RecommendationPriority.LOW,
                ),
                DailyRoutineItem(
                    time_slot="16:00",
                    duration_minutes=90,
                    title="Avadanlıq baxımı",
                    description="Suvarma avadanlığını yoxlayın və təmizləyin",
                    icon="🔧",
                    category="maintenance",
                    priority=RecommendationPriority.MEDIUM,
                ),
            ]
        elif request.farm_type in ("livestock", "heyvandarlıq"):
            routine = [
                DailyRoutineItem(
                    time_slot="05:00",
                    duration_minutes=60,
                    title="Səhər yemləməsi",
                    description="Mal-qaranı yemləyin, su qablarını doldurun",
                    icon="🥬",
                    category="feeding",
                    priority=RecommendationPriority.HIGH,
                ),
                DailyRoutineItem(
                    time_slot="06:00",
                    duration_minutes=90,
                    title="Sağım",
                    description="İnəkləri sağın, süd keyfiyyətini yoxlayın",
                    icon="🥛",
                    category="milking",
                    priority=RecommendationPriority.HIGH,
                ),
                DailyRoutineItem(
                    time_slot="08:00",
                    duration_minutes=60,
                    title="Sağlamlıq yoxlaması",
                    description="Hər heyvanı vizual yoxlayın, simptomları qeyd edin",
                    icon="🩺",
                    category="health",
                    priority=RecommendationPriority.HIGH,
                ),
                DailyRoutineItem(
                    time_slot="10:00",
                    duration_minutes=30,
                    title="Ventilyasiya yoxlaması",
                    description="Tövlə temperatur və rütubətini ölçün",
                    icon="🌡️",
                    category="environment",
                    priority=RecommendationPriority.CRITICAL,
                ),
                DailyRoutineItem(
                    time_slot="17:00",
                    duration_minutes=60,
                    title="Axşam yemləməsi",
                    description="Axşam yemlənməsi, döşəmə yoxlaması",
                    icon="🌾",
                    category="feeding",
                    priority=RecommendationPriority.HIGH,
                ),
                DailyRoutineItem(
                    time_slot="18:00",
                    duration_minutes=90,
                    title="Axşam sağımı",
                    description="İkinci sağım, avadanlıq təmizliyi",
                    icon="🥛",
                    category="milking",
                    priority=RecommendationPriority.HIGH,
                ),
            ]
        elif request.farm_type in ("poultry", "quşçuluq"):
            routine = [
                DailyRoutineItem(
                    time_slot="05:00",
                    duration_minutes=30,
                    title="İşıqlandırma",
                    description="Kümes işıqlarını yandırın",
                    icon="💡",
                    category="environment",
                    priority=RecommendationPriority.HIGH,
                ),
                DailyRoutineItem(
                    time_slot="05:30",
                    duration_minutes=60,
                    title="Yemləmə",
                    description="Yem və su sistemlərini yoxlayın, doldurun",
                    icon="🌾",
                    category="feeding",
                    priority=RecommendationPriority.HIGH,
                ),
                DailyRoutineItem(
                    time_slot="07:00",
                    duration_minutes=90,
                    title="Yumurta yığımı",
                    description="Yumurtaları yığın, keyfiyyət sortlaması",
                    icon="🥚",
                    category="collection",
                    priority=RecommendationPriority.HIGH,
                ),
                DailyRoutineItem(
                    time_slot="10:00",
                    duration_minutes=60,
                    title="Kümes təmizliyi",
                    description="Döşəmə və yuva qutularını təmizləyin",
                    icon="🧹",
                    category="hygiene",
                    priority=RecommendationPriority.MEDIUM,
                ),
                DailyRoutineItem(
                    time_slot="14:00",
                    duration_minutes=30,
                    title="İqlim nəzarəti",
                    description="Temperatur, rütubət, ammonyak səviyyəsini ölçün",
                    icon="🌡️",
                    category="environment",
                    priority=RecommendationPriority.HIGH,
                ),
                DailyRoutineItem(
                    time_slot="16:00",
                    duration_minutes=60,
                    title="İkinci yumurta yığımı",
                    description="Günorta yumurtalarını yığın",
                    icon="🥚",
                    category="collection",
                    priority=RecommendationPriority.MEDIUM,
                ),
            ]
        else:  # orchard, mixed, default
            routine = [
                DailyRoutineItem(
                    time_slot="06:00",
                    duration_minutes=60,
                    title="Bağ gəzintisi",
                    description="Ağacları vizual yoxlayın, zərərverici əlamətləri axtarın",
                    icon="🚶",
                    category="monitoring",
                    priority=RecommendationPriority.MEDIUM,
                ),
                DailyRoutineItem(
                    time_slot="07:00",
                    duration_minutes=120,
                    title="Suvarma",
                    description="Damcı suvarma sistemini işə salın",
                    icon="💧",
                    category="irrigation",
                    priority=RecommendationPriority.HIGH,
                ),
                DailyRoutineItem(
                    time_slot="09:00",
                    duration_minutes=180,
                    title="Məhsul yığımı",
                    description="Yetişmiş meyvə/tərəvəzləri yığın",
                    icon="🧺",
                    category="harvest",
                    priority=RecommendationPriority.HIGH,
                ),
                DailyRoutineItem(
                    time_slot="14:00",
                    duration_minutes=60,
                    title="Feromon tələ yoxlaması",
                    description="Tələləri yoxlayın, tutulmuş həşəratları sayın",
                    icon="🪤",
                    category="pest_control",
                    priority=RecommendationPriority.MEDIUM,
                ),
                DailyRoutineItem(
                    time_slot="17:00",
                    duration_minutes=60,
                    title="Axşam suvarması",
                    description="İkinci suvarma dövrü (lazım olduqda)",
                    icon="💧",
                    category="irrigation",
                    priority=RecommendationPriority.MEDIUM,
                ),
            ]
        
        return routine
    
    def get_health(self) -> dict:
        """GET /health endpoint simulation."""
        return {
            "status": "healthy",
            "inference_engine": "qwen2.5-7b-simulated",
            "total_requests": self._request_counter,
            "timestamp": datetime.now().isoformat(),
        }


# Create singleton instance
mock_backend = MockBackend()

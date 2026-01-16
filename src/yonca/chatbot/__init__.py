"""
Yonca AI - Azerbaijani Language Chatbot
Intent-based conversational assistant for farmers.
"""
import re
from dataclasses import dataclass
from typing import Optional
from datetime import date

from yonca.models import (
    ChatMessage, ChatResponse, FarmProfile, Task, TaskPriority, TaskStatus
)
from yonca.core.engine import recommendation_engine
from yonca.data.scenarios import get_scenario_farms
from yonca.config import settings


@dataclass
class Intent:
    """A chatbot intent definition."""
    name: str
    patterns: list[str]
    response_template: str
    requires_farm: bool = False
    action: Optional[str] = None


# ============= Intent Definitions =============

INTENTS = [
    # Greeting intents
    Intent(
        name="greeting",
        patterns=[
            r"salam",
            r"salamlar",
            r"xoş gəldin",
            r"necəsən",
            r"necəsiniz",
            r"hello",
            r"hi\b",
        ],
        response_template="Salam! Mən Yonca AI köməkçisiyəm. Sizə təsərrüfat işlərində necə kömək edə bilərəm?",
    ),
    
    # Irrigation queries
    Intent(
        name="suvarma_sorğusu",
        patterns=[
            r"suvar",
            r"su ver",
            r"nə vaxt suvarım",
            r"suvarma",
            r"su lazımdır",
            r"torpaq quru",
            r"nəmlik",
        ],
        response_template="Suvarma məsləhəti üçün təsərrüfatınızı yoxlayıram...",
        requires_farm=True,
        action="irrigation_advice",
    ),
    
    # Fertilization queries
    Intent(
        name="gübrələmə_sorğusu",
        patterns=[
            r"gübrə",
            r"gübrələmə",
            r"azot",
            r"fosfor",
            r"kalium",
            r"torpaq qidalandırma",
            r"nə vaxt gübrə",
        ],
        response_template="Gübrələmə tövsiyələri hazırlanır...",
        requires_farm=True,
        action="fertilization_advice",
    ),
    
    # Pest and disease queries
    Intent(
        name="xəstəlik_xəbərdarlığı",
        patterns=[
            r"xəstəlik",
            r"zərərverici",
            r"göbələk",
            r"mənənə",
            r"böcək",
            r"ziyanverici",
            r"yarpaq sarı",
            r"bitki xəstə",
        ],
        response_template="Zərərverici və xəstəlik riskləri yoxlanılır...",
        requires_farm=True,
        action="pest_disease_advice",
    ),
    
    # Harvest queries
    Intent(
        name="məhsul_yığımı",
        patterns=[
            r"məhsul yığ",
            r"biçin",
            r"yığım",
            r"nə vaxt yığım",
            r"harvest",
            r"yetişib",
            r"hazırdır",
        ],
        response_template="Məhsul yığımı vaxtını hesablayıram...",
        requires_farm=True,
        action="harvest_advice",
    ),
    
    # Weather queries
    Intent(
        name="hava_sorğusu",
        patterns=[
            r"hava",
            r"yağış",
            r"temperatur",
            r"fırtına",
            r"günəş",
            r"proqnoz",
            r"hava necə olacaq",
        ],
        response_template="Hava proqnozu yoxlanılır...",
        requires_farm=True,
        action="weather_info",
    ),
    
    # Livestock queries
    Intent(
        name="heyvan_sorğusu",
        patterns=[
            r"heyvan",
            r"mal-qara",
            r"inək",
            r"qoyun",
            r"toyuq",
            r"peyvənd",
            r"yemləmə",
            r"sağlamlıq",
        ],
        response_template="Heyvandarlıq məsləhəti hazırlanır...",
        requires_farm=True,
        action="livestock_advice",
    ),
    
    # Subsidy queries
    Intent(
        name="subsidiya_sorğusu",
        patterns=[
            r"subsidiya",
            r"dövlət yardımı",
            r"müraciət",
            r"tarix",
            r"son müddət",
            r"deadline",
        ],
        response_template="Subsidiya məlumatları axtarılır...",
        action="subsidy_info",
    ),
    
    # Schedule/Task queries
    Intent(
        name="cədvəl_sorğusu",
        patterns=[
            r"cədvəl",
            r"bu gün",
            r"tapşırıq",
            r"nə edim",
            r"plan",
            r"işlər",
            r"gündəlik",
        ],
        response_template="Gündəlik cədvəlinizi hazırlayıram...",
        requires_farm=True,
        action="daily_schedule",
    ),
    
    # Help intent
    Intent(
        name="kömək",
        patterns=[
            r"kömək",
            r"help",
            r"nə edə bilərsən",
            r"imkan",
            r"funksiya",
        ],
        response_template="""Mən sizə aşağıdakı mövzularda kömək edə bilərəm:

🌊 **Suvarma** - "Nə vaxt suvarmalıyam?" soruşun
🌱 **Gübrələmə** - "Gübrə lazımdırmı?" soruşun  
🐛 **Zərərvericilər** - "Xəstəlik riski varmı?" soruşun
🌾 **Məhsul yığımı** - "Məhsul hazırdırmı?" soruşun
🌤️ **Hava** - "Hava necə olacaq?" soruşun
🐄 **Heyvandarlıq** - "Peyvənd lazımdırmı?" soruşun
📋 **Gündəlik plan** - "Bu gün nə edim?" soruşun
💰 **Subsidiya** - "Subsidiya tarixləri?" soruşun

Sadəcə sualınızı yazın!""",
    ),
    
    # Goodbye intent
    Intent(
        name="vidalaşma",
        patterns=[
            r"sağ ol",
            r"təşəkkür",
            r"görüşənədək",
            r"bye",
            r"hələlik",
        ],
        response_template="Xoş gəldiniz! Uğurlar, başqa sualınız olsa yenə yazın. 🌿",
    ),
]


class AzerbaijaniChatbot:
    """
    Intent-based chatbot for Azerbaijani-speaking farmers.
    """
    
    def __init__(self):
        self.intents = INTENTS
        self.farms = get_scenario_farms()
        self.fallback_message = settings.chatbot_fallback_message
        self.confidence_threshold = settings.chatbot_confidence_threshold
    
    def process_message(
        self,
        message: ChatMessage,
        farm: Optional[FarmProfile] = None
    ) -> ChatResponse:
        """
        Process an incoming chat message and generate a response.
        
        Args:
            message: The incoming chat message
            farm: Optional farm profile for context
            
        Returns:
            ChatResponse with the assistant's reply
        """
        text = message.message.lower().strip()
        
        # Find matching intent
        matched_intent, confidence = self._match_intent(text)
        
        if not matched_intent or confidence < self.confidence_threshold:
            return ChatResponse(
                message=self.fallback_message,
                intent=None,
                confidence=confidence,
                suggestions=[
                    "Suvarma haqqında soruşun",
                    "Gübrələmə məsləhəti alın",
                    "Gündəlik plan",
                    "Kömək",
                ],
            )
        
        # Get farm if needed
        if matched_intent.requires_farm and not farm:
            farm_id = message.farm_id
            if farm_id and farm_id in self.farms:
                farm = self.farms[farm_id]
            else:
                # Use first scenario farm as default
                farm = list(self.farms.values())[0]
        
        # Generate response based on intent
        response_text, related_tasks = self._generate_response(
            matched_intent, farm, text
        )
        
        return ChatResponse(
            message=response_text,
            intent=matched_intent.name,
            confidence=confidence,
            suggestions=self._get_suggestions(matched_intent),
            related_tasks=related_tasks,
        )
    
    def _match_intent(self, text: str) -> tuple[Optional[Intent], float]:
        """Match text to an intent and return confidence score."""
        best_match: Optional[Intent] = None
        best_score = 0.0
        
        for intent in self.intents:
            for pattern in intent.patterns:
                if re.search(pattern, text, re.IGNORECASE):
                    # Simple scoring based on pattern length ratio
                    score = len(pattern) / max(len(text), 1)
                    score = min(score + 0.5, 1.0)  # Boost matched patterns
                    
                    if score > best_score:
                        best_score = score
                        best_match = intent
        
        return best_match, best_score
    
    def _generate_response(
        self,
        intent: Intent,
        farm: Optional[FarmProfile],
        original_text: str
    ) -> tuple[str, list[Task]]:
        """Generate a response based on the matched intent."""
        related_tasks: list[Task] = []
        
        # If no action required, return template
        if not intent.action:
            return intent.response_template, related_tasks
        
        # Generate action-specific responses
        if intent.action == "irrigation_advice" and farm:
            return self._irrigation_response(farm)
        
        elif intent.action == "fertilization_advice" and farm:
            return self._fertilization_response(farm)
        
        elif intent.action == "pest_disease_advice" and farm:
            return self._pest_response(farm)
        
        elif intent.action == "harvest_advice" and farm:
            return self._harvest_response(farm)
        
        elif intent.action == "weather_info" and farm:
            return self._weather_response(farm)
        
        elif intent.action == "livestock_advice" and farm:
            return self._livestock_response(farm)
        
        elif intent.action == "daily_schedule" and farm:
            return self._schedule_response(farm)
        
        elif intent.action == "subsidy_info":
            return self._subsidy_response()
        
        return intent.response_template, related_tasks
    
    def _irrigation_response(self, farm: FarmProfile) -> tuple[str, list[Task]]:
        """Generate irrigation advice response."""
        tasks = []
        
        if not farm.soil_data:
            return "Torpaq məlumatları mövcud deyil. Torpaq nəmliyini ölçməyi tövsiyə edirəm.", tasks
        
        soil = farm.soil_data
        moisture = soil.moisture_percent
        
        if moisture < 30:
            response = f"""⚠️ **Təcili suvarma lazımdır!**

Torpaq nəmliyi: **{moisture}%** (optimal: 40-60%)
Torpaq tipi: {soil.soil_type.value}

📋 **Tövsiyə:**
- Bu gün səhər tezdən (6:00-8:00) suvarın
- Damcı suvarma ilə 20-25mm su verin
- Yenidən 2-3 gün sonra yoxlayın"""
            
            tasks.append(Task(
                id="task-irr-001",
                title="Irrigate fields",
                title_az="Sahələri suvarın",
                description=f"Soil moisture at {moisture}%",
                description_az=f"Torpaq nəmliyi {moisture}%",
                priority=TaskPriority.HIGH,
                status=TaskStatus.PENDING,
                due_date=date.today(),
                estimated_duration_minutes=120,
                category="irrigation",
            ))
        
        elif moisture < 45:
            response = f"""ℹ️ **Suvarma planlaşdırın**

Torpaq nəmliyi: **{moisture}%** (yaxşı, amma izləyin)

📋 **Tövsiyə:**
- 1-2 gün ərzində suvarma planlaşdırın
- Hava proqnozunu yoxlayın (yağış gözlənilir?)
- Bitkilərin vəziyyətini izləyin"""
        
        else:
            response = f"""✅ **Torpaq nəmliyi yaxşıdır**

Torpaq nəmliyi: **{moisture}%**

📋 **Tövsiyə:**
- Hazırda suvarma lazım deyil
- 3-4 gün sonra yenidən yoxlayın
- Həddindən artıq suvarmadan çəkinin"""
        
        return response, tasks
    
    def _fertilization_response(self, farm: FarmProfile) -> tuple[str, list[Task]]:
        """Generate fertilization advice response."""
        tasks = []
        
        if not farm.soil_data:
            return "Torpaq analizi məlumatları mövcud deyil. Laboratoriya testini tövsiyə edirəm.", tasks
        
        soil = farm.soil_data
        recommendations = []
        
        if soil.nitrogen_level < 30:
            recommendations.append(f"🟡 **Azot aşağıdır** ({soil.nitrogen_level} kg/ha) - Azot gübrəsi tətbiq edin")
        
        if soil.phosphorus_level < 25:
            recommendations.append(f"🟡 **Fosfor aşağıdır** ({soil.phosphorus_level} kg/ha) - Fosfor gübrəsi tətbiq edin")
        
        if soil.potassium_level < 100:
            recommendations.append(f"🟡 **Kalium aşağıdır** ({soil.potassium_level} kg/ha) - Kalium gübrəsi tətbiq edin")
        
        if soil.ph_level < 5.5 or soil.ph_level > 7.5:
            ph_action = "əhəng" if soil.ph_level < 5.5 else "kükürd"
            recommendations.append(f"⚠️ **pH tənzimləyin** ({soil.ph_level}) - {ph_action} tətbiq edin")
        
        if recommendations:
            rec_text = "\n".join(recommendations)
            response = f"""📊 **Torpaq Analizi Nəticələri**

{rec_text}

📋 **Ümumi tövsiyələr:**
- Gübrələməni səhər tezdən edin
- Suvarma ilə birləşdirin (çatılma)
- 2 həftə sonra yenidən test edin"""
        else:
            response = f"""✅ **Torpaq qida səviyyəsi yaxşıdır**

- Azot: {soil.nitrogen_level} kg/ha ✓
- Fosfor: {soil.phosphorus_level} kg/ha ✓
- Kalium: {soil.potassium_level} kg/ha ✓
- pH: {soil.ph_level} ✓

Hazırda əlavə gübrələmə lazım deyil."""
        
        return response, tasks
    
    def _pest_response(self, farm: FarmProfile) -> tuple[str, list[Task]]:
        """Generate pest/disease advice response."""
        tasks = []
        
        from yonca.data.generators import WeatherGenerator
        weather = WeatherGenerator.generate(date.today(), farm.location.region, 1)[0]
        
        risks = []
        
        if weather.humidity_percent > 75:
            risks.append(f"🍄 **Göbələk riski YÜKSƏK** - Rütubət {weather.humidity_percent}%")
        
        if weather.temperature_max > 25 and weather.humidity_percent < 50:
            risks.append("🐛 **Mənənə riski** - İsti və quru hava")
        
        if weather.precipitation_mm > 15:
            risks.append(f"🌧️ **Yağışdan sonra yoxlayın** - {weather.precipitation_mm}mm yağış")
        
        if risks:
            risk_text = "\n".join(risks)
            response = f"""⚠️ **Zərərverici/Xəstəlik Riskləri**

{risk_text}

📋 **Tövsiyələr:**
- Bitkiləri hər gün yoxlayın
- Xəstə yarpaqları təcrid edin
- Lazım gəldikdə müdafiə preparatı tətbiq edin
- Peşəkar aqronomla məsləhətləşin"""
        else:
            response = """✅ **Hazırda ciddi risk aşkar edilmədi**

📋 **Profilaktik tövsiyələr:**
- Həftədə bir dəfə bitkiləri yoxlayın
- Yarpaq rəngini və formasını izləyin
- Hava dəyişikliklərini izləyin"""
        
        return response, tasks
    
    def _harvest_response(self, farm: FarmProfile) -> tuple[str, list[Task]]:
        """Generate harvest timing advice."""
        tasks = []
        
        if not farm.crops:
            return "Əkin məlumatları mövcud deyil.", tasks
        
        from yonca.models import CropStage
        
        harvest_info = []
        for crop in farm.crops:
            days_to_harvest = (crop.expected_harvest_date - date.today()).days if crop.expected_harvest_date else None
            
            if crop.current_stage == CropStage.MATURITY:
                harvest_info.append(f"🌾 **{crop.crop_type}** - YETİŞİB! Bu gün yığım mümkündür")
            elif crop.current_stage == CropStage.HARVEST:
                harvest_info.append(f"✅ **{crop.crop_type}** - Yığım mərhələsində")
            elif days_to_harvest and days_to_harvest <= 7:
                harvest_info.append(f"⏳ **{crop.crop_type}** - ~{days_to_harvest} gün qalıb")
            elif days_to_harvest:
                harvest_info.append(f"📅 **{crop.crop_type}** - {days_to_harvest} gün sonra ({crop.expected_harvest_date})")
        
        info_text = "\n".join(harvest_info) if harvest_info else "Yığım üçün hazır bitki yoxdur."
        
        response = f"""🌾 **Məhsul Yığımı Statusu**

{info_text}

📋 **Tövsiyələr:**
- Hava proqnozunu yoxlayın (quru gün seçin)
- Yığım avadanlığını hazırlayın
- Saxlama yerini təmizləyin"""
        
        return response, tasks
    
    def _weather_response(self, farm: FarmProfile) -> tuple[str, list[Task]]:
        """Generate weather information response."""
        from yonca.data.generators import WeatherGenerator
        
        forecast = WeatherGenerator.generate(date.today(), farm.location.region, 3)
        
        weather_lines = []
        for w in forecast:
            emoji = {
                "sunny": "☀️",
                "cloudy": "☁️", 
                "rainy": "🌧️",
                "stormy": "⛈️",
                "snowy": "❄️",
                "windy": "💨",
            }.get(w.condition.value, "🌤️")
            
            weather_lines.append(
                f"{emoji} **{w.date}**: {w.temperature_min}°C - {w.temperature_max}°C, "
                f"Rütubət: {w.humidity_percent}%"
            )
        
        weather_text = "\n".join(weather_lines)
        
        response = f"""🌤️ **Hava Proqnozu - {farm.location.region}**

{weather_text}

📋 **Təsərrüfat Tövsiyələri:**
- Temperatur >35°C olduqda suvarmanı artırın
- Yağış gözlənilirsə suvarmanı təxirə salın
- Fırtına xəbərdarlığında məhsul yığımını tezləşdirin"""
        
        return response, []
    
    def _livestock_response(self, farm: FarmProfile) -> tuple[str, list[Task]]:
        """Generate livestock advice response."""
        tasks = []
        
        if not farm.livestock:
            return "Heyvandarlıq məlumatları mövcud deyil.", tasks
        
        livestock_info = []
        for animal in farm.livestock:
            days_since_vacc = (date.today() - animal.last_vaccination_date).days if animal.last_vaccination_date else None
            
            status_emoji = "✅" if animal.health_status == "sağlam" else "⚠️"
            
            info = f"{status_emoji} **{animal.livestock_type.value.capitalize()}**: {animal.count} baş"
            
            if days_since_vacc and days_since_vacc > 180:
                info += f" ⚠️ Peyvənd {days_since_vacc} gün əvvəl - YENİLƏMƏ LAZIM!"
            elif days_since_vacc:
                info += f" (Son peyvənd: {days_since_vacc} gün əvvəl)"
            
            livestock_info.append(info)
        
        info_text = "\n".join(livestock_info)
        
        response = f"""🐄 **Heyvandarlıq Statusu**

{info_text}

📋 **Tövsiyələr:**
- Hər gün su və yem yoxlayın
- İsti havada kölgə təmin edin
- Peyvənd cədvəlini izləyin
- Sağlamlıq dəyişikliklərini qeyd edin"""
        
        return response, tasks
    
    def _schedule_response(self, farm: FarmProfile) -> tuple[str, list[Task]]:
        """Generate daily schedule response."""
        schedule = recommendation_engine.generate_daily_schedule(farm)
        
        if not schedule.tasks:
            response = """✅ **Bu gün üçün planlaşdırılmış tapşırıq yoxdur**

Yaxşı gün! Lakin aşağıdakıları unutmayın:
- Bitkiləri gündəlik yoxlayın
- Hava proqnozunu izləyin
- Avadanlığı yoxlayın"""
            return response, []
        
        task_lines = []
        priority_emoji = {
            TaskPriority.CRITICAL: "🔴",
            TaskPriority.HIGH: "🟠",
            TaskPriority.MEDIUM: "🟡",
            TaskPriority.LOW: "🟢",
        }
        
        for task in schedule.tasks[:5]:  # Top 5 tasks
            emoji = priority_emoji.get(task.priority, "⚪")
            task_lines.append(f"{emoji} {task.title_az}")
        
        task_text = "\n".join(task_lines)
        
        alert_text = ""
        if schedule.alerts:
            alert_lines = [f"⚠️ {a.title_az}" for a in schedule.alerts[:3]]
            alert_text = "\n\n**Xəbərdarlıqlar:**\n" + "\n".join(alert_lines)
        
        response = f"""📋 **Bu Gün üçün Plan - {date.today()}**

**Tapşırıqlar:**
{task_text}
{alert_text}

Tapşırıq detalları üçün həmin mövzunu soruşun."""
        
        return response, schedule.tasks
    
    def _subsidy_response(self) -> tuple[str, list[Task]]:
        """Generate subsidy information response."""
        response = """💰 **Subsidiya Məlumatları**

**Mövcud proqramlar:**
- 🌾 Taxıl subsidiyası - Müraciət: Mart-Aprel
- 🐄 Heyvandarlıq dəstəyi - Müraciət: İl boyu
- 🌱 Toxum subsidiyası - Müraciət: Fevral
- 💧 Suvarma avadanlığı - Müraciət: Yanvar-Mart

📍 **Müraciət qaydası:**
1. ASAN Xidmət mərkəzinə gedin
2. Torpaq sənədlərini hazırlayın
3. Bank hesabı məlumatları
4. Şəxsiyyət vəsiqəsi

📞 **Əlaqə:** Kənd Təsərrüfatı Nazirliyi
🌐 **Yonca tətbiqində** subsidiya bölməsini yoxlayın"""
        
        return response, []
    
    def _get_suggestions(self, current_intent: Intent) -> list[str]:
        """Get suggested follow-up queries."""
        suggestion_map = {
            "suvarma_sorğusu": ["Gübrələmə lazımdırmı?", "Hava necə olacaq?", "Gündəlik plan"],
            "gübrələmə_sorğusu": ["Suvarma lazımdırmı?", "Zərərverici riski?", "Gündəlik plan"],
            "xəstəlik_xəbərdarlığı": ["Hava proqnozu", "Suvarma tövsiyəsi", "Məhsul yığımı"],
            "məhsul_yığımı": ["Hava proqnozu", "Gündəlik plan", "Subsidiya məlumatları"],
            "hava_sorğusu": ["Suvarma lazımdırmı?", "Zərərverici riski?", "Məhsul yığımı"],
            "heyvan_sorğusu": ["Hava proqnozu", "Gündəlik plan", "Subsidiya"],
            "cədvəl_sorğusu": ["Suvarma", "Gübrələmə", "Hava"],
            "greeting": ["Gündəlik plan", "Suvarma", "Kömək"],
        }
        
        return suggestion_map.get(current_intent.name, ["Gündəlik plan", "Kömək"])


# Singleton instance
chatbot = AzerbaijaniChatbot()

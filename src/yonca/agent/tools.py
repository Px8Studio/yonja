"""
Yonca AI - LangGraph Tools
Tool definitions for the farm assistant agent.
"""
from datetime import date
from typing import Optional, Annotated
from langchain_core.tools import tool

from yonca.data.scenarios import get_scenario_farms
from yonca.data.generators import WeatherGenerator, SoilGenerator
from yonca.sidecar import generate_daily_schedule


@tool
def get_weather_tool(
    region: Annotated[str, "Region name in Azerbaijan (e.g., 'Aran', 'Şəki-Zaqatala', 'Lənkəran')"],
    days: Annotated[int, "Number of forecast days (1-14)"] = 7
) -> str:
    """
    Get weather forecast for a specific region in Azerbaijan.
    Use this tool when the user asks about weather, temperature, rain, or climate conditions.
    Returns weather data including temperature, humidity, precipitation, and conditions.
    """
    try:
        forecast = WeatherGenerator.generate(date.today(), region, min(days, 14))
        
        result = f"🌤️ Hava proqnozu - {region} ({days} gün):\n\n"
        
        for w in forecast[:5]:  # Show max 5 days in response
            emoji = {
                "sunny": "☀️", "cloudy": "☁️", "rainy": "🌧️",
                "stormy": "⛈️", "snowy": "❄️", "windy": "💨"
            }.get(w.condition.value, "🌤️")
            
            result += f"{emoji} {w.date}: {w.temperature_min}°C - {w.temperature_max}°C, "
            result += f"Rütubət: {w.humidity_percent}%, Yağıntı: {w.precipitation_mm}mm\n"
        
        return result
    except Exception as e:
        return f"Xəta: {region} üçün hava məlumatı alınmadı. Mövcud regionlar: Aran, Şəki-Zaqatala, Lənkəran, Abşeron, Gəncə-Qazax, Mil-Muğan, Şirvan, Quba-Xaçmaz"


@tool
def get_soil_analysis_tool(
    farm_id: Annotated[str, "Farm ID (e.g., 'scenario-wheat', 'scenario-vegetable')"]
) -> str:
    """
    Get soil analysis data for a farm including pH, moisture, and nutrient levels.
    Use this when the user asks about soil conditions, nutrients, or fertilization needs.
    """
    farms = get_scenario_farms()
    
    if farm_id not in farms:
        available = ", ".join(farms.keys())
        return f"Təsərrüfat tapılmadı. Mövcud təsərrüfatlar: {available}"
    
    farm = farms[farm_id]
    soil = farm.soil_data
    
    if not soil:
        return f"{farm.name} üçün torpaq məlumatı mövcud deyil."
    
    result = f"🌱 Torpaq Analizi - {farm.name}:\n\n"
    result += f"📍 Region: {farm.location.region}\n"
    result += f"🏷️ Torpaq tipi: {soil.soil_type.value}\n"
    result += f"💧 Nəmlik: {soil.moisture_percent}%\n"
    result += f"🧪 pH: {soil.ph_level}\n"
    result += f"🟢 Azot (N): {soil.nitrogen_level} kg/ha\n"
    result += f"🟠 Fosfor (P): {soil.phosphorus_level} kg/ha\n"
    result += f"🟡 Kalium (K): {soil.potassium_level} kg/ha\n"
    
    # Add interpretation
    issues = []
    if soil.moisture_percent < 30:
        issues.append("⚠️ Nəmlik aşağıdır - suvarma lazımdır")
    if soil.nitrogen_level < 30:
        issues.append("⚠️ Azot səviyyəsi aşağıdır")
    if soil.phosphorus_level < 25:
        issues.append("⚠️ Fosfor səviyyəsi aşağıdır")
    if soil.potassium_level < 100:
        issues.append("⚠️ Kalium səviyyəsi aşağıdır")
    if soil.ph_level < 5.5:
        issues.append("⚠️ pH çox turşudur - əhəng lazımdır")
    elif soil.ph_level > 7.5:
        issues.append("⚠️ pH çox qələvidir - kükürd lazımdır")
    
    if issues:
        result += "\n" + "\n".join(issues)
    else:
        result += "\n✅ Torpaq vəziyyəti yaxşıdır"
    
    return result


@tool
def get_irrigation_recommendation_tool(
    farm_id: Annotated[str, "Farm ID to get irrigation advice for"]
) -> str:
    """
    Get irrigation recommendations for a farm based on soil moisture and weather.
    Use this when the user asks about watering, irrigation, or suvarma.
    """
    farms = get_scenario_farms()
    
    if farm_id not in farms:
        return f"Təsərrüfat tapılmadı: {farm_id}"
    
    farm = farms[farm_id]
    
    if not farm.soil_data:
        return "Torpaq məlumatları mövcud deyil."
    
    soil = farm.soil_data
    weather = WeatherGenerator.generate(date.today(), farm.location.region, 1)[0]
    
    result = f"💧 Suvarma Tövsiyəsi - {farm.name}:\n\n"
    result += f"Cari torpaq nəmliyi: {soil.moisture_percent}%\n"
    result += f"Bu günkü hava: {weather.condition.value}, {weather.temperature_max}°C\n\n"
    
    if soil.moisture_percent < 30:
        result += "🔴 **TƏCİLİ SUVARMA LAZIMDIR**\n"
        result += "Torpaq nəmliyi kritik həddə çatıb. Bu gün səhər tezdən (6:00-8:00) suvarın.\n"
        if farm.irrigation_system:
            result += f"Tövsiyə: {farm.irrigation_system} sistemindən istifadə edin.\n"
    elif soil.moisture_percent < 45:
        if weather.condition.value in ["rainy", "stormy"]:
            result += "🟡 Suvarmanı TƏXİRƏ SALIN\n"
            result += f"Yağış gözlənilir ({weather.precipitation_mm}mm). Təbii suvarmanı gözləyin.\n"
        else:
            result += "🟡 1-2 gün ərzində suvarma planlaşdırın\n"
            result += "Nəmlik optimal aralığa yaxındır.\n"
    else:
        result += "🟢 Hazırda suvarma lazım deyil\n"
        result += f"Torpaq nəmliyi yaxşıdır ({soil.moisture_percent}%).\n"
        result += "3-4 gün sonra yenidən yoxlayın.\n"
    
    if weather.temperature_max > 35:
        result += "\n⚠️ **İSTİ XƏBƏRDARLIĞI**: Temperatur yüksəkdir. Suvarmanı səhər və ya axşam saatlarında edin."
    
    return result


@tool
def get_fertilization_recommendation_tool(
    farm_id: Annotated[str, "Farm ID to get fertilization advice for"]
) -> str:
    """
    Get fertilization recommendations based on soil nutrients and crop stage.
    Use this when the user asks about fertilizers, gübrə, nutrients, or soil feeding.
    """
    farms = get_scenario_farms()
    
    if farm_id not in farms:
        return f"Təsərrüfat tapılmadı: {farm_id}"
    
    farm = farms[farm_id]
    
    if not farm.soil_data:
        return "Torpaq məlumatları mövcud deyil."
    
    soil = farm.soil_data
    
    result = f"🌱 Gübrələmə Tövsiyəsi - {farm.name}:\n\n"
    result += f"**Cari torpaq vəziyyəti:**\n"
    result += f"- Azot: {soil.nitrogen_level} kg/ha {'🔴 Aşağı' if soil.nitrogen_level < 30 else '🟢 Normal'}\n"
    result += f"- Fosfor: {soil.phosphorus_level} kg/ha {'🔴 Aşağı' if soil.phosphorus_level < 25 else '🟢 Normal'}\n"
    result += f"- Kalium: {soil.potassium_level} kg/ha {'🔴 Aşağı' if soil.potassium_level < 100 else '🟢 Normal'}\n"
    result += f"- pH: {soil.ph_level}\n\n"
    
    recommendations = []
    
    if soil.nitrogen_level < 30:
        recommendations.append("🟢 **Azot gübrəsi tətbiq edin** (Karbamid və ya Ammonium Nitrat)")
        recommendations.append("   Dozaj: 150-200 kg/ha")
    
    if soil.phosphorus_level < 25:
        recommendations.append("🟠 **Fosfor gübrəsi tətbiq edin** (Superfosfat)")
        recommendations.append("   Dozaj: 100-150 kg/ha")
    
    if soil.potassium_level < 100:
        recommendations.append("🟡 **Kalium gübrəsi tətbiq edin** (Kalium Xlorid)")
        recommendations.append("   Dozaj: 100-150 kg/ha")
    
    if soil.ph_level < 5.5:
        recommendations.append("⚪ **Əhəng tətbiq edin** - pH çox aşağıdır")
    elif soil.ph_level > 7.5:
        recommendations.append("⚪ **Kükürd tətbiq edin** - pH çox yüksəkdir")
    
    if recommendations:
        result += "**Tövsiyələr:**\n" + "\n".join(recommendations)
    else:
        result += "✅ Hazırda gübrələmə lazım deyil. Torpaq qida maddələri ilə yaxşı təmin olunub."
    
    return result


@tool
def get_pest_alert_tool(
    farm_id: Annotated[str, "Farm ID to check for pest and disease risks"]
) -> str:
    """
    Get pest and disease risk alerts based on weather and crop conditions.
    Use this when the user asks about pests, diseases, xəstəlik, zərərverici, or plant health.
    """
    farms = get_scenario_farms()
    
    if farm_id not in farms:
        return f"Təsərrüfat tapılmadı: {farm_id}"
    
    farm = farms[farm_id]
    weather = WeatherGenerator.generate(date.today(), farm.location.region, 1)[0]
    
    result = f"🐛 Zərərverici və Xəstəlik Analizi - {farm.name}:\n\n"
    result += f"**Hava şəraiti:**\n"
    result += f"- Temperatur: {weather.temperature_min}°C - {weather.temperature_max}°C\n"
    result += f"- Rütubət: {weather.humidity_percent}%\n"
    result += f"- Şərait: {weather.condition.value}\n\n"
    
    risks = []
    
    if weather.humidity_percent > 75:
        risks.append({
            "level": "YÜKSƏK",
            "emoji": "🔴",
            "name": "Göbələk xəstəlikləri",
            "reason": f"Rütubət çox yüksəkdir ({weather.humidity_percent}%)",
            "action": "Bitkiləri fungisid ilə emal edin. Ventilyasiyanı yaxşılaşdırın."
        })
    
    if weather.temperature_max > 25 and weather.humidity_percent < 50:
        risks.append({
            "level": "ORTA",
            "emoji": "🟡",
            "name": "Mənənə (Aphid)",
            "reason": "İsti və quru hava mənənə üçün əlverişlidir",
            "action": "Bitki yarpaqlarının alt tərəfini yoxlayın. Lazım gəldikdə insektisid tətbiq edin."
        })
    
    if weather.precipitation_mm > 15:
        risks.append({
            "level": "ORTA",
            "emoji": "🟡",
            "name": "Yağışdan sonra xəstəliklər",
            "reason": f"Güclü yağış ({weather.precipitation_mm}mm) xəstəlik yayılmasına səbəb ola bilər",
            "action": "Yağışdan sonra bitkiləri diqqətlə yoxlayın."
        })
    
    if risks:
        result += "**Aşkar edilmiş risklər:**\n\n"
        for risk in risks:
            result += f"{risk['emoji']} **{risk['name']}** - Risk: {risk['level']}\n"
            result += f"   Səbəb: {risk['reason']}\n"
            result += f"   Tövsiyə: {risk['action']}\n\n"
    else:
        result += "✅ **Hazırda ciddi risk aşkar edilmədi**\n\n"
        result += "Profilaktik tövsiyələr:\n"
        result += "- Həftədə bir dəfə bitkiləri yoxlayın\n"
        result += "- Yarpaq rəngini və formasını izləyin\n"
        result += "- Hava dəyişikliklərini izləyin\n"
    
    return result


@tool
def get_harvest_timing_tool(
    farm_id: Annotated[str, "Farm ID to check harvest readiness"]
) -> str:
    """
    Get harvest timing recommendations based on crop maturity.
    Use this when the user asks about harvest, məhsul yığımı, or when crops are ready.
    """
    farms = get_scenario_farms()
    
    if farm_id not in farms:
        return f"Təsərrüfat tapılmadı: {farm_id}"
    
    farm = farms[farm_id]
    
    if not farm.crops:
        return f"{farm.name} - Əkin məlumatları mövcud deyil."
    
    weather = WeatherGenerator.generate(date.today(), farm.location.region, 3)
    
    result = f"🌾 Məhsul Yığımı Statusu - {farm.name}:\n\n"
    
    from yonca.models import CropStage
    
    for crop in farm.crops:
        days_to_harvest = (crop.expected_harvest_date - date.today()).days if crop.expected_harvest_date else None
        
        result += f"**{crop.crop_type.capitalize()}** ({crop.variety})\n"
        result += f"   Sahə: {crop.area_hectares} ha\n"
        result += f"   Mərhələ: {crop.current_stage.value}\n"
        
        if crop.current_stage == CropStage.MATURITY:
            result += "   Status: 🟢 **YETİŞİB - Yığıma hazırdır!**\n"
            
            # Check weather
            bad_weather = any(w.condition.value in ["rainy", "stormy"] for w in weather)
            if bad_weather:
                result += "   ⚠️ Yağışlı hava gözlənilir - TƏCİLİ yığın!\n"
            else:
                result += "   ✅ Hava yaxşıdır - optimal yığım şəraiti\n"
        
        elif crop.current_stage == CropStage.HARVEST:
            result += "   Status: 🟢 **Yığım mərhələsində**\n"
        
        elif days_to_harvest and days_to_harvest <= 7:
            result += f"   Status: 🟡 ~{days_to_harvest} gün qalıb\n"
        
        elif days_to_harvest:
            result += f"   Status: ⏳ {days_to_harvest} gün sonra ({crop.expected_harvest_date})\n"
        
        result += "\n"
    
    return result


@tool
def get_livestock_health_tool(
    farm_id: Annotated[str, "Farm ID to check livestock status"]
) -> str:
    """
    Get livestock health status and care recommendations.
    Use this when the user asks about animals, heyvanlar, vaccination, peyvənd, or livestock care.
    """
    farms = get_scenario_farms()
    
    if farm_id not in farms:
        return f"Təsərrüfat tapılmadı: {farm_id}"
    
    farm = farms[farm_id]
    
    if not farm.livestock:
        return f"{farm.name} - Heyvandarlıq məlumatları mövcud deyil."
    
    weather = WeatherGenerator.generate(date.today(), farm.location.region, 1)[0]
    
    result = f"🐄 Heyvandarlıq Statusu - {farm.name}:\n\n"
    
    for animal in farm.livestock:
        result += f"**{animal.livestock_type.value.capitalize()}**\n"
        result += f"   Sayı: {animal.count} baş\n"
        result += f"   Orta yaş: {animal.average_age_months} ay\n"
        result += f"   Sağlamlıq: {animal.health_status}\n"
        
        if animal.last_vaccination_date:
            days_since = (date.today() - animal.last_vaccination_date).days
            if days_since > 180:
                result += f"   ⚠️ **Peyvənd gecikib!** Son peyvənd: {days_since} gün əvvəl\n"
            else:
                result += f"   ✅ Son peyvənd: {days_since} gün əvvəl\n"
        
        result += "\n"
    
    # Weather-based alerts
    result += "**Hava əsaslı tövsiyələr:**\n"
    
    if weather.temperature_max > 32:
        result += f"🔴 **İSTİ STRESI RİSKİ** - Temperatur {weather.temperature_max}°C\n"
        result += "   - Kölgəlik təmin edin\n"
        result += "   - Əlavə su verin\n"
        result += "   - Günorta saatlarında heyvanları içəri alın\n"
    elif weather.temperature_min < 5:
        result += f"🔵 **SOYUQ XƏBƏRDARLIĞI** - Temperatur {weather.temperature_min}°C-yə düşə bilər\n"
        result += "   - Sığınacaq şəraitini yoxlayın\n"
        result += "   - Küləkdən qoruyun\n"
        result += "   - Yemləməni artırın\n"
    else:
        result += "✅ Hava şəraiti heyvandarlıq üçün əlverişlidir\n"
    
    return result


@tool
def get_daily_schedule_tool(
    farm_id: Annotated[str, "Farm ID to generate daily schedule for"]
) -> str:
    """
    Get the complete daily schedule with all tasks and alerts for a farm.
    Use this when the user asks about today's plan, what to do, gündəlik plan, or cədvəl.
    """
    farms = get_scenario_farms()
    
    if farm_id not in farms:
        available = ", ".join(farms.keys())
        return f"Təsərrüfat tapılmadı. Mövcud: {available}"
    
    farm = farms[farm_id]
    schedule = generate_daily_schedule(farm)
    
    result = f"📋 Gündəlik Plan - {farm.name}\n"
    result += f"📅 Tarix: {date.today()}\n\n"
    
    if schedule.weather_forecast:
        w = schedule.weather_forecast
        emoji = {"sunny": "☀️", "cloudy": "☁️", "rainy": "🌧️", "stormy": "⛈️"}.get(w.condition.value, "🌤️")
        result += f"**Hava:** {emoji} {w.temperature_min}°C - {w.temperature_max}°C, Rütubət: {w.humidity_percent}%\n\n"
    
    if schedule.alerts:
        result += "**⚠️ Xəbərdarlıqlar:**\n"
        for alert in schedule.alerts[:3]:
            severity_emoji = {"critical": "🔴", "warning": "🟡", "info": "🔵"}.get(alert.severity.value, "⚪")
            result += f"{severity_emoji} {alert.title_az}\n"
        result += "\n"
    
    if schedule.tasks:
        result += "**📝 Bu günkü tapşırıqlar:**\n"
        priority_emoji = {"critical": "🔴", "high": "🟠", "medium": "🟡", "low": "🟢"}
        
        for i, task in enumerate(schedule.tasks[:7], 1):
            emoji = priority_emoji.get(task.priority.value, "⚪")
            result += f"{i}. {emoji} {task.title_az}\n"
            result += f"   ⏱️ ~{task.estimated_duration_minutes} dəqiqə\n"
    else:
        result += "✅ Bu gün üçün planlaşdırılmış tapşırıq yoxdur.\n"
    
    return result


# Export all tools as a list
ALL_TOOLS = [
    get_weather_tool,
    get_soil_analysis_tool,
    get_irrigation_recommendation_tool,
    get_fertilization_recommendation_tool,
    get_pest_alert_tool,
    get_harvest_timing_tool,
    get_livestock_health_tool,
    get_daily_schedule_tool,
]

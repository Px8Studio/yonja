# demo-ui/components/farm_selector.py
"""Farm selector component using Chainlit ChatSettings."""

import chainlit as cl
from chainlit.input_widget import Select

from services.mock_data import MockDataService, get_demo_farm_by_id

# Localized strings
AZ_STRINGS = {
    "farm_label": "Təsərrüfat seçin",
    "farm_loaded": "📍 **Təsərrüfat dəyişdirildi:** {farm_name}",
    "farm_details": """
📍 **Təsərrüfat:** {name}
👤 **Sahibi:** {owner}
🌱 **Əkin:** {crop}
📐 **Sahə:** {area_ha} hektar
🏔️ **Rayon:** {district}, {region}
🌍 **Torpaq:** {soil_type}
💧 **Suvarma:** {irrigation_type}
📊 **NDVI:** {ndvi}
""",
}


async def create_farm_settings() -> list:
    """Create the farm selector settings widget.
    
    Returns:
        List of ChatSettings widgets.
    """
    mock_data = MockDataService()
    farm_options = mock_data.get_farm_selector_options()
    
    # Create Select widget with farm options
    return [
        Select(
            id="farm_id",
            label=AZ_STRINGS["farm_label"],
            values=[opt["value"] for opt in farm_options],
            initial_value=farm_options[0]["value"] if farm_options else None,
        ),
    ]


async def handle_farm_change(settings: dict) -> dict | None:
    """Handle farm selection change.
    
    Args:
        settings: The updated settings dictionary.
        
    Returns:
        The selected farm context or None.
    """
    farm_id = settings.get("farm_id")
    if not farm_id:
        return None
    
    farm = get_demo_farm_by_id(farm_id)
    if not farm:
        return None
    
    # Format NDVI for display
    ndvi_display = f"{farm['last_ndvi']:.2f}" if farm.get("last_ndvi") else "N/A"
    
    # Send farm context message
    details = AZ_STRINGS["farm_details"].format(
        name=farm["name"],
        owner=farm["owner"],
        crop=farm["crop"],
        area_ha=farm["area_ha"],
        district=farm["district"],
        region=farm["region"],
        soil_type=farm["soil_type"],
        irrigation_type=farm["irrigation_type"],
        ndvi=ndvi_display,
    )
    
    await cl.Message(
        content=AZ_STRINGS["farm_loaded"].format(farm_name=farm["name"]) + "\n" + details,
        author="Sistem",
    ).send()
    
    return farm


def format_farm_context_for_prompt(farm: dict) -> str:
    """Format farm context for inclusion in LLM prompts.
    
    Args:
        farm: Farm dictionary.
        
    Returns:
        Formatted context string.
    """
    return f"""Fermerin təsərrüfat məlumatları:
- Təsərrüfat adı: {farm["name"]}
- Rayon: {farm["district"]}, {farm["region"]} bölgəsi
- Əkin növü: {farm["crop"]}
- Sahə: {farm["area_ha"]} hektar
- Torpaq tipi: {farm["soil_type"]}
- Suvarma sistemi: {farm["irrigation_type"]}
- NDVI (bitki sağlamlığı): {farm.get("last_ndvi", "məlum deyil")}
- Təcrübə: {farm["experience_years"]} il"""

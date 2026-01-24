from constants import CROP_TO_EXPERTISE, EXPERIENCE_TO_EXPERTISE, PROFILE_PROMPTS


def detect_expertise_from_persona(persona_dict: dict | None) -> list[str]:
    """Detect relevant expertise areas from ALİM persona.

    Uses crop type and experience level to determine smart defaults.

    Args:
        persona_dict: ALİM persona dictionary with crop_type, experience_level

    Returns:
        List of expertise area IDs (e.g., ["cotton", "advanced"])
    """
    if not persona_dict:
        return ["general"]

    expertise = set()

    # Add expertise based on crop type
    crop_type = persona_dict.get("crop_type", "")
    if crop_type in CROP_TO_EXPERTISE:
        expertise.update(CROP_TO_EXPERTISE[crop_type])

    # Add expertise based on experience level
    experience = persona_dict.get("experience_level", "intermediate")
    if experience in EXPERIENCE_TO_EXPERTISE:
        expertise.update(EXPERIENCE_TO_EXPERTISE[experience])

    # Always include general if nothing specific detected
    if not expertise:
        expertise.add("general")

    # Sort for consistent ordering
    return sorted(list(expertise))


def build_combined_system_prompt(expertise_areas: list[str]) -> str:
    """Build combined system prompt from multiple expertise areas.

    Args:
        expertise_areas: List of selected expertise area IDs

    Returns:
        Combined system prompt string
    """
    if not expertise_areas:
        return ""

    prompts = []
    for area in expertise_areas:
        if area in PROFILE_PROMPTS and PROFILE_PROMPTS[area]:
            prompts.append(PROFILE_PROMPTS[area].strip())

    if not prompts:
        return ""

    # Combine with header
    combined = """
Sən çoxsahəli kənd təsərrüfatı ekspertisən. Aşağıdakı sahələrdə ixtisaslaşmısan:

""" + "\n\n".join(prompts)

    return combined

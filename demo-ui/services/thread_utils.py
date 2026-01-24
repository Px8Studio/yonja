import logging

import chainlit as cl
from data_layer import get_data_layer

logger = logging.getLogger(__name__)


def build_thread_name(
    crop_type: str | None, region: str | None, planning_month: str | None = None
) -> str:
    """Generate a human-friendly thread name for the sidebar."""
    parts = []
    if crop_type:
        parts.append(crop_type)
    if region:
        parts.append(region)
    if planning_month:
        parts.append(planning_month)
    return " • ".join(parts) if parts else "Yeni söhbət"


def build_thread_tags(
    crop_type: str | None,
    region: str | None,
    expertise_ids: list[str] | None,
    action_categories: list[str] | None = None,
    experience_level: str | None = None,
    interaction_mode: str | None = None,
    llm_model: str | None = None,
) -> list[str]:
    """Produce sidebar tags so users can filter threads."""
    tags: list[str] = []
    if crop_type:
        tags.append(crop_type)
    if region:
        tags.append(region)
    if experience_level:
        tags.append(f"experience:{experience_level}")
    if expertise_ids:
        tags.extend(expertise_ids)
    if action_categories:
        tags.extend([f"plan:{cat}" for cat in action_categories])
    if interaction_mode:
        tags.append(f"mode:{interaction_mode.lower()}")
    if llm_model:
        tags.append(f"model:{llm_model}")
    # Deduplicate while keeping order
    seen = set()
    unique = []
    for tag in tags:
        if tag not in seen:
            unique.append(tag)
            seen.add(tag)
    return unique


async def update_thread_presentation(
    name: str | None,
    tags: list[str] | None,
    metadata_updates: dict | None = None,
):
    """Persist thread name/tags/metadata so the sidebar shows rich info."""
    data_layer = get_data_layer()
    thread_id = cl.user_session.get("thread_id")

    if not data_layer or not thread_id:
        return

    metadata = (cl.user_session.get("thread_metadata") or {}).copy()
    if metadata_updates:
        metadata.update(metadata_updates)

    # Keep metadata in session and push to DB
    cl.user_session.set("thread_metadata", metadata)

    try:
        # Use correct method signature: update_thread(thread_id, name, user_id, metadata, tags)
        # Tags should be a list - the data layer handles JSON serialization
        await data_layer.update_thread(
            thread_id=thread_id,
            name=name,
            metadata=metadata,
            tags=tags,  # Pass as list, not serialized
        )
        logger.debug("thread_presentation_updated", thread_id=thread_id, name=name, tags=tags)
    except Exception as e:  # noqa: BLE001
        logger.warning("thread_presentation_update_failed", thread_id=thread_id, error=str(e))

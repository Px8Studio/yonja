# demo-ui/services/lifecycle.py
"""Lifecycle handlers for chat session management.

This module contains the core logic for:
- on_chat_start: Session initialization, persona loading, MCP setup
- on_chat_resume: Thread restoration after browser refresh
- on_shared_thread_view: Shared thread access control

The actual @cl decorators remain in app.py for Chainlit registration,
but delegate to these handlers for logic.
"""

from __future__ import annotations

import json
import os
from typing import TYPE_CHECKING

import chainlit as cl
from alim_persona import ALİMPersona, PersonaProvisioner
from alim_persona_db import (
    load_alim_persona_from_db,
    save_alim_persona_to_db,
    update_persona_login_time,
)
from chainlit.types import ThreadDict
from config import settings as demo_settings
from constants import AgentMode

from services.expertise import build_combined_system_prompt, detect_expertise_from_persona
from services.logger import get_logger
from services.mcp_connector import format_mcp_status, get_mcp_status
from services.mcp_resilience import get_mcp_manager, initialize_mcp
from services.model_resolver import resolve_active_model
from services.session_manager import SessionManager, initialize_session_with_persistence
from services.thread_utils import build_thread_name, build_thread_tags, update_thread_presentation

if TYPE_CHECKING:
    pass

# Initialize logger
logger = get_logger(__name__)


async def handle_chat_start(
    user: cl.User | None,
    session_id: str,
    get_data_layer_fn: callable,
    setup_chat_settings_fn: callable,
    send_dashboard_welcome_fn: callable,
) -> None:
    """Core logic for on_chat_start handler.

    Args:
        user: Authenticated user from OAuth (or None)
        session_id: Chainlit session ID
        get_data_layer_fn: Function to get data layer (avoid circular import)
        setup_chat_settings_fn: Function to setup chat settings
        send_dashboard_welcome_fn: Function to send welcome message
    """
    user_id = user.identifier if user else "anonymous"
    user_email = user.metadata.get("email") if user and user.metadata else None

    # ─────────────────────────────────────────────────────────────
    # ENSURE USER IS PERSISTED TO DB (CRITICAL!)
    # ─────────────────────────────────────────────────────────────
    if user:
        from data_layer import ensure_user_persisted

        user_persisted = await ensure_user_persisted(user)
        if not user_persisted:
            logger.warning("user_not_persisted_continuing_anyway", user_id=user_id)

    # ─────────────────────────────────────────────────────────────
    # JIT PERSONA PROVISIONING
    # ─────────────────────────────────────────────────────────────
    alim_persona: ALİMPersona | None = None

    if user and user.metadata:
        oauth_claims = {
            "name": user.metadata.get("name", "Unknown Farmer"),
            "email": user.metadata.get("email", user_email),
        }

        existing_persona_dict = await load_alim_persona_from_db(email=user_email)

        if existing_persona_dict:
            alim_persona = ALİMPersona(
                user_id=user_id,
                full_name=existing_persona_dict["full_name"],
                email=existing_persona_dict["email"],
                fin_code=existing_persona_dict["fin_code"],
                phone=existing_persona_dict["phone"],
                region=existing_persona_dict["region"],
                crop_type=existing_persona_dict["crop_type"],
                total_area_ha=existing_persona_dict["total_area_ha"],
                experience_level=existing_persona_dict["experience_level"],
                ektis_verified=existing_persona_dict["ektis_verified"],
            )
            await update_persona_login_time(email=user_email)
            logger.info(
                "persona_loaded_from_db",
                user_id=user_id,
                fin_code=alim_persona.fin_code,
                region=alim_persona.region,
            )
        else:
            alim_persona = PersonaProvisioner.provision_from_oauth(
                user_id=user_id,
                oauth_claims=oauth_claims,
                existing_persona=None,
            )
            await save_alim_persona_to_db(
                alim_persona=alim_persona.to_dict(),
                chainlit_user_id=user_id,
                email=user_email,
            )
            logger.info(
                "persona_generated_and_saved",
                user_id=user_id,
                fin_code=alim_persona.fin_code,
                region=alim_persona.region,
            )

        cl.user_session.set("alim_persona", alim_persona.to_dict())
        logger.info(
            "alim_persona_provisioned",
            user_id=user_id,
            fin_code=alim_persona.fin_code,
            region=alim_persona.region,
            crop_type=alim_persona.crop_type,
        )
    else:
        logger.debug("no_authenticated_user_skipping_persona")

    # ─────────────────────────────────────────────────────────────
    # SMART EXPERTISE DETECTION
    # ─────────────────────────────────────────────────────────────
    alim_persona_dict = cl.user_session.get("alim_persona")
    default_expertise = detect_expertise_from_persona(alim_persona_dict)
    profile_prompt = build_combined_system_prompt(default_expertise)

    logger.info(
        "expertise_detected",
        default_expertise=default_expertise,
        has_prompt=bool(profile_prompt),
    )

    # Store session info
    cl.user_session.set("user_id", user_id)
    cl.user_session.set("user_email", user_email)
    cl.user_session.set("profile_prompt", profile_prompt)
    cl.user_session.set("expertise_areas", default_expertise)
    cl.user_session.set("interaction_mode", "Ask")
    cl.user_session.set("llm_model", demo_settings.ollama_model)
    cl.user_session.set("data_consent_given", False)
    cl.user_session.set("consent_prompt_shown", False)

    persona_crop = (
        alim_persona.crop_type
        if alim_persona
        else (alim_persona_dict.get("crop_type") if alim_persona_dict else None)
    )
    persona_region = (
        alim_persona.region
        if alim_persona
        else (alim_persona_dict.get("region") if alim_persona_dict else None)
    )

    logger.info(
        "expertise_configured",
        expertise=default_expertise,
        user_id=user_id,
        has_custom_prompt=bool(profile_prompt),
    )

    # Default farm for demo
    farm_id = "demo_farm_001"
    cl.user_session.set("farm_id", farm_id)
    cl.user_session.set("thread_id", session_id)

    # ═══════════════════════════════════════════════════════════════
    # SESSION PERSISTENCE
    # ═══════════════════════════════════════════════════════════════
    if user and user_email:
        await initialize_session_with_persistence(user_id, user_email)

        persisted_farm = SessionManager.get_session_state("farm_id")
        if persisted_farm:
            farm_id = persisted_farm
            cl.user_session.set("farm_id", farm_id)
            logger.info("farm_restored_from_persistence", farm_id=farm_id)

    # Initialize Chat Settings
    user_settings = await setup_chat_settings_fn(user=user)
    cl.user_session.set("user_preferences", user_settings)

    # Active model
    active_model = resolve_active_model()
    cl.user_session.set("active_model", active_model)
    logger.debug(
        "active_model_configured",
        provider=active_model.get("provider"),
        model=active_model.get("model"),
        location=active_model.get("location"),
    )

    logger.info(
        "session_started_http_mode",
        session_id=session_id,
        user_id=user_id,
        farm_id=farm_id,
        langgraph_server=demo_settings.langgraph_base_url,
    )

    # ─────────────────────────────────────────────────────────────
    # THREAD METADATA PERSISTENCE
    # ─────────────────────────────────────────────────────────────
    data_layer = get_data_layer_fn()
    if data_layer and user:
        try:
            thread_metadata = {
                "farm_id": farm_id,
                "expertise_areas": default_expertise,
                "alim_persona_fin": alim_persona_dict.get("fin_code")
                if alim_persona_dict
                else None,
                "language": "az",
                "active_model": active_model,
                "interaction_mode": "Ask",
                "llm_model": demo_settings.ollama_model,
            }
            cl.user_session.set("thread_metadata", thread_metadata)
            logger.debug("thread_metadata_prepared", metadata_keys=list(thread_metadata.keys()))
        except Exception as e:
            logger.warning("thread_metadata_preparation_failed", error=str(e))

    # Persist initial name/tags
    await update_thread_presentation(
        name=build_thread_name(persona_crop, persona_region, None),
        tags=build_thread_tags(
            persona_crop,
            persona_region,
            default_expertise,
            interaction_mode="Ask",
            llm_model=demo_settings.ollama_model,
        ),
        metadata_updates={
            **(cl.user_session.get("thread_metadata") or {}),
            "is_shared": False,
            "shared_at": None,
            "interaction_mode": "Ask",
            "llm_model": demo_settings.ollama_model,
        },
    )

    # ─────────────────────────────────────────────────────────────
    # MCP CONNECTION INITIALIZATION
    # ─────────────────────────────────────────────────────────────
    mcp_url = os.getenv("ZEKALAB_MCP_URL", "http://localhost:7777")
    agent_mcp_status = None

    try:
        mcp_initialized = await initialize_mcp(mcp_url=mcp_url)

        if mcp_initialized:
            logger.info("mcp_resilience_initialized", url=mcp_url)
        else:
            logger.warning("mcp_resilience_unavailable", url=mcp_url)

        agent_mcp_status = await get_mcp_status(profile=AgentMode.AGENT.value)
        mcp_manager_status = get_mcp_manager(mcp_url).get_status()

        cl.user_session.set("mcp_status", agent_mcp_status)
        cl.user_session.set("mcp_manager_status", mcp_manager_status)
        cl.user_session.set("mcp_enabled", agent_mcp_status.get("connectors_enabled", False))

        logger.info(
            "mcp_initialized",
            profile=AgentMode.AGENT.value,
            servers=list(agent_mcp_status.get("servers", {}).keys()),
            tool_count=agent_mcp_status.get("tool_count", 0),
            mcp_available=mcp_manager_status.get("available", False),
        )

        # Display MCP status in UI
        formatted_status = format_mcp_status(agent_mcp_status)
        await cl.Message(content=formatted_status, author="System").send()

        offline_servers = [
            name
            for name, info in agent_mcp_status.get("servers", {}).items()
            if info.get("status") != "online"
        ]

        if offline_servers:
            cl.user_session.set("mcp_offline_warned", True)
            await cl.Message(
                content=f"⚠️ MCP offline: {', '.join(offline_servers)}. Agent tools limited until restored.",
                author="System",
            ).send()

        if not agent_mcp_status.get("connectors_enabled"):
            await cl.Message(
                content="🔒 MCP connectors disabled for this mode. Switch to Agent to enable tools.",
                author="System",
            ).send()

    except Exception as e:
        logger.warning("mcp_initialization_error", error=str(e), exc_info=True)
        cl.user_session.set("mcp_enabled", False)

    # ─────────────────────────────────────────────────────────────
    # WELCOME MESSAGE
    # ─────────────────────────────────────────────────────────────
    await send_dashboard_welcome_fn(user, mcp_status=agent_mcp_status)


async def handle_chat_resume(
    thread: ThreadDict,
    get_app_checkpointer_fn: callable,
    compile_agent_graph_fn: callable,
    setup_chat_settings_fn: callable,
) -> None:
    """Core logic for on_chat_resume handler.

    Args:
        thread: Thread dict with id, name, userId, metadata, tags
        get_app_checkpointer_fn: Function to get checkpointer
        compile_agent_graph_fn: Function to compile agent graph
        setup_chat_settings_fn: Function to setup chat settings
    """
    logger.info(
        "thread_resumed",
        thread_id=thread["id"],
        user_id=thread.get("userId"),
        thread_name=thread.get("name"),
    )

    # 1. Get authenticated user
    user: cl.User | None = cl.user_session.get("user")
    user_id = user.identifier if user else thread.get("userId", "anonymous")
    user_email = user.metadata.get("email") if user and user.metadata else None

    # 2. Restore session variables from thread metadata
    metadata = thread.get("metadata", {})
    if isinstance(metadata, str):
        try:
            metadata = json.loads(metadata) if metadata.strip() else {}
        except Exception:
            metadata = {}

    cl.user_session.set("thread_id", thread["id"])
    cl.user_session.set("user_id", user_id)
    cl.user_session.set("user_email", user_email)
    cl.user_session.set("farm_id", metadata.get("farm_id", "demo_farm_001"))

    # 3. Restore ALİM persona
    if user and user_email:
        existing_persona_dict = await load_alim_persona_from_db(email=user_email)
        if existing_persona_dict:
            cl.user_session.set("alim_persona", existing_persona_dict)
            await update_persona_login_time(email=user_email)
            logger.info("persona_restored", fin_code=existing_persona_dict.get("fin_code"))
        else:
            logger.warning("persona_not_found_on_resume", email=user_email)

    # 4. Restore chat settings
    from data_layer import load_farm_scenario, load_user_settings

    user_settings = await load_user_settings(user)
    cl.user_session.set("user_preferences", user_settings)

    # 5. Restore farm scenario
    scenario = await load_farm_scenario(user_id=user_id, thread_id=thread["id"])
    if scenario:
        cl.user_session.set("scenario_context", scenario)
        cl.user_session.set("settings_version", scenario.get("settings_version", 1))
        logger.info(
            "scenario_restored",
            crop=scenario.get("specific_crop"),
            stage=scenario.get("conversation_stage"),
        )

    # 6. Restore expertise areas
    alim_persona_dict = cl.user_session.get("alim_persona")
    expertise = metadata.get("expertise_areas")
    if not expertise and alim_persona_dict:
        expertise = detect_expertise_from_persona(alim_persona_dict)
    if not expertise:
        expertise = ["general"]
    cl.user_session.set("expertise_areas", expertise)

    # Build system prompt
    profile_prompt = build_combined_system_prompt(expertise)
    cl.user_session.set("profile_prompt", profile_prompt)

    # 7. Active model
    active_model = resolve_active_model()
    cl.user_session.set("active_model", active_model)

    # 8. Reinitialize LangGraph agent
    checkpointer = await get_app_checkpointer_fn()
    agent = compile_agent_graph_fn(checkpointer=checkpointer)
    cl.user_session.set("agent", agent)

    # 9. Restore chat settings UI
    await setup_chat_settings_fn(user=user)

    logger.info(
        "thread_resume_complete",
        thread_id=thread["id"],
        user_id=user_id,
        has_persona=bool(alim_persona_dict),
        has_settings=bool(user_settings),
        has_scenario=bool(scenario),
        expertise=expertise,
    )

    # 10. Send resume indicator
    await cl.Message(
        content="🔄 Söhbət bərpa olundu. Sualınızı davam etdirə bilərsiniz.",
        author="system",
    ).send()


async def handle_shared_thread_view(thread: ThreadDict, viewer: cl.User | None) -> bool:
    """Core logic for on_shared_thread_view handler.

    Args:
        thread: Thread being viewed
        viewer: User viewing the shared thread (or None)

    Returns:
        True to allow viewing, False to deny
    """
    viewer_id = viewer.identifier if viewer else "anonymous"
    metadata = thread.get("metadata", {}) or {}
    if isinstance(metadata, str):
        try:
            metadata = json.loads(metadata) if metadata.strip() else {}
        except Exception:
            metadata = {}

    logger.info(
        "shared_thread_view",
        thread_id=thread.get("id"),
        owner_id=thread.get("userId"),
        viewer_id=viewer_id,
        is_shared=metadata.get("is_shared"),
    )

    # Placeholder policy: always allow
    return True

# demo-ui/alem_persona_db.py
"""Database persistence functions for ALEM Personas.

These functions handle loading and saving ALEM persona data to the
alem_personas PostgreSQL table for session persistence.
"""

import uuid
from datetime import datetime
from typing import Any

import structlog
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine
from yonca.data.database import get_db_session

logger = structlog.get_logger(__name__)

_engine: AsyncEngine | None = None


async def load_alem_persona_from_db(
    email: str,
) -> dict[str, Any] | None:
    """Load persona from database by email.

    Args:
        email: User email (from OAuth)

    Returns:
        Dict with persona data if found, None otherwise
    """
    try:
        async with get_db_session() as session:
            result = await session.execute(
                text(
                    """
                    SELECT alem_persona_id, email, full_name, fin_code, phone,
                           region, crop_type, total_area_ha, experience_level,
                           ektis_verified, data_source, created_at, last_login_at
                    FROM alem_personas
                    WHERE email = :email
                """
                ),
                {"email": email},
            )
            row = result.fetchone()

            if row:
                logger.info("persona_loaded_from_db", email=email, fin_code=row[3])
                return {
                    "alem_persona_id": row[0],
                    "email": row[1],
                    "full_name": row[2],
                    "fin_code": row[3],
                    "phone": row[4],
                    "region": row[5],
                    "crop_type": row[6],
                    "total_area_ha": row[7],
                    "experience_level": row[8],
                    "ektis_verified": row[9],
                    "data_source": row[10],
                    "created_at": row[11].isoformat() if row[11] else None,
                    "last_login_at": row[12].isoformat() if row[12] else None,
                }
            else:
                logger.debug("persona_not_found_in_db", email=email)
                return None

    except Exception as e:
        logger.error("load_persona_failed", email=email, error=str(e))
        return None


async def save_alem_persona_to_db(
    alem_persona: dict,
    chainlit_user_id: str,
    email: str,
    user_profile_id: str | None = None,
) -> bool:
    """Save generated persona to database for persistence."""
    try:
        async with get_db_session() as session:
            # Ensure FK uses users.id (UUID), not the email identifier
            if not chainlit_user_id or "-" not in chainlit_user_id:
                result = await session.execute(
                    text('SELECT "id" FROM users WHERE "identifier" = :identifier'),
                    {"identifier": email},
                )
                row = result.first()
                if row:
                    chainlit_user_id = row[0]
                else:
                    chainlit_user_id = str(uuid.uuid4())
                    await session.execute(
                        text(
                            'INSERT INTO users ("id", "identifier", "createdAt", "metadata") '
                            "VALUES (:id, :identifier, :created_at, :metadata)"
                        ),
                        {
                            "id": chainlit_user_id,
                            "identifier": email,
                            "created_at": datetime.utcnow().isoformat(),
                            "metadata": "{}",
                        },
                    )

            persona_id = str(uuid.uuid4())
            await session.execute(
                text(
                    """
                    INSERT INTO alem_personas (
                        alem_persona_id, chainlit_user_id, email, user_profile_id,
                        full_name, fin_code, phone, region, crop_type, total_area_ha,
                        experience_level, ektis_verified, data_source, created_at, last_login_at
                    ) VALUES (
                        :persona_id, :user_id, :email, :profile_id,
                        :name, :fin, :phone, :region, :crop, :area,
                        :exp, :verified, :source, :created, :login
                    )
                    ON CONFLICT (email) DO UPDATE SET
                        last_login_at = :login,
                        updated_at = CURRENT_TIMESTAMP
                """
                ),
                {
                    "persona_id": persona_id,
                    "user_id": chainlit_user_id,
                    "email": email,
                    "profile_id": user_profile_id,
                    "name": alem_persona["full_name"],
                    "fin": alem_persona["fin_code"],
                    "phone": alem_persona["phone"],
                    "region": alem_persona["region"],
                    "crop": alem_persona["crop_type"],
                    "area": alem_persona["total_area_ha"],
                    "exp": alem_persona["experience_level"],
                    "verified": alem_persona.get("ektis_verified", False),
                    "source": alem_persona.get("data_source", "synthetic"),
                    "created": datetime.utcnow(),
                    "login": datetime.utcnow(),
                },
            )
            await session.commit()
            logger.info("persona_saved_to_db", email=email, persona_id=persona_id)
            return True
    except Exception as e:
        logger.error("save_persona_failed", email=email, error=str(e))
        return False


async def update_persona_login_time(email: str) -> bool:
    """Update last_login_at timestamp for existing persona.

    Args:
        email: User email

    Returns:
        True if updated successfully
    """
    try:
        async with get_db_session() as session:
            await session.execute(
                text(
                    """
                    UPDATE alem_personas
                    SET last_login_at = :login_time,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE email = :email
                """
                ),
                {
                    "email": email,
                    "login_time": datetime.utcnow(),
                },
            )
            logger.debug("persona_login_updated", email=email)
            return True

    except Exception as e:
        logger.error("update_login_failed", email=email, error=str(e))
        return False


async def get_alem_persona_by_chainlit_user(chainlit_user_id: str) -> dict | None:
    """Get persona data by Chainlit user ID.

    Args:
        chainlit_user_id: Chainlit user identifier (email from OAuth)

    Returns:
        Dict with persona data if found, None otherwise
    """
    try:
        async with get_db_session() as session:
            result = await session.execute(
                text(
                    """
                    SELECT alem_persona_id, email, full_name, fin_code, phone,
                           region, crop_type, total_area_ha, experience_level,
                           ektis_verified, data_source, created_at, last_login_at
                    FROM alem_personas
                    WHERE chainlit_user_id = :user_id
                """
                ),
                {"user_id": chainlit_user_id},
            )
            row = result.fetchone()

            if row:
                logger.info(
                    "persona_loaded_from_db_by_user_id", user_id=chainlit_user_id, fin_code=row[3]
                )
                return {
                    "alem_persona_id": row[0],
                    "email": row[1],
                    "full_name": row[2],
                    "fin_code": row[3],
                    "phone": row[4],
                    "region": row[5],
                    "crop_type": row[6],
                    "total_area_ha": row[7],
                    "experience_level": row[8],
                    "ektis_verified": row[9],
                    "data_source": row[10],
                    "created_at": row[11].isoformat() if row[11] else None,
                    "last_login_at": row[12].isoformat() if row[12] else None,
                }
            else:
                logger.debug("persona_not_found_in_db_by_user_id", user_id=chainlit_user_id)
                return None

    except Exception as e:
        logger.error("load_persona_failed_by_user_id", user_id=chainlit_user_id, error=str(e))
        return None

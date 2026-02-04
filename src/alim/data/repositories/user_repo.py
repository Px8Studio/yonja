# src/ALİM/data/repositories/user_repo.py
"""User repository for user profile operations."""

from collections.abc import Sequence

from alim.data.models.user import ExperienceLevel, UserProfile
from alim.data.repositories.base import BaseRepository
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload


class UserRepository(BaseRepository[UserProfile]):
    """Repository for UserProfile operations.

    Extends BaseRepository with user-specific queries:
    - get_with_farms: Load user with all farms eagerly
    - get_by_region: Filter users by region
    - get_by_experience: Filter users by experience level
    - get_context_for_ai: Get user context for AI personalization
    """

    def __init__(self, session: AsyncSession):
        """Initialize user repository."""
        super().__init__(session, UserProfile)

    async def get_with_farms(self, user_id: str) -> UserProfile | None:
        """Get user with all farms eagerly loaded.

        Args:
            user_id: User ID

        Returns:
            User with farms loaded, or None if not found
        """
        query = (
            select(UserProfile)
            .options(selectinload(UserProfile.farms))
            .where(UserProfile.user_id == user_id)
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_by_region(self, region_code: str) -> Sequence[UserProfile]:
        """Get all users in a region.

        Args:
            region_code: ISO region code (e.g., AZ-ARN)

        Returns:
            Sequence of users in the region
        """
        query = select(UserProfile).where(UserProfile.region_code == region_code)
        result = await self.session.execute(query)
        return result.scalars().all()

    async def get_by_experience(
        self,
        level: ExperienceLevel,
    ) -> Sequence[UserProfile]:
        """Get all users with a specific experience level.

        Args:
            level: Experience level (novice, intermediate, expert)

        Returns:
            Sequence of users with that experience level
        """
        query = select(UserProfile).where(UserProfile.experience_level == level)
        result = await self.session.execute(query)
        return result.scalars().all()

    async def get_context_for_ai(self, user_id: str) -> dict | None:
        """Get user context formatted for AI personalization.

        Returns a dict with fields that influence AI response style:
        - experience_level: Determines explanation depth
        - farming_years: Respect for traditional methods
        - education_level: Vocabulary complexity
        - receives_subsidies: Financial recommendation eligibility
        - farm_count: Number of farms for context

        Args:
            user_id: User ID

        Returns:
            Context dict or None if user not found
        """
        user = await self.get_with_farms(user_id)
        if user is None:
            return None

        return {
            "user_id": user.user_id,
            "experience_level": user.experience_level.value,
            "farming_years": user.farming_years,
            "education_level": user.education_level.value,
            "language_pref": user.language_pref,
            "preferred_units": user.preferred_units,
            "receives_subsidies": user.receives_subsidies,
            "notification_pref": user.notification_pref.value,
            "farm_count": len(user.farms),
            "farm_ids": [farm.farm_id for farm in user.farms],
            "region_code": user.region_code,
            # AI personalization hints
            "explanation_depth": self._get_explanation_depth(user),
            "vocabulary_level": self._get_vocabulary_level(user),
            "trust_traditional": user.farming_years >= 20,
        }

    def _get_explanation_depth(self, user: UserProfile) -> str:
        """Determine explanation depth based on experience."""
        if user.experience_level == ExperienceLevel.NOVICE:
            return "detailed"  # Step-by-step explanations
        if user.experience_level == ExperienceLevel.EXPERT:
            return "brief"  # Concise summaries
        return "balanced"  # Standard explanations

    def _get_vocabulary_level(self, user: UserProfile) -> str:
        """Determine vocabulary complexity based on education."""
        from alim.data.models.user import EducationLevel

        if user.education_level == EducationLevel.UNIVERSITY:
            return "technical"  # Scientific terms OK
        if user.education_level == EducationLevel.TECHNICAL:
            return "professional"  # Industry terms OK
        return "simple"  # Plain language preferred

    async def search(
        self,
        region_code: str | None = None,
        experience_level: ExperienceLevel | None = None,
        min_farming_years: int | None = None,
        receives_subsidies: bool | None = None,
        limit: int = 50,
    ) -> Sequence[UserProfile]:
        """Search users with multiple filters.

        Args:
            region_code: Filter by region
            experience_level: Filter by experience
            min_farming_years: Minimum years of experience
            receives_subsidies: Filter by subsidy status
            limit: Maximum results

        Returns:
            Sequence of matching users
        """
        query = select(UserProfile)

        if region_code is not None:
            query = query.where(UserProfile.region_code == region_code)

        if experience_level is not None:
            query = query.where(UserProfile.experience_level == experience_level)

        if min_farming_years is not None:
            query = query.where(UserProfile.farming_years >= min_farming_years)

        if receives_subsidies is not None:
            query = query.where(UserProfile.receives_subsidies == receives_subsidies)

        query = query.limit(limit)

        result = await self.session.execute(query)
        return result.scalars().all()

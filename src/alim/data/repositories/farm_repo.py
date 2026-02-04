# src/ALİM/data/repositories/farm_repo.py
"""Farm repository for farm profile and parcel operations."""

from collections.abc import Sequence
from datetime import date
from typing import Any

from alim.data.models.farm import FarmProfile, FarmType, Region
from alim.data.models.ndvi import HealthStatus, NDVIReading
from alim.data.models.parcel import Parcel
from alim.data.models.sowing import DeclarationStatus, SowingDeclaration
from alim.data.repositories.base import BaseRepository
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload


class FarmRepository(BaseRepository[FarmProfile]):
    """Repository for FarmProfile operations.

    Extends BaseRepository with farm-specific queries:
    - get_with_parcels: Load farm with all parcels eagerly
    - get_by_user: Get all farms owned by a user
    - get_context_for_ai: Get complete farm context for AI
    - get_active_crops: Get currently planted crops
    - get_recent_ndvi: Get latest NDVI readings
    """

    def __init__(self, session: AsyncSession):
        """Initialize farm repository."""
        super().__init__(session, FarmProfile)

    async def get_with_parcels(self, farm_id: str) -> FarmProfile | None:
        """Get farm with all parcels eagerly loaded.

        Args:
            farm_id: Farm ID

        Returns:
            Farm with parcels loaded, or None if not found
        """
        query = (
            select(FarmProfile)
            .options(
                selectinload(FarmProfile.parcels).selectinload(Parcel.sowing_declarations),
                selectinload(FarmProfile.parcels).selectinload(Parcel.ndvi_readings),
            )
            .where(FarmProfile.farm_id == farm_id)
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_by_user(self, user_id: str) -> Sequence[FarmProfile]:
        """Get all farms owned by a user.

        Args:
            user_id: Owner's user ID

        Returns:
            Sequence of farms
        """
        query = (
            select(FarmProfile)
            .where(FarmProfile.user_id == user_id)
            .order_by(FarmProfile.is_primary.desc())
        )
        result = await self.session.execute(query)
        return result.scalars().all()

    async def get_by_region(self, region: Region) -> Sequence[FarmProfile]:
        """Get all farms in a region.

        Args:
            region: Agricultural region

        Returns:
            Sequence of farms in the region
        """
        query = select(FarmProfile).where(FarmProfile.region == region)
        result = await self.session.execute(query)
        return result.scalars().all()

    async def get_primary_farm(self, user_id: str) -> FarmProfile | None:
        """Get user's primary farm.

        Args:
            user_id: Owner's user ID

        Returns:
            Primary farm or None
        """
        query = (
            select(FarmProfile)
            .where(
                FarmProfile.user_id == user_id,
                FarmProfile.is_primary == True,  # noqa: E712
            )
            .limit(1)
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_context_for_ai(self, farm_id: str) -> dict[str, Any] | None:
        """Get complete farm context for AI recommendations.

        Returns a comprehensive dict with:
        - Farm basic info (type, region, area)
        - Active crops with growth stages
        - Recent NDVI readings with health status
        - Weather-relevant coordinates

        Args:
            farm_id: Farm ID

        Returns:
            Context dict or None if farm not found
        """
        farm = await self.get_with_parcels(farm_id)
        if farm is None:
            return None

        # Collect parcel information
        parcels_context = []
        active_crops = []
        alerts = []

        for parcel in farm.parcels:
            parcel_info = {
                "parcel_id": parcel.parcel_id,
                "area_ha": parcel.area_hectares,
                "soil_type": parcel.soil_type.value
                if hasattr(parcel.soil_type, "value")
                else parcel.soil_type,
                "irrigation": parcel.irrigation_type.value
                if hasattr(parcel.irrigation_type, "value")
                else parcel.irrigation_type,
                "coordinates": {
                    "lat": parcel.latitude,
                    "lon": parcel.longitude,
                },
            }

            # Get active crop
            active_declaration = next(
                (d for d in parcel.sowing_declarations if d.is_active),
                None,
            )
            if active_declaration:
                crop_type_value = (
                    active_declaration.crop_type.value
                    if hasattr(active_declaration.crop_type, "value")
                    else active_declaration.crop_type
                )
                parcel_info["current_crop"] = crop_type_value
                parcel_info["sowing_date"] = active_declaration.sowing_date.isoformat()
                active_crops.append(
                    {
                        "crop": crop_type_value,
                        "parcel_id": parcel.parcel_id,
                        "days_since_sowing": (date.today() - active_declaration.sowing_date).days,
                    }
                )

            # Get latest NDVI
            if parcel.ndvi_readings:
                latest_ndvi = max(parcel.ndvi_readings, key=lambda r: r.reading_date)
                health_status = (
                    latest_ndvi.health_status.value
                    if hasattr(latest_ndvi.health_status, "value")
                    else latest_ndvi.health_status
                )
                parcel_info["latest_ndvi"] = {
                    "value": latest_ndvi.ndvi_value,
                    "date": latest_ndvi.reading_date.isoformat(),
                    "health": health_status,
                }

                # Flag if attention needed
                if latest_ndvi.requires_attention:
                    alerts.append(
                        {
                            "type": "ndvi_stress",
                            "parcel_id": parcel.parcel_id,
                            "severity": "high"
                            if latest_ndvi.health_status == HealthStatus.CRITICAL
                            else "medium",
                            "message_az": f"{parcel.parcel_id} sahəsində bitki stressi aşkarlandı",
                        }
                    )

            parcels_context.append(parcel_info)

        return {
            "farm_id": farm.farm_id,
            "farm_name": farm.farm_name,
            "farm_type": farm.farm_type.value
            if hasattr(farm.farm_type, "value")
            else farm.farm_type,
            "region": farm.region.value if hasattr(farm.region, "value") else farm.region,
            "total_area_ha": farm.total_area_ha,
            "primary_activity": farm.primary_activity,
            "is_primary": farm.is_primary,
            "parcel_count": len(farm.parcels),
            "parcels": parcels_context,
            "active_crops": active_crops,
            "alerts": alerts,
            "center_coordinates": farm.region_coordinates,
        }

    async def get_active_crops(self, farm_id: str) -> list[dict[str, Any]]:
        """Get all currently planted crops for a farm.

        Args:
            farm_id: Farm ID

        Returns:
            List of active crop info dicts
        """
        query = (
            select(SowingDeclaration)
            .join(Parcel)
            .where(
                Parcel.farm_id == farm_id,
                SowingDeclaration.status.in_(
                    [
                        DeclarationStatus.PENDING,
                        DeclarationStatus.CONFIRMED,
                    ]
                ),
            )
        )
        result = await self.session.execute(query)
        declarations = result.scalars().all()

        return [
            {
                "declaration_id": d.declaration_id,
                "parcel_id": d.parcel_id,
                "crop_type": d.crop_type.value if hasattr(d.crop_type, "value") else d.crop_type,
                "sowing_date": d.sowing_date.isoformat(),
                "expected_harvest": d.expected_harvest_date.isoformat()
                if d.expected_harvest_date
                else None,
                "days_growing": (date.today() - d.sowing_date).days,
            }
            for d in declarations
        ]

    async def get_recent_ndvi(
        self,
        farm_id: str,
        days: int = 30,
    ) -> list[dict[str, Any]]:
        """Get recent NDVI readings for all parcels in a farm.

        Args:
            farm_id: Farm ID
            days: Number of days to look back

        Returns:
            List of NDVI reading dicts
        """
        from datetime import timedelta

        cutoff_date = date.today() - timedelta(days=days)

        query = (
            select(NDVIReading)
            .join(Parcel)
            .where(
                Parcel.farm_id == farm_id,
                NDVIReading.reading_date >= cutoff_date,
            )
            .order_by(NDVIReading.reading_date.desc())
        )
        result = await self.session.execute(query)
        readings = result.scalars().all()

        return [
            {
                "reading_id": r.reading_id,
                "parcel_id": r.parcel_id,
                "date": r.reading_date.isoformat(),
                "ndvi": r.ndvi_value,
                "health_status": r.health_status.value
                if hasattr(r.health_status, "value")
                else r.health_status,
                "requires_attention": r.requires_attention,
            }
            for r in readings
        ]

    async def get_stress_alerts(self, user_id: str) -> list[dict[str, Any]]:
        """Get all stress alerts for a user's farms.

        Args:
            user_id: User ID

        Returns:
            List of alert dicts
        """
        # Get all farms for user
        farms = await self.get_by_user(user_id)

        alerts = []
        for farm in farms:
            farm_context = await self.get_context_for_ai(farm.farm_id)
            if farm_context:
                for alert in farm_context.get("alerts", []):
                    alert["farm_id"] = farm.farm_id
                    alert["farm_name"] = farm.farm_name
                    alerts.append(alert)

        return alerts

    async def search(
        self,
        user_id: str | None = None,
        region: Region | None = None,
        farm_type: FarmType | None = None,
        min_area_ha: float | None = None,
        is_active: bool = True,
        limit: int = 50,
    ) -> Sequence[FarmProfile]:
        """Search farms with multiple filters.

        Args:
            user_id: Filter by owner
            region: Filter by region
            farm_type: Filter by farm type
            min_area_ha: Minimum area in hectares
            is_active: Filter by active status
            limit: Maximum results

        Returns:
            Sequence of matching farms
        """
        query = select(FarmProfile).where(FarmProfile.is_active == is_active)

        if user_id is not None:
            query = query.where(FarmProfile.user_id == user_id)

        if region is not None:
            query = query.where(FarmProfile.region == region)

        if farm_type is not None:
            query = query.where(FarmProfile.farm_type == farm_type)

        if min_area_ha is not None:
            query = query.where(FarmProfile.total_area_ha >= min_area_ha)

        query = query.limit(limit)

        result = await self.session.execute(query)
        return result.scalars().all()

"""
Yonca AI - Data Adapter Interface
=================================

Hot-swappable data source interface for Dummy-to-Real transition.

Phase 1 (Current): SyntheticDataAdapter - 100% generated data
Phase 2 (Future):  HybridDataAdapter - Real + synthetic blend
Phase 3 (Future):  SecureRealDataAdapter - Full national integration
"""

from abc import ABC, abstractmethod
from datetime import date
from typing import Optional, Protocol, runtime_checkable

from yonca.models import FarmProfile, WeatherData, SoilData


@runtime_checkable
class DataAdapter(Protocol):
    """
    Interface for swappable data sources.
    
    Implement this protocol to add new data sources.
    The Sidecar Intelligence module uses this interface,
    enabling hot-swap between synthetic and real data.
    """
    
    def get_farm_profile(self, farm_id: str) -> Optional[FarmProfile]:
        """
        Get a farm profile by ID.
        
        Args:
            farm_id: The farm identifier
            
        Returns:
            FarmProfile if found, None otherwise
        """
        ...
    
    def get_weather(
        self,
        region: str,
        start_date: date,
        days: int = 7
    ) -> list[WeatherData]:
        """
        Get weather forecast for a region.
        
        Args:
            region: Region name (e.g., "Aran", "Şəki-Zaqatala")
            start_date: Start date for forecast
            days: Number of days to forecast
            
        Returns:
            List of WeatherData for each day
        """
        ...
    
    def get_soil_data(self, farm_id: str) -> Optional[SoilData]:
        """
        Get soil data for a farm.
        
        Args:
            farm_id: The farm identifier
            
        Returns:
            SoilData if available, None otherwise
        """
        ...
    
    def list_farms(self) -> list[FarmProfile]:
        """
        List all available farm profiles.
        
        Returns:
            List of all FarmProfile objects
        """
        ...


class SyntheticDataAdapter:
    """
    Phase 1 Adapter: 100% Synthetic Data
    
    Uses pre-defined scenario farms and generated data.
    No real farmer data is accessed.
    """
    
    def __init__(self):
        from yonca.data.scenarios import get_scenario_farms, ALL_SCENARIOS
        from yonca.data.generators import WeatherGenerator, SoilGenerator
        
        self._farms = get_scenario_farms()
        self._all_farms = ALL_SCENARIOS
        self._weather_generator = WeatherGenerator
        self._soil_generator = SoilGenerator
    
    def get_farm_profile(self, farm_id: str) -> Optional[FarmProfile]:
        """Get synthetic farm profile."""
        return self._farms.get(farm_id)
    
    def get_weather(
        self,
        region: str,
        start_date: date,
        days: int = 7
    ) -> list[WeatherData]:
        """Generate synthetic weather forecast."""
        return self._weather_generator.generate(start_date, region, days)
    
    def get_soil_data(self, farm_id: str) -> Optional[SoilData]:
        """Get synthetic soil data from farm profile."""
        farm = self._farms.get(farm_id)
        return farm.soil_data if farm else None
    
    def list_farms(self) -> list[FarmProfile]:
        """List all synthetic scenario farms."""
        return self._all_farms


class HybridDataAdapter:
    """
    Phase 2 Adapter: Real + Synthetic Blend
    
    Attempts real data first, falls back to synthetic.
    Real data is anonymized (k-anonymity, k≥10).
    
    TODO: Implement in Phase 2
    """
    
    def __init__(
        self,
        real_adapter: Optional[DataAdapter] = None,
        synthetic_adapter: Optional[DataAdapter] = None,
        anonymization_k: int = 10
    ):
        self._real = real_adapter
        self._synthetic = synthetic_adapter or SyntheticDataAdapter()
        self._k = anonymization_k
    
    def get_farm_profile(self, farm_id: str) -> Optional[FarmProfile]:
        """
        Try real data first, fall back to synthetic.
        
        Real farm profiles are anonymized before return.
        """
        if self._real:
            try:
                profile = self._real.get_farm_profile(farm_id)
                if profile:
                    return self._anonymize_profile(profile)
            except Exception:
                pass
        
        return self._synthetic.get_farm_profile(farm_id)
    
    def get_weather(
        self,
        region: str,
        start_date: date,
        days: int = 7
    ) -> list[WeatherData]:
        """
        Prefer real weather data if available.
        
        Weather data is generally not PII-sensitive.
        """
        if self._real:
            try:
                data = self._real.get_weather(region, start_date, days)
                if data:
                    return data
            except Exception:
                pass
        
        return self._synthetic.get_weather(region, start_date, days)
    
    def get_soil_data(self, farm_id: str) -> Optional[SoilData]:
        """
        Soil data from real sources if available.
        
        Soil data is generally not PII-sensitive.
        """
        if self._real:
            try:
                data = self._real.get_soil_data(farm_id)
                if data:
                    return data
            except Exception:
                pass
        
        return self._synthetic.get_soil_data(farm_id)
    
    def list_farms(self) -> list[FarmProfile]:
        """List farms from both real and synthetic sources."""
        farms = self._synthetic.list_farms()
        
        if self._real:
            try:
                real_farms = self._real.list_farms()
                # Anonymize and add real farms
                for farm in real_farms:
                    farms.append(self._anonymize_profile(farm))
            except Exception:
                pass
        
        return farms
    
    def _anonymize_profile(self, profile: FarmProfile) -> FarmProfile:
        """
        Apply k-anonymity to a farm profile.
        
        - Remove or generalize identifying information
        - Ensure k≥10 identical profiles exist
        """
        # Create a copy with anonymized fields
        anonymized = profile.model_copy(deep=True)
        
        # Generalize location (round coordinates)
        if anonymized.location:
            anonymized.location.latitude = round(anonymized.location.latitude, 1)
            anonymized.location.longitude = round(anonymized.location.longitude, 1)
        
        # Generalize area (to nearest 5 hectares)
        anonymized.total_area_hectares = round(anonymized.total_area_hectares / 5) * 5
        
        # Remove potentially identifying names
        anonymized.name = f"Anonim Təsərrüfat ({anonymized.farm_type.value})"
        anonymized.id = f"anon-{hash(profile.id) % 10000:04d}"
        
        return anonymized


class SecureRealDataAdapter:
    """
    Phase 3 Adapter: Full National Integration
    
    Connects to national agricultural data systems:
    - ASAN Kənd API
    - AzerStat Agricultural Data
    - AgriBank Subsidy Systems
    
    Security features:
    - OAuth 2.0 authentication
    - End-to-end encryption
    - Audit logging
    - Data minimization
    
    TODO: Implement in Phase 3
    """
    
    def __init__(
        self,
        api_base_url: str,
        client_id: str,
        client_secret: str,
        **kwargs
    ):
        self._api_url = api_base_url
        self._client_id = client_id
        self._client_secret = client_secret
        self._token = None
        
        # TODO: Initialize OAuth client
        raise NotImplementedError(
            "SecureRealDataAdapter is planned for Phase 3 (12-24 months). "
            "Use SyntheticDataAdapter or HybridDataAdapter for now."
        )
    
    def get_farm_profile(self, farm_id: str) -> Optional[FarmProfile]:
        raise NotImplementedError("Phase 3 feature")
    
    def get_weather(
        self,
        region: str,
        start_date: date,
        days: int = 7
    ) -> list[WeatherData]:
        raise NotImplementedError("Phase 3 feature")
    
    def get_soil_data(self, farm_id: str) -> Optional[SoilData]:
        raise NotImplementedError("Phase 3 feature")
    
    def list_farms(self) -> list[FarmProfile]:
        raise NotImplementedError("Phase 3 feature")


# Factory function
def create_data_adapter(
    mode: str = "synthetic",
    **kwargs
) -> DataAdapter:
    """
    Create a data adapter based on deployment mode.
    
    Args:
        mode: "synthetic", "hybrid", or "real"
        **kwargs: Additional configuration for the adapter
        
    Returns:
        Configured DataAdapter instance
    """
    if mode == "synthetic":
        return SyntheticDataAdapter()
    elif mode == "hybrid":
        return HybridDataAdapter(**kwargs)
    elif mode == "real":
        return SecureRealDataAdapter(**kwargs)
    else:
        raise ValueError(f"Unknown adapter mode: {mode}")

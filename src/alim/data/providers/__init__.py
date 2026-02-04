# src/ALİM/data/providers/__init__.py
"""Custom Faker providers for Azerbaijani agricultural data.

Provides realistic Azerbaijani-specific data generation for:
- Parcel IDs (EKTIS format)
- Declaration IDs
- Azerbaijani names, regions, crops
- Weather data
- NDVI time series
"""

from alim.data.providers.azerbaijani import AzerbaijaniAgrarianProvider

__all__ = ["AzerbaijaniAgrarianProvider"]

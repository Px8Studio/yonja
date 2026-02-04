# src/ALİM/data/repositories/__init__.py
"""Repository pattern for clean data access.

Provides:
- UserRepository: User profile CRUD operations
- FarmRepository: Farm profile with context loading
- ParcelRepository: Parcel data access
"""

from alim.data.repositories.base import BaseRepository
from alim.data.repositories.farm_repo import FarmRepository
from alim.data.repositories.user_repo import UserRepository

__all__ = [
    "BaseRepository",
    "UserRepository",
    "FarmRepository",
]

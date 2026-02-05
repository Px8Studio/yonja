# src/ALİM/data/repositories/base.py
"""Base repository with common CRUD operations."""

from collections.abc import Sequence
from typing import Any, Generic, TypeVar

from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from alim.data.database import Base

ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository(Generic[ModelType]):
    """Base repository providing common CRUD operations.

    Provides:
    - create: Insert new record
    - get_by_id: Fetch single record by primary key
    - get_all: Fetch all records with optional limit/offset
    - update: Update existing record
    - delete: Delete record by ID
    - exists: Check if record exists
    """

    def __init__(self, session: AsyncSession, model: type[ModelType]):
        """Initialize repository.

        Args:
            session: Async SQLAlchemy session
            model: SQLAlchemy model class
        """
        self.session = session
        self.model = model

    async def create(self, **kwargs: Any) -> ModelType:
        """Create a new record.

        Args:
            **kwargs: Model field values

        Returns:
            Created model instance
        """
        instance = self.model(**kwargs)
        self.session.add(instance)
        await self.session.flush()
        await self.session.refresh(instance)
        return instance

    async def create_many(self, items: list[dict[str, Any]]) -> list[ModelType]:
        """Create multiple records.

        Args:
            items: List of dicts with model field values

        Returns:
            List of created model instances
        """
        instances = [self.model(**item) for item in items]
        self.session.add_all(instances)
        await self.session.flush()
        for instance in instances:
            await self.session.refresh(instance)
        return instances

    async def get_by_id(self, id_: str) -> ModelType | None:
        """Get a record by primary key.

        Args:
            id_: Primary key value

        Returns:
            Model instance or None if not found
        """
        return await self.session.get(self.model, id_)

    async def get_all(
        self,
        limit: int | None = None,
        offset: int = 0,
    ) -> Sequence[ModelType]:
        """Get all records with optional pagination.

        Args:
            limit: Maximum number of records to return
            offset: Number of records to skip

        Returns:
            Sequence of model instances
        """
        query = select(self.model).offset(offset)
        if limit is not None:
            query = query.limit(limit)

        result = await self.session.execute(query)
        return result.scalars().all()

    async def update(self, id_: str, **kwargs: Any) -> ModelType | None:
        """Update a record by ID.

        Args:
            id_: Primary key value
            **kwargs: Fields to update

        Returns:
            Updated model instance or None if not found
        """
        # Get primary key column name
        pk_name = self.model.__mapper__.primary_key[0].name

        stmt = update(self.model).where(getattr(self.model, pk_name) == id_).values(**kwargs)
        await self.session.execute(stmt)
        await self.session.flush()

        return await self.get_by_id(id_)

    async def delete(self, id_: str) -> bool:
        """Delete a record by ID.

        Args:
            id_: Primary key value

        Returns:
            True if deleted, False if not found
        """
        pk_name = self.model.__mapper__.primary_key[0].name

        stmt = delete(self.model).where(getattr(self.model, pk_name) == id_)
        result = await self.session.execute(stmt)
        await self.session.flush()

        return result.rowcount > 0

    async def exists(self, id_: str) -> bool:
        """Check if a record exists.

        Args:
            id_: Primary key value

        Returns:
            True if exists, False otherwise
        """
        instance = await self.get_by_id(id_)
        return instance is not None

    async def count(self) -> int:
        """Get total count of records.

        Returns:
            Number of records
        """
        from sqlalchemy import func

        query = select(func.count()).select_from(self.model)
        result = await self.session.execute(query)
        return result.scalar() or 0

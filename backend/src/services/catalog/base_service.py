"""Base Service - Block B (Catalog Agent).

Generic CRUD operations for all catalog entities.
"""

from typing import Generic, Optional, Sequence, Type, TypeVar
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ...models.base import Base

ModelT = TypeVar("ModelT", bound=Base)


class BaseService(Generic[ModelT]):
    """Generic base service with CRUD operations."""

    def __init__(self, session: AsyncSession, model: Type[ModelT]) -> None:
        self.session = session
        self.model = model

    async def get_by_id(self, id: UUID) -> Optional[ModelT]:
        """Get entity by ID."""
        result = await self.session.execute(
            select(self.model).where(self.model.id == id)
        )
        return result.scalar_one_or_none()

    async def get_all(
        self,
        *,
        skip: int = 0,
        limit: int = 100,
    ) -> Sequence[ModelT]:
        """Get all entities with pagination."""
        result = await self.session.execute(
            select(self.model).offset(skip).limit(limit)
        )
        return result.scalars().all()

    async def count(self) -> int:
        """Count all entities."""
        result = await self.session.execute(
            select(func.count()).select_from(self.model)
        )
        return result.scalar() or 0

    async def create(self, **kwargs) -> ModelT:
        """Create a new entity."""
        entity = self.model(**kwargs)
        self.session.add(entity)
        await self.session.flush()
        await self.session.refresh(entity)
        return entity

    async def update(self, id: UUID, **kwargs) -> Optional[ModelT]:
        """Update an entity by ID."""
        entity = await self.get_by_id(id)
        if entity is None:
            return None
        for key, value in kwargs.items():
            if hasattr(entity, key):
                setattr(entity, key, value)
        await self.session.flush()
        await self.session.refresh(entity)
        return entity

    async def delete(self, id: UUID) -> bool:
        """Delete an entity by ID."""
        entity = await self.get_by_id(id)
        if entity is None:
            return False
        await self.session.delete(entity)
        await self.session.flush()
        return True

    async def exists(self, id: UUID) -> bool:
        """Check if entity exists."""
        result = await self.session.execute(
            select(func.count()).select_from(self.model).where(self.model.id == id)
        )
        return (result.scalar() or 0) > 0

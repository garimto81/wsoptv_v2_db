"""Season Service - Block B (Catalog Agent).

CRUD operations for Season entity.
"""

from typing import Optional, Sequence
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ...models.season import Season
from .base_service import BaseService


class SeasonService(BaseService[Season]):
    """Service for Season entity operations."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, Season)

    async def get_by_project_and_year(
        self,
        project_id: UUID,
        year: int,
        sub_category: Optional[str] = None,
    ) -> Optional[Season]:
        """Get season by project and year."""
        query = select(Season).where(
            Season.project_id == project_id,
            Season.year == year,
        )
        if sub_category:
            query = query.where(Season.sub_category == sub_category)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_by_project(
        self,
        project_id: UUID,
        *,
        skip: int = 0,
        limit: int = 100,
    ) -> Sequence[Season]:
        """Get all seasons for a project."""
        result = await self.session.execute(
            select(Season)
            .where(Season.project_id == project_id)
            .order_by(Season.year.desc())
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()

    async def get_with_events(self, season_id: UUID) -> Optional[Season]:
        """Get season with events loaded."""
        result = await self.session.execute(
            select(Season)
            .options(selectinload(Season.events))
            .where(Season.id == season_id)
        )
        return result.scalar_one_or_none()

    async def create_season(
        self,
        project_id: UUID,
        year: int,
        name: str,
        *,
        location: Optional[str] = None,
        sub_category: Optional[str] = None,
    ) -> Season:
        """Create a new season."""
        return await self.create(
            project_id=project_id,
            year=year,
            name=name,
            location=location,
            sub_category=sub_category,
        )

    async def get_years_for_project(self, project_id: UUID) -> list[int]:
        """Get distinct years for a project."""
        result = await self.session.execute(
            select(Season.year)
            .where(Season.project_id == project_id)
            .distinct()
            .order_by(Season.year.desc())
        )
        return list(result.scalars().all())

    async def get_by_year_range(
        self,
        project_id: UUID,
        start_year: int,
        end_year: int,
    ) -> Sequence[Season]:
        """Get seasons within a year range."""
        result = await self.session.execute(
            select(Season)
            .where(
                Season.project_id == project_id,
                Season.year >= start_year,
                Season.year <= end_year,
            )
            .order_by(Season.year.desc())
        )
        return result.scalars().all()

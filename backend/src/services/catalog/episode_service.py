"""Episode Service - Block B (Catalog Agent).

CRUD operations for Episode entity.
"""

from typing import Optional, Sequence
from uuid import UUID

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ...models.episode import Episode
from .base_service import BaseService


class EpisodeService(BaseService[Episode]):
    """Service for Episode entity operations."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, Episode)

    async def get_by_event_and_number(
        self,
        event_id: UUID,
        episode_number: Optional[int] = None,
        day_number: Optional[int] = None,
        part_number: Optional[int] = None,
    ) -> Optional[Episode]:
        """Get episode by event and numbering."""
        query = select(Episode).where(Episode.event_id == event_id)
        if episode_number is not None:
            query = query.where(Episode.episode_number == episode_number)
        if day_number is not None:
            query = query.where(Episode.day_number == day_number)
        if part_number is not None:
            query = query.where(Episode.part_number == part_number)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_by_event(
        self,
        event_id: UUID,
        *,
        skip: int = 0,
        limit: int = 100,
    ) -> Sequence[Episode]:
        """Get all episodes for an event."""
        result = await self.session.execute(
            select(Episode)
            .where(Episode.event_id == event_id)
            .order_by(
                Episode.day_number,
                Episode.episode_number,
                Episode.part_number,
            )
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()

    async def get_with_video_files(self, episode_id: UUID) -> Optional[Episode]:
        """Get episode with video files loaded."""
        result = await self.session.execute(
            select(Episode)
            .options(selectinload(Episode.video_files))
            .where(Episode.id == episode_id)
        )
        return result.scalar_one_or_none()

    async def get_with_hand_clips(self, episode_id: UUID) -> Optional[Episode]:
        """Get episode with hand clips loaded."""
        result = await self.session.execute(
            select(Episode)
            .options(selectinload(Episode.hand_clips))
            .where(Episode.id == episode_id)
        )
        return result.scalar_one_or_none()

    async def get_full(self, episode_id: UUID) -> Optional[Episode]:
        """Get episode with all relationships loaded."""
        result = await self.session.execute(
            select(Episode)
            .options(
                selectinload(Episode.video_files),
                selectinload(Episode.hand_clips),
                selectinload(Episode.event),
            )
            .where(Episode.id == episode_id)
        )
        return result.scalar_one_or_none()

    async def create_episode(
        self,
        event_id: UUID,
        *,
        episode_number: Optional[int] = None,
        day_number: Optional[int] = None,
        part_number: Optional[int] = None,
        title: Optional[str] = None,
        episode_type: Optional[str] = None,
        table_type: Optional[str] = None,
        duration_seconds: Optional[int] = None,
    ) -> Episode:
        """Create a new episode."""
        return await self.create(
            event_id=event_id,
            episode_number=episode_number,
            day_number=day_number,
            part_number=part_number,
            title=title,
            episode_type=episode_type,
            table_type=table_type,
            duration_seconds=duration_seconds,
        )

    async def get_by_episode_type(
        self,
        event_id: UUID,
        episode_type: str,
    ) -> Sequence[Episode]:
        """Get episodes by type within an event."""
        result = await self.session.execute(
            select(Episode)
            .where(
                Episode.event_id == event_id,
                Episode.episode_type == episode_type,
            )
            .order_by(Episode.episode_number)
        )
        return result.scalars().all()

    async def get_by_table_type(
        self,
        event_id: UUID,
        table_type: str,
    ) -> Sequence[Episode]:
        """Get episodes by table type (final_table, day1, etc)."""
        result = await self.session.execute(
            select(Episode)
            .where(
                Episode.event_id == event_id,
                Episode.table_type == table_type,
            )
            .order_by(Episode.episode_number)
        )
        return result.scalars().all()

    async def get_final_tables(self, event_id: UUID) -> Sequence[Episode]:
        """Get final table episodes for an event."""
        result = await self.session.execute(
            select(Episode)
            .where(
                Episode.event_id == event_id,
                or_(
                    Episode.table_type == "final_table",
                    Episode.table_type == "heads_up",
                ),
            )
            .order_by(Episode.episode_number)
        )
        return result.scalars().all()

    async def get_total_duration(self, event_id: UUID) -> int:
        """Get total duration of all episodes for an event."""
        result = await self.session.execute(
            select(Episode.duration_seconds)
            .where(Episode.event_id == event_id)
        )
        durations = result.scalars().all()
        return sum(d for d in durations if d is not None)

    async def search_by_title(
        self,
        query: str,
        *,
        event_id: Optional[UUID] = None,
        limit: int = 50,
    ) -> Sequence[Episode]:
        """Search episodes by title."""
        stmt = select(Episode).where(Episode.title.ilike(f"%{query}%"))
        if event_id:
            stmt = stmt.where(Episode.event_id == event_id)
        stmt = stmt.limit(limit)
        result = await self.session.execute(stmt)
        return result.scalars().all()

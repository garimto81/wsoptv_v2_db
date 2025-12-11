"""Event Service - Block B (Catalog Agent).

CRUD operations for Event entity.
"""

from decimal import Decimal
from typing import Optional, Sequence
from uuid import UUID

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ...models.event import Event
from .base_service import BaseService


class EventService(BaseService[Event]):
    """Service for Event entity operations."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, Event)

    async def get_by_season_and_number(
        self,
        season_id: UUID,
        event_number: int,
    ) -> Optional[Event]:
        """Get event by season and event number."""
        result = await self.session.execute(
            select(Event).where(
                Event.season_id == season_id,
                Event.event_number == event_number,
            )
        )
        return result.scalar_one_or_none()

    async def get_by_season(
        self,
        season_id: UUID,
        *,
        skip: int = 0,
        limit: int = 100,
    ) -> Sequence[Event]:
        """Get all events for a season."""
        result = await self.session.execute(
            select(Event)
            .where(Event.season_id == season_id)
            .order_by(Event.event_number)
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()

    async def get_with_episodes(self, event_id: UUID) -> Optional[Event]:
        """Get event with episodes loaded."""
        result = await self.session.execute(
            select(Event)
            .options(selectinload(Event.episodes))
            .where(Event.id == event_id)
        )
        return result.scalar_one_or_none()

    async def create_event(
        self,
        season_id: UUID,
        name: str,
        *,
        event_number: Optional[int] = None,
        name_short: Optional[str] = None,
        event_type: Optional[str] = None,
        game_type: Optional[str] = None,
        buy_in: Optional[Decimal] = None,
        gtd_amount: Optional[Decimal] = None,
        venue: Optional[str] = None,
    ) -> Event:
        """Create a new event."""
        return await self.create(
            season_id=season_id,
            name=name,
            event_number=event_number,
            name_short=name_short,
            event_type=event_type,
            game_type=game_type,
            buy_in=buy_in,
            gtd_amount=gtd_amount,
            venue=venue,
        )

    async def search_by_name(
        self,
        query: str,
        *,
        season_id: Optional[UUID] = None,
        limit: int = 50,
    ) -> Sequence[Event]:
        """Search events by name."""
        stmt = select(Event).where(
            or_(
                Event.name.ilike(f"%{query}%"),
                Event.name_short.ilike(f"%{query}%"),
            )
        )
        if season_id:
            stmt = stmt.where(Event.season_id == season_id)
        stmt = stmt.limit(limit)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_by_event_type(
        self,
        season_id: UUID,
        event_type: str,
    ) -> Sequence[Event]:
        """Get events by type within a season."""
        result = await self.session.execute(
            select(Event)
            .where(
                Event.season_id == season_id,
                Event.event_type == event_type,
            )
            .order_by(Event.event_number)
        )
        return result.scalars().all()

    async def get_by_game_type(
        self,
        season_id: UUID,
        game_type: str,
    ) -> Sequence[Event]:
        """Get events by game type within a season."""
        result = await self.session.execute(
            select(Event)
            .where(
                Event.season_id == season_id,
                Event.game_type == game_type,
            )
            .order_by(Event.event_number)
        )
        return result.scalars().all()

    async def get_high_roller_events(
        self,
        season_id: UUID,
        min_buy_in: Decimal = Decimal("10000"),
    ) -> Sequence[Event]:
        """Get high roller events (buy-in >= threshold)."""
        result = await self.session.execute(
            select(Event)
            .where(
                Event.season_id == season_id,
                Event.buy_in >= min_buy_in,
            )
            .order_by(Event.buy_in.desc())
        )
        return result.scalars().all()

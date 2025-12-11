"""Player Service - Block C (Hand Analysis Agent).

CRUD operations for Player entity.
"""

from decimal import Decimal
from typing import Optional, Sequence
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ...models.hand_clip import hand_clip_players
from ...models.player import Player
from ..catalog.base_service import BaseService


class PlayerService(BaseService[Player]):
    """Service for Player entity operations."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, Player)

    async def get_by_name(self, name: str) -> Optional[Player]:
        """Get player by name."""
        result = await self.session.execute(
            select(Player).where(Player.name == name)
        )
        return result.scalar_one_or_none()

    async def get_with_hand_clips(self, player_id: UUID) -> Optional[Player]:
        """Get player with hand clips loaded."""
        result = await self.session.execute(
            select(Player)
            .options(selectinload(Player.hand_clips))
            .where(Player.id == player_id)
        )
        return result.scalar_one_or_none()

    async def create_player(
        self,
        name: str,
        *,
        name_display: Optional[str] = None,
        nationality: Optional[str] = None,
        hendon_mob_id: Optional[str] = None,
        total_live_earnings: Optional[Decimal] = None,
        wsop_bracelets: int = 0,
    ) -> Player:
        """Create a new player."""
        return await self.create(
            name=name,
            name_display=name_display or name,
            nationality=nationality,
            hendon_mob_id=hendon_mob_id,
            total_live_earnings=total_live_earnings,
            wsop_bracelets=wsop_bracelets,
        )

    async def get_or_create(self, name: str) -> Player:
        """Get existing player or create new one."""
        player = await self.get_by_name(name)
        if player is None:
            player = await self.create_player(name)
        return player

    async def search_by_name(
        self,
        query: str,
        *,
        limit: int = 50,
    ) -> Sequence[Player]:
        """Search players by name."""
        result = await self.session.execute(
            select(Player)
            .where(Player.name.ilike(f"%{query}%"))
            .limit(limit)
        )
        return result.scalars().all()

    async def get_by_nationality(
        self,
        nationality: str,
        *,
        skip: int = 0,
        limit: int = 100,
    ) -> Sequence[Player]:
        """Get players by nationality."""
        result = await self.session.execute(
            select(Player)
            .where(Player.nationality == nationality)
            .order_by(Player.name)
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()

    async def get_bracelet_winners(
        self,
        min_bracelets: int = 1,
        *,
        limit: int = 100,
    ) -> Sequence[Player]:
        """Get players with WSOP bracelets."""
        result = await self.session.execute(
            select(Player)
            .where(Player.wsop_bracelets >= min_bracelets)
            .order_by(Player.wsop_bracelets.desc())
            .limit(limit)
        )
        return result.scalars().all()

    async def get_top_earners(
        self,
        limit: int = 50,
    ) -> Sequence[Player]:
        """Get players by total live earnings."""
        result = await self.session.execute(
            select(Player)
            .where(Player.total_live_earnings.isnot(None))
            .order_by(Player.total_live_earnings.desc())
            .limit(limit)
        )
        return result.scalars().all()

    async def get_frequent_players(
        self,
        limit: int = 20,
    ) -> Sequence[tuple[Player, int]]:
        """Get most frequently appearing players in hand clips."""
        stmt = (
            select(Player, func.count(hand_clip_players.c.hand_clip_id).label("count"))
            .outerjoin(hand_clip_players, Player.id == hand_clip_players.c.player_id)
            .group_by(Player.id)
            .order_by(func.count(hand_clip_players.c.hand_clip_id).desc())
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return [(row[0], row[1]) for row in result.all()]

    async def update_stats(
        self,
        player_id: UUID,
        *,
        total_live_earnings: Optional[Decimal] = None,
        wsop_bracelets: Optional[int] = None,
    ) -> Optional[Player]:
        """Update player statistics."""
        update_data = {}
        if total_live_earnings is not None:
            update_data["total_live_earnings"] = total_live_earnings
        if wsop_bracelets is not None:
            update_data["wsop_bracelets"] = wsop_bracelets
        if not update_data:
            return await self.get_by_id(player_id)
        return await self.update(player_id, **update_data)

    async def deactivate(self, player_id: UUID) -> Optional[Player]:
        """Deactivate a player."""
        player = await self.get_by_id(player_id)
        if player is None:
            return None
        player.is_active = False
        await self.session.flush()
        await self.session.refresh(player)
        return player

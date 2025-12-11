"""HandClip Service - Block C (Hand Analysis Agent).

CRUD operations for HandClip entity with tag and player management.
"""

from typing import Optional, Sequence
from uuid import UUID

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ...models.hand_clip import HandClip, hand_clip_players, hand_clip_tags
from ...models.player import Player
from ...models.tag import Tag
from ..catalog.base_service import BaseService


class HandClipService(BaseService[HandClip]):
    """Service for HandClip entity operations."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, HandClip)

    async def get_by_sheet_row(
        self,
        sheet_source: str,
        row_number: int,
    ) -> Optional[HandClip]:
        """Get hand clip by sheet source and row number."""
        result = await self.session.execute(
            select(HandClip).where(
                HandClip.sheet_source == sheet_source,
                HandClip.sheet_row_number == row_number,
            )
        )
        return result.scalar_one_or_none()

    async def get_by_episode(
        self,
        episode_id: UUID,
        *,
        skip: int = 0,
        limit: int = 100,
    ) -> Sequence[HandClip]:
        """Get all hand clips for an episode."""
        result = await self.session.execute(
            select(HandClip)
            .where(HandClip.episode_id == episode_id)
            .order_by(HandClip.timecode)
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()

    async def get_by_video_file(
        self,
        video_file_id: UUID,
        *,
        skip: int = 0,
        limit: int = 100,
    ) -> Sequence[HandClip]:
        """Get all hand clips for a video file."""
        result = await self.session.execute(
            select(HandClip)
            .where(HandClip.video_file_id == video_file_id)
            .order_by(HandClip.timecode)
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()

    async def get_with_relationships(self, clip_id: UUID) -> Optional[HandClip]:
        """Get hand clip with all relationships loaded."""
        result = await self.session.execute(
            select(HandClip)
            .options(
                selectinload(HandClip.tags),
                selectinload(HandClip.players),
                selectinload(HandClip.episode),
                selectinload(HandClip.video_file),
            )
            .where(HandClip.id == clip_id)
        )
        return result.scalar_one_or_none()

    async def create_hand_clip(
        self,
        *,
        episode_id: Optional[UUID] = None,
        video_file_id: Optional[UUID] = None,
        sheet_source: Optional[str] = None,
        sheet_row_number: Optional[int] = None,
        title: Optional[str] = None,
        timecode: Optional[str] = None,
        timecode_end: Optional[str] = None,
        duration_seconds: Optional[int] = None,
        notes: Optional[str] = None,
        hand_grade: Optional[str] = None,
        pot_size: Optional[int] = None,
        winner_hand: Optional[str] = None,
        hands_involved: Optional[str] = None,
    ) -> HandClip:
        """Create a new hand clip."""
        return await self.create(
            episode_id=episode_id,
            video_file_id=video_file_id,
            sheet_source=sheet_source,
            sheet_row_number=sheet_row_number,
            title=title,
            timecode=timecode,
            timecode_end=timecode_end,
            duration_seconds=duration_seconds,
            notes=notes,
            hand_grade=hand_grade,
            pot_size=pot_size,
            winner_hand=winner_hand,
            hands_involved=hands_involved,
        )

    async def add_tag(self, clip_id: UUID, tag_id: UUID) -> bool:
        """Add a tag to a hand clip."""
        clip = await self.get_with_relationships(clip_id)
        if clip is None:
            return False
        result = await self.session.execute(
            select(Tag).where(Tag.id == tag_id)
        )
        tag = result.scalar_one_or_none()
        if tag is None:
            return False
        if tag not in clip.tags:
            clip.tags.append(tag)
            await self.session.flush()
        return True

    async def remove_tag(self, clip_id: UUID, tag_id: UUID) -> bool:
        """Remove a tag from a hand clip."""
        clip = await self.get_with_relationships(clip_id)
        if clip is None:
            return False
        result = await self.session.execute(
            select(Tag).where(Tag.id == tag_id)
        )
        tag = result.scalar_one_or_none()
        if tag is None or tag not in clip.tags:
            return False
        clip.tags.remove(tag)
        await self.session.flush()
        return True

    async def add_player(self, clip_id: UUID, player_id: UUID) -> bool:
        """Add a player to a hand clip."""
        clip = await self.get_with_relationships(clip_id)
        if clip is None:
            return False
        result = await self.session.execute(
            select(Player).where(Player.id == player_id)
        )
        player = result.scalar_one_or_none()
        if player is None:
            return False
        if player not in clip.players:
            clip.players.append(player)
            await self.session.flush()
        return True

    async def remove_player(self, clip_id: UUID, player_id: UUID) -> bool:
        """Remove a player from a hand clip."""
        clip = await self.get_with_relationships(clip_id)
        if clip is None:
            return False
        result = await self.session.execute(
            select(Player).where(Player.id == player_id)
        )
        player = result.scalar_one_or_none()
        if player is None or player not in clip.players:
            return False
        clip.players.remove(player)
        await self.session.flush()
        return True

    async def search_by_title(
        self,
        query: str,
        *,
        limit: int = 50,
    ) -> Sequence[HandClip]:
        """Search hand clips by title."""
        result = await self.session.execute(
            select(HandClip)
            .where(HandClip.title.ilike(f"%{query}%"))
            .limit(limit)
        )
        return result.scalars().all()

    async def get_by_grade(
        self,
        grade: str,
        *,
        skip: int = 0,
        limit: int = 100,
    ) -> Sequence[HandClip]:
        """Get hand clips by grade."""
        result = await self.session.execute(
            select(HandClip)
            .where(HandClip.hand_grade == grade)
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()

    async def get_by_tag(
        self,
        tag_id: UUID,
        *,
        skip: int = 0,
        limit: int = 100,
    ) -> Sequence[HandClip]:
        """Get hand clips with a specific tag."""
        result = await self.session.execute(
            select(HandClip)
            .join(hand_clip_tags)
            .where(hand_clip_tags.c.tag_id == tag_id)
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()

    async def get_by_player(
        self,
        player_id: UUID,
        *,
        skip: int = 0,
        limit: int = 100,
    ) -> Sequence[HandClip]:
        """Get hand clips featuring a specific player."""
        result = await self.session.execute(
            select(HandClip)
            .join(hand_clip_players)
            .where(hand_clip_players.c.player_id == player_id)
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()

    async def get_high_pot_clips(
        self,
        min_pot: int = 100000,
        *,
        limit: int = 50,
    ) -> Sequence[HandClip]:
        """Get hand clips with large pots."""
        result = await self.session.execute(
            select(HandClip)
            .where(HandClip.pot_size >= min_pot)
            .order_by(HandClip.pot_size.desc())
            .limit(limit)
        )
        return result.scalars().all()

"""Tag Service - Block C (Hand Analysis Agent).

CRUD operations for Tag entity.
"""

from typing import Optional, Sequence

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ...models.hand_clip import hand_clip_tags
from ...models.tag import Tag, TagCategory
from ..catalog.base_service import BaseService


class TagService(BaseService[Tag]):
    """Service for Tag entity operations."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, Tag)

    async def get_by_category_and_name(
        self,
        category: str,
        name: str,
    ) -> Optional[Tag]:
        """Get tag by category and name."""
        result = await self.session.execute(
            select(Tag).where(
                Tag.category == category,
                Tag.name == name,
            )
        )
        return result.scalar_one_or_none()

    async def get_by_category(
        self,
        category: str,
        *,
        active_only: bool = True,
    ) -> Sequence[Tag]:
        """Get all tags in a category."""
        query = select(Tag).where(Tag.category == category)
        if active_only:
            query = query.where(Tag.is_active == True)
        query = query.order_by(Tag.sort_order, Tag.name)
        result = await self.session.execute(query)
        return result.scalars().all()

    async def create_tag(
        self,
        category: str,
        name: str,
        *,
        name_display: Optional[str] = None,
        description: Optional[str] = None,
        sort_order: int = 0,
    ) -> Tag:
        """Create a new tag."""
        return await self.create(
            category=category,
            name=name,
            name_display=name_display or name,
            description=description,
            sort_order=sort_order,
        )

    async def get_or_create(
        self,
        category: str,
        name: str,
    ) -> Tag:
        """Get existing tag or create new one."""
        tag = await self.get_by_category_and_name(category, name)
        if tag is None:
            tag = await self.create_tag(category, name)
        return tag

    async def search_by_name(
        self,
        query: str,
        *,
        category: Optional[str] = None,
        limit: int = 50,
    ) -> Sequence[Tag]:
        """Search tags by name."""
        stmt = select(Tag).where(Tag.name.ilike(f"%{query}%"))
        if category:
            stmt = stmt.where(Tag.category == category)
        stmt = stmt.limit(limit)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_popular_tags(
        self,
        *,
        category: Optional[str] = None,
        limit: int = 20,
    ) -> Sequence[tuple[Tag, int]]:
        """Get most used tags with usage count."""
        stmt = (
            select(Tag, func.count(hand_clip_tags.c.hand_clip_id).label("count"))
            .outerjoin(hand_clip_tags, Tag.id == hand_clip_tags.c.tag_id)
            .group_by(Tag.id)
            .order_by(func.count(hand_clip_tags.c.hand_clip_id).desc())
        )
        if category:
            stmt = stmt.where(Tag.category == category)
        stmt = stmt.limit(limit)
        result = await self.session.execute(stmt)
        return [(row[0], row[1]) for row in result.all()]

    async def deactivate(self, tag_id) -> Optional[Tag]:
        """Deactivate a tag."""
        tag = await self.get_by_id(tag_id)
        if tag is None:
            return None
        tag.is_active = False
        await self.session.flush()
        await self.session.refresh(tag)
        return tag

    async def seed_default_tags(self) -> list[Tag]:
        """Seed default poker and emotion tags."""
        tags = []
        default_tags = [
            # Poker play tags
            (TagCategory.POKER_PLAY, "preflop_allin", "프리플랍 올인"),
            (TagCategory.POKER_PLAY, "cooler", "쿨러"),
            (TagCategory.POKER_PLAY, "bluff", "블러프"),
            (TagCategory.POKER_PLAY, "hero_call", "히어로 콜"),
            (TagCategory.POKER_PLAY, "suckout", "석아웃"),
            (TagCategory.POKER_PLAY, "bad_beat", "배드 비트"),
            (TagCategory.POKER_PLAY, "slow_play", "슬로우 플레이"),
            (TagCategory.POKER_PLAY, "check_raise", "체크 레이즈"),
            (TagCategory.POKER_PLAY, "value_bet", "밸류 벳"),
            (TagCategory.POKER_PLAY, "river_bluff", "리버 블러프"),
            # Emotion tags
            (TagCategory.EMOTION, "stressed", "긴장"),
            (TagCategory.EMOTION, "excitement", "흥분"),
            (TagCategory.EMOTION, "relief", "안도"),
            (TagCategory.EMOTION, "pain", "고통"),
            (TagCategory.EMOTION, "laughing", "웃음"),
            (TagCategory.EMOTION, "frustration", "좌절"),
            # Epic hand tags
            (TagCategory.EPIC_HAND, "royal_flush", "로열 플러시"),
            (TagCategory.EPIC_HAND, "quads", "포카드"),
            (TagCategory.EPIC_HAND, "straight_flush", "스트레이트 플러시"),
            (TagCategory.EPIC_HAND, "full_house_vs_full_house", "풀하우스 vs 풀하우스"),
            # Runout tags
            (TagCategory.RUNOUT, "runner_runner", "러너러너"),
            (TagCategory.RUNOUT, "one_outer", "원 아우터"),
            (TagCategory.RUNOUT, "backdoor", "백도어"),
        ]
        for category, name, display_name in default_tags:
            existing = await self.get_by_category_and_name(category, name)
            if existing is None:
                tag = await self.create_tag(
                    category=category,
                    name=name,
                    name_display=display_name,
                )
                tags.append(tag)
        return tags

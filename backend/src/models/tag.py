"""Tag model - 블럭 C (Hand Analysis Agent)."""

from typing import TYPE_CHECKING, Optional
from uuid import UUID, uuid4

from sqlalchemy import String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin
from .hand_clip import hand_clip_tags

if TYPE_CHECKING:
    from .hand_clip import HandClip


class Tag(Base, TimestampMixin):
    """태그 마스터."""

    __tablename__ = "tags"
    __table_args__ = (
        UniqueConstraint("category", "name"),
        {"schema": "pokervod"},
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    category: Mapped[str] = mapped_column(String(50), index=True)
    name: Mapped[str] = mapped_column(String(100), index=True)
    name_display: Mapped[Optional[str]] = mapped_column(String(100), default=None)
    description: Mapped[Optional[str]] = mapped_column(Text, default=None)
    sort_order: Mapped[int] = mapped_column(default=0)
    is_active: Mapped[bool] = mapped_column(default=True)

    # Relationships
    hand_clips: Mapped[list["HandClip"]] = relationship(
        secondary=hand_clip_tags, back_populates="tags"
    )

    def __repr__(self) -> str:
        return f"<Tag(category={self.category}, name={self.name})>"


# 태그 카테고리
class TagCategory:
    POKER_PLAY = "poker_play"
    EMOTION = "emotion"
    EPIC_HAND = "epic_hand"
    RUNOUT = "runout"
    ADJECTIVE = "adjective"


# 포커 플레이 태그 예시
class PokerPlayTag:
    PREFLOP_ALLIN = "preflop_allin"
    COOLER = "cooler"
    BLUFF = "bluff"
    HERO_CALL = "hero_call"
    SUCKOUT = "suckout"
    BAD_BEAT = "bad_beat"


# 감정 태그 예시
class EmotionTag:
    STRESSED = "stressed"
    EXCITEMENT = "excitement"
    RELIEF = "relief"
    PAIN = "pain"
    LAUGHING = "laughing"

"""Player model - 블럭 C (Hand Analysis Agent)."""

from decimal import Decimal
from typing import TYPE_CHECKING, Optional
from uuid import UUID, uuid4

from sqlalchemy import Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin
from .hand_clip import hand_clip_players

if TYPE_CHECKING:
    from .hand_clip import HandClip


class Player(Base, TimestampMixin):
    """포커 플레이어 정보."""

    __tablename__ = "players"
    __table_args__ = {"schema": "pokervod"}

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(String(200), unique=True, index=True)
    name_display: Mapped[Optional[str]] = mapped_column(String(200), default=None)
    nationality: Mapped[Optional[str]] = mapped_column(String(100), default=None)
    hendon_mob_id: Mapped[Optional[str]] = mapped_column(String(50), default=None)
    total_live_earnings: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(15, 2), default=None
    )
    wsop_bracelets: Mapped[int] = mapped_column(default=0)
    is_active: Mapped[bool] = mapped_column(default=True)

    # Relationships
    hand_clips: Mapped[list["HandClip"]] = relationship(
        secondary=hand_clip_players, back_populates="players"
    )

    def __repr__(self) -> str:
        return f"<Player(name={self.name})>"

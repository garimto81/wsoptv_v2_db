"""Event model - 블럭 B (Catalog Agent)."""

from decimal import Decimal
from typing import TYPE_CHECKING, Optional
from uuid import UUID, uuid4

from sqlalchemy import ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin

if TYPE_CHECKING:
    from .episode import Episode
    from .season import Season


class Event(Base, TimestampMixin):
    """토너먼트/이벤트."""

    __tablename__ = "events"
    __table_args__ = {"schema": "pokervod"}

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    season_id: Mapped[UUID] = mapped_column(
        ForeignKey("pokervod.seasons.id", ondelete="CASCADE")
    )
    event_number: Mapped[Optional[int]] = mapped_column(default=None, index=True)
    name: Mapped[str] = mapped_column(String(500))
    name_short: Mapped[Optional[str]] = mapped_column(String(100), default=None)
    event_type: Mapped[Optional[str]] = mapped_column(String(50), default=None)
    game_type: Mapped[Optional[str]] = mapped_column(String(50), default=None)
    buy_in: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2), default=None)
    gtd_amount: Mapped[Optional[Decimal]] = mapped_column(Numeric(15, 2), default=None)
    venue: Mapped[Optional[str]] = mapped_column(String(200), default=None)
    status: Mapped[str] = mapped_column(String(20), default="upcoming")

    # Relationships
    season: Mapped["Season"] = relationship(back_populates="events")
    episodes: Mapped[list["Episode"]] = relationship(
        back_populates="event", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Event(number={self.event_number}, name={self.name})>"


# 이벤트 타입
class EventType:
    BRACELET = "bracelet"
    CIRCUIT = "circuit"
    SUPER_CIRCUIT = "super_circuit"
    HIGH_ROLLER = "high_roller"
    SUPER_HIGH_ROLLER = "super_high_roller"
    CASH_GAME = "cash_game"
    TV_SERIES = "tv_series"
    MYSTERY_BOUNTY = "mystery_bounty"
    MAIN_EVENT = "main_event"


# 게임 타입
class GameType:
    NLHE = "NLHE"
    PLO = "PLO"
    PLO8 = "PLO8"
    MIXED = "Mixed"
    STUD = "Stud"
    RAZZ = "Razz"
    HORSE = "HORSE"
    TRIPLE_DRAW = "2-7TD"

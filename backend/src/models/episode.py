"""Episode model - 블럭 B (Catalog Agent)."""

from typing import TYPE_CHECKING, Optional
from uuid import UUID, uuid4

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin

if TYPE_CHECKING:
    from .event import Event
    from .hand_clip import HandClip
    from .video_file import VideoFile


class Episode(Base, TimestampMixin):
    """영상 에피소드 단위."""

    __tablename__ = "episodes"
    __table_args__ = {"schema": "pokervod"}

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    event_id: Mapped[UUID] = mapped_column(
        ForeignKey("pokervod.events.id", ondelete="CASCADE")
    )
    episode_number: Mapped[Optional[int]] = mapped_column(default=None)
    day_number: Mapped[Optional[int]] = mapped_column(default=None)
    part_number: Mapped[Optional[int]] = mapped_column(default=None)
    title: Mapped[Optional[str]] = mapped_column(String(500), default=None)
    episode_type: Mapped[Optional[str]] = mapped_column(String(50), default=None)
    table_type: Mapped[Optional[str]] = mapped_column(String(50), default=None)
    duration_seconds: Mapped[Optional[int]] = mapped_column(default=None)

    # Relationships
    event: Mapped["Event"] = relationship(back_populates="episodes")
    video_files: Mapped[list["VideoFile"]] = relationship(
        back_populates="episode", cascade="all, delete-orphan"
    )
    hand_clips: Mapped[list["HandClip"]] = relationship(
        back_populates="episode", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Episode(number={self.episode_number}, title={self.title})>"


# 에피소드 타입
class EpisodeType:
    FULL = "full"
    HIGHLIGHT = "highlight"
    RECAP = "recap"
    INTERVIEW = "interview"
    SUBCLIP = "subclip"


# 테이블 타입
class TableType:
    PRELIMINARY = "preliminary"
    DAY1 = "day1"
    DAY2 = "day2"
    DAY3 = "day3"
    FINAL_TABLE = "final_table"
    HEADS_UP = "heads_up"

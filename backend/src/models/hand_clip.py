"""HandClip model - 블럭 C (Hand Analysis Agent)."""

from typing import TYPE_CHECKING, Optional
from uuid import UUID, uuid4

from sqlalchemy import Column, ForeignKey, String, Table, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin

if TYPE_CHECKING:
    from .episode import Episode
    from .player import Player
    from .tag import Tag
    from .video_file import VideoFile

# N:N 연결 테이블
hand_clip_tags = Table(
    "hand_clip_tags",
    Base.metadata,
    Column("hand_clip_id", ForeignKey("pokervod.hand_clips.id", ondelete="CASCADE")),
    Column("tag_id", ForeignKey("pokervod.tags.id", ondelete="CASCADE")),
    schema="pokervod",
)

hand_clip_players = Table(
    "hand_clip_players",
    Base.metadata,
    Column("hand_clip_id", ForeignKey("pokervod.hand_clips.id", ondelete="CASCADE")),
    Column("player_id", ForeignKey("pokervod.players.id", ondelete="CASCADE")),
    schema="pokervod",
)


class HandClip(Base, TimestampMixin):
    """포커 핸드 분석 클립."""

    __tablename__ = "hand_clips"
    __table_args__ = (
        UniqueConstraint("sheet_source", "sheet_row_number"),
        {"schema": "pokervod"},
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    episode_id: Mapped[Optional[UUID]] = mapped_column(
        ForeignKey("pokervod.episodes.id", ondelete="SET NULL"), default=None
    )
    video_file_id: Mapped[Optional[UUID]] = mapped_column(
        ForeignKey("pokervod.video_files.id", ondelete="SET NULL"),
        default=None,
        index=True,
    )

    # Sheet tracking
    sheet_source: Mapped[Optional[str]] = mapped_column(String(50), default=None)
    sheet_row_number: Mapped[Optional[int]] = mapped_column(default=None)

    # NAS 매칭용 (Sheets의 "Nas Folder Link" 컬럼)
    nas_folder_link: Mapped[Optional[str]] = mapped_column(String(1000), default=None)
    sheet_file_name: Mapped[Optional[str]] = mapped_column(String(500), default=None)

    # Content
    title: Mapped[Optional[str]] = mapped_column(String(500), default=None)
    timecode: Mapped[Optional[str]] = mapped_column(String(20), default=None)
    timecode_end: Mapped[Optional[str]] = mapped_column(String(20), default=None)
    duration_seconds: Mapped[Optional[int]] = mapped_column(default=None)
    notes: Mapped[Optional[str]] = mapped_column(Text, default=None)

    # Hand info
    hand_grade: Mapped[Optional[str]] = mapped_column(String(10), default=None)
    pot_size: Mapped[Optional[int]] = mapped_column(default=None)
    winner_hand: Mapped[Optional[str]] = mapped_column(String(50), default=None)
    hands_involved: Mapped[Optional[str]] = mapped_column(String(100), default=None)

    # Relationships
    episode: Mapped[Optional["Episode"]] = relationship(back_populates="hand_clips")
    video_file: Mapped[Optional["VideoFile"]] = relationship(
        back_populates="hand_clips"
    )
    tags: Mapped[list["Tag"]] = relationship(
        secondary=hand_clip_tags, back_populates="hand_clips"
    )
    players: Mapped[list["Player"]] = relationship(
        secondary=hand_clip_players, back_populates="hand_clips"
    )

    def __repr__(self) -> str:
        return f"<HandClip(title={self.title}, grade={self.hand_grade})>"


# 핸드 등급
class HandGrade:
    ONE_STAR = "★"
    TWO_STAR = "★★"
    THREE_STAR = "★★★"

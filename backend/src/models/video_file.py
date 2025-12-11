"""VideoFile model - 블럭 A (NAS Inventory Agent)."""

from datetime import datetime
from typing import TYPE_CHECKING, Optional
from uuid import UUID, uuid4

from sqlalchemy import BigInteger, DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin

if TYPE_CHECKING:
    from .episode import Episode
    from .hand_clip import HandClip
    from .nas_file import NASFile


class VideoFile(Base, TimestampMixin):
    """비디오 파일 메타데이터."""

    __tablename__ = "video_files"
    __table_args__ = {"schema": "pokervod"}

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    episode_id: Mapped[Optional[UUID]] = mapped_column(
        ForeignKey("pokervod.episodes.id", ondelete="SET NULL"), default=None
    )

    # File info
    file_path: Mapped[str] = mapped_column(String(1000), unique=True, index=True)
    file_name: Mapped[str] = mapped_column(String(500))
    file_size_bytes: Mapped[Optional[int]] = mapped_column(BigInteger, default=None)
    file_format: Mapped[Optional[str]] = mapped_column(String(20), default=None)
    file_mtime: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), default=None
    )

    # Video metadata
    resolution: Mapped[Optional[str]] = mapped_column(String(20), default=None)
    video_codec: Mapped[Optional[str]] = mapped_column(String(50), default=None)
    audio_codec: Mapped[Optional[str]] = mapped_column(String(50), default=None)
    bitrate_kbps: Mapped[Optional[int]] = mapped_column(default=None)
    duration_seconds: Mapped[Optional[int]] = mapped_column(default=None)
    version_type: Mapped[Optional[str]] = mapped_column(String(20), default=None)
    is_original: Mapped[bool] = mapped_column(default=False)

    # Catalog display
    display_title: Mapped[Optional[str]] = mapped_column(String(500), default=None)
    content_type: Mapped[Optional[str]] = mapped_column(String(20), default=None)
    catalog_title: Mapped[Optional[str]] = mapped_column(String(300), default=None)
    is_catalog_item: Mapped[bool] = mapped_column(default=False)

    # Filtering
    is_hidden: Mapped[bool] = mapped_column(default=False)
    hidden_reason: Mapped[Optional[str]] = mapped_column(String(50), default=None)
    scan_status: Mapped[str] = mapped_column(String(20), default="pending")

    # Relationships
    episode: Mapped[Optional["Episode"]] = relationship(back_populates="video_files")
    hand_clips: Mapped[list["HandClip"]] = relationship(back_populates="video_file")
    nas_file: Mapped[Optional["NASFile"]] = relationship(back_populates="video_file")

    def __repr__(self) -> str:
        return f"<VideoFile(name={self.file_name})>"


# 버전 타입
class VersionType:
    CLEAN = "clean"
    MASTERED = "mastered"
    STREAM = "stream"
    SUBCLIP = "subclip"
    FINAL_EDIT = "final_edit"
    NOBUG = "nobug"
    PGM = "pgm"
    HIRES = "hires"
    GENERIC = "generic"

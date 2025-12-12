"""NASFile model - 블럭 A (NAS Inventory Agent)."""

from datetime import datetime
from typing import TYPE_CHECKING, Optional
from uuid import UUID, uuid4

from sqlalchemy import BigInteger, DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin

if TYPE_CHECKING:
    from .nas_folder import NASFolder
    from .video_file import VideoFile


class NASFile(Base, TimestampMixin):
    """NAS 파일 인벤토리."""

    __tablename__ = "nas_files"
    __table_args__ = {"schema": "pokervod"}

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    file_path: Mapped[str] = mapped_column(String(1000), unique=True, index=True)
    file_name: Mapped[str] = mapped_column(String(500))
    file_size_bytes: Mapped[int] = mapped_column(BigInteger, default=0)
    file_extension: Mapped[Optional[str]] = mapped_column(String(20), default=None)
    file_mtime: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), default=None
    )

    # Classification
    file_category: Mapped[str] = mapped_column(String(20), default="other")
    is_hidden_file: Mapped[bool] = mapped_column(default=False)
    is_excluded: Mapped[bool] = mapped_column(default=False)
    exclude_reason: Mapped[Optional[str]] = mapped_column(String(100), default=None)

    # Foreign keys
    video_file_id: Mapped[Optional[UUID]] = mapped_column(
        ForeignKey("pokervod.video_files.id", ondelete="SET NULL"), default=None
    )
    folder_id: Mapped[Optional[UUID]] = mapped_column(
        ForeignKey("pokervod.nas_folders.id", ondelete="SET NULL"), default=None
    )

    # Relationships
    video_file: Mapped[Optional["VideoFile"]] = relationship(back_populates="nas_file")
    folder: Mapped[Optional["NASFolder"]] = relationship(back_populates="files")

    def __repr__(self) -> str:
        return f"<NASFile(name={self.file_name})>"


# 파일 카테고리
class FileCategory:
    VIDEO = "video"
    METADATA = "metadata"
    SYSTEM = "system"
    ARCHIVE = "archive"
    OTHER = "other"

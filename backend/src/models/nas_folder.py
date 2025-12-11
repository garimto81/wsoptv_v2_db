"""NASFolder model - 블럭 A (NAS Inventory Agent)."""

from typing import TYPE_CHECKING, Optional
from uuid import UUID, uuid4

from sqlalchemy import BigInteger, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin

if TYPE_CHECKING:
    from .nas_file import NASFile


class NASFolder(Base, TimestampMixin):
    """NAS 폴더 구조."""

    __tablename__ = "nas_folders"
    __table_args__ = {"schema": "pokervod"}

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    folder_path: Mapped[str] = mapped_column(String(1000), unique=True, index=True)
    folder_name: Mapped[str] = mapped_column(String(500))
    parent_path: Mapped[Optional[str]] = mapped_column(String(1000), default=None)
    depth: Mapped[int] = mapped_column(default=0)

    # Statistics
    file_count: Mapped[int] = mapped_column(default=0)
    folder_count: Mapped[int] = mapped_column(default=0)
    total_size_bytes: Mapped[int] = mapped_column(BigInteger, default=0)

    # Metadata
    is_empty: Mapped[bool] = mapped_column(default=True)
    is_hidden_folder: Mapped[bool] = mapped_column(default=False)

    # Relationships
    files: Mapped[list["NASFile"]] = relationship(
        back_populates="folder", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<NASFolder(path={self.folder_path})>"

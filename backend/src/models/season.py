"""Season model - 블럭 B (Catalog Agent)."""

from typing import TYPE_CHECKING, Optional
from uuid import UUID, uuid4

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin

if TYPE_CHECKING:
    from .event import Event
    from .project import Project


class Season(Base, TimestampMixin):
    """연도별 시즌."""

    __tablename__ = "seasons"
    __table_args__ = {"schema": "pokervod"}

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    project_id: Mapped[UUID] = mapped_column(
        ForeignKey("pokervod.projects.id", ondelete="CASCADE")
    )
    year: Mapped[int] = mapped_column(index=True)
    name: Mapped[str] = mapped_column(String(200))
    location: Mapped[Optional[str]] = mapped_column(String(200), default=None)
    sub_category: Mapped[Optional[str]] = mapped_column(String(50), default=None)
    status: Mapped[str] = mapped_column(String(20), default="active")

    # Relationships
    project: Mapped["Project"] = relationship(back_populates="seasons")
    events: Mapped[list["Event"]] = relationship(
        back_populates="season", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Season(year={self.year}, name={self.name})>"


# WSOP 서브 카테고리
class SubCategory:
    ARCHIVE = "ARCHIVE"
    BRACELET_LV = "BRACELET_LV"
    BRACELET_EU = "BRACELET_EU"
    BRACELET_PARA = "BRACELET_PARA"
    CIRCUIT = "CIRCUIT"
    SUPER_CIRCUIT = "SUPER_CIRCUIT"

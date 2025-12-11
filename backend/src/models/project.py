"""Project model - 블럭 B (Catalog Agent)."""

from typing import TYPE_CHECKING, Optional
from uuid import UUID, uuid4

from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin

if TYPE_CHECKING:
    from .season import Season


class Project(Base, TimestampMixin):
    """포커 프로젝트 (WSOP, HCL, GGMillions 등)."""

    __tablename__ = "projects"
    __table_args__ = {"schema": "pokervod"}

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    code: Mapped[str] = mapped_column(String(20), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(200))
    description: Mapped[Optional[str]] = mapped_column(Text, default=None)
    nas_base_path: Mapped[Optional[str]] = mapped_column(String(500), default=None)
    filename_pattern: Mapped[Optional[str]] = mapped_column(String(500), default=None)
    is_active: Mapped[bool] = mapped_column(default=True)

    # Relationships
    seasons: Mapped[list["Season"]] = relationship(
        back_populates="project", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Project(code={self.code}, name={self.name})>"


# 7개 프로젝트 코드 상수
class ProjectCode:
    WSOP = "WSOP"
    HCL = "HCL"
    GGMILLIONS = "GGMILLIONS"
    MPP = "MPP"
    PAD = "PAD"
    GOG = "GOG"
    OTHER = "OTHER"

    ALL = [WSOP, HCL, GGMILLIONS, MPP, PAD, GOG, OTHER]

"""CatalogItem model - Netflix-style 플랫 카탈로그."""

from typing import Optional
from uuid import UUID, uuid4

from sqlalchemy import ForeignKey, Integer, String, Text, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin


class CatalogItem(Base, TimestampMixin):
    """Netflix-style 카탈로그 아이템 (플랫 구조).

    VideoFile을 기반으로 UI 표시에 최적화된 데이터를 저장.
    Browse, Featured, Top10 API에서 직접 조회.
    """

    __tablename__ = "catalog_items"
    __table_args__ = {"schema": "pokervod"}

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)

    # 표시 정보
    display_title: Mapped[str] = mapped_column(String(500))
    # "WSOP 2024 Event #21 Final Table"
    catalog_title: Mapped[Optional[str]] = mapped_column(String(300), default=None)
    # "Event #21 - $10K NLHE Final"
    description: Mapped[Optional[str]] = mapped_column(Text, default=None)
    thumbnail_url: Mapped[Optional[str]] = mapped_column(String(500), default=None)
    duration_seconds: Mapped[Optional[int]] = mapped_column(Integer, default=None)

    # 분류
    project_code: Mapped[str] = mapped_column(String(20), index=True)
    # "WSOP", "PAD", "GOG", etc.
    category: Mapped[Optional[str]] = mapped_column(String(50), default=None)
    # "tournament", "cash_game", "tv_series"
    content_type: Mapped[Optional[str]] = mapped_column(String(20), default=None)
    # "full", "highlight", "recap"
    tags: Mapped[Optional[list[str]]] = mapped_column(JSON, default=None)
    # ["final_table", "high_roller", "nlhe"]

    # 정렬/필터용 메타데이터
    year: Mapped[Optional[int]] = mapped_column(Integer, index=True, default=None)
    event_number: Mapped[Optional[int]] = mapped_column(Integer, default=None)
    episode_number: Mapped[Optional[int]] = mapped_column(Integer, default=None)
    day_number: Mapped[Optional[int]] = mapped_column(Integer, default=None)

    # Featured/Top10 순위
    featured_rank: Mapped[Optional[int]] = mapped_column(Integer, default=None)
    # Hero 배너용 (1~5)
    top10_rank: Mapped[Optional[int]] = mapped_column(Integer, default=None)
    # Top 10 리스트용

    # 추가 메타데이터 (JSON)
    extra_metadata: Mapped[Optional[dict]] = mapped_column(JSON, default=None)
    # {"buy_in": 10000, "game_type": "NLHE", "venue": "Las Vegas"}

    # 상태
    is_published: Mapped[bool] = mapped_column(default=True)
    is_featured: Mapped[bool] = mapped_column(default=False)

    # 원본 참조
    video_file_id: Mapped[UUID] = mapped_column(
        ForeignKey("pokervod.video_files.id", ondelete="CASCADE"),
        unique=True,
        index=True
    )
    episode_id: Mapped[Optional[UUID]] = mapped_column(
        ForeignKey("pokervod.episodes.id", ondelete="SET NULL"),
        default=None
    )

    def __repr__(self) -> str:
        return f"<CatalogItem(title={self.display_title[:30]}...)>"


# 카탈로그 카테고리
class CatalogCategory:
    TOURNAMENT = "tournament"
    CASH_GAME = "cash_game"
    TV_SERIES = "tv_series"
    HIGHLIGHT = "highlight"
    INTERVIEW = "interview"


# 콘텐츠 타입
class ContentType:
    FULL = "full"
    HIGHLIGHT = "highlight"
    RECAP = "recap"
    INTERVIEW = "interview"
    CLIP = "clip"

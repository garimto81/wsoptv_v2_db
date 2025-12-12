"""CatalogItemService - Netflix-style 카탈로그 관리.

VideoFile → CatalogItem 변환 및 Browse/Featured/Top10 조회.
"""

from typing import Optional, Sequence
from uuid import UUID

from sqlalchemy import and_, desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from ...models import (
    CatalogItem,
    Episode,
    Event,
    Project,
    Season,
    VideoFile,
)
from ..file_parser.base_parser import ParsedMetadata
from ..file_parser.title_generator import TitleGenerator
from .base_service import BaseService


class CatalogItemService(BaseService[CatalogItem]):
    """Netflix-style 카탈로그 아이템 서비스."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, CatalogItem)
        self.title_generator = TitleGenerator()

    # ============================================
    # Browse/Featured/Top10 조회
    # ============================================

    async def get_browse_items(
        self,
        *,
        project_code: Optional[str] = None,
        category: Optional[str] = None,
        year: Optional[int] = None,
        skip: int = 0,
        limit: int = 20,
    ) -> Sequence[CatalogItem]:
        """Browse 페이지용 카탈로그 조회.

        Args:
            project_code: 프로젝트 필터 (WSOP, PAD 등)
            category: 카테고리 필터 (tournament, cash_game 등)
            year: 연도 필터
            skip: 페이지네이션 오프셋
            limit: 페이지 크기

        Returns:
            CatalogItem 리스트
        """
        query = select(CatalogItem).where(CatalogItem.is_published == True)

        if project_code:
            query = query.where(CatalogItem.project_code == project_code)
        if category:
            query = query.where(CatalogItem.category == category)
        if year:
            query = query.where(CatalogItem.year == year)

        query = query.order_by(
            desc(CatalogItem.year),
            desc(CatalogItem.event_number),
            CatalogItem.episode_number,
        ).offset(skip).limit(limit)

        result = await self.session.execute(query)
        return result.scalars().all()

    async def get_featured_items(self, limit: int = 5) -> Sequence[CatalogItem]:
        """Hero 배너용 Featured 아이템 조회.

        Args:
            limit: 최대 개수 (기본 5)

        Returns:
            featured_rank 순으로 정렬된 CatalogItem 리스트
        """
        query = (
            select(CatalogItem)
            .where(
                and_(
                    CatalogItem.is_published == True,
                    CatalogItem.is_featured == True,
                    CatalogItem.featured_rank.isnot(None),
                )
            )
            .order_by(CatalogItem.featured_rank)
            .limit(limit)
        )
        result = await self.session.execute(query)
        return result.scalars().all()

    async def get_top10_items(
        self,
        project_code: Optional[str] = None,
    ) -> Sequence[CatalogItem]:
        """Top 10 리스트 조회.

        Args:
            project_code: 프로젝트 필터 (없으면 전체)

        Returns:
            top10_rank 순으로 정렬된 최대 10개 CatalogItem
        """
        query = (
            select(CatalogItem)
            .where(
                and_(
                    CatalogItem.is_published == True,
                    CatalogItem.top10_rank.isnot(None),
                )
            )
        )

        if project_code:
            query = query.where(CatalogItem.project_code == project_code)

        query = query.order_by(CatalogItem.top10_rank).limit(10)
        result = await self.session.execute(query)
        return result.scalars().all()

    async def get_by_project(
        self,
        project_code: str,
        *,
        skip: int = 0,
        limit: int = 50,
    ) -> Sequence[CatalogItem]:
        """프로젝트별 카탈로그 조회."""
        query = (
            select(CatalogItem)
            .where(
                and_(
                    CatalogItem.is_published == True,
                    CatalogItem.project_code == project_code,
                )
            )
            .order_by(desc(CatalogItem.year), desc(CatalogItem.created_at))
            .offset(skip)
            .limit(limit)
        )
        result = await self.session.execute(query)
        return result.scalars().all()

    # ============================================
    # VideoFile → CatalogItem 변환
    # ============================================

    async def create_from_video_file(
        self,
        video_file: VideoFile,
        metadata: Optional[ParsedMetadata] = None,
    ) -> CatalogItem:
        """VideoFile에서 CatalogItem 생성.

        Args:
            video_file: 원본 VideoFile
            metadata: 파싱된 메타데이터 (없으면 video_file에서 추출)

        Returns:
            생성된 CatalogItem
        """
        # 기존 CatalogItem 확인
        existing = await self.get_by_video_file_id(video_file.id)
        if existing:
            return existing

        # 메타데이터에서 제목 생성
        if metadata:
            display_title, catalog_title = self.title_generator.generate(metadata)
            project_code = metadata.project_code or "OTHER"
            year = metadata.year
            event_number = metadata.event_number
            episode_number = metadata.episode_number
            day_number = metadata.day_number
            category = self._determine_category(metadata)
            tags = self._extract_tags(metadata)
            extra_metadata = self._build_extra_metadata(metadata)
        else:
            # video_file에서 직접 추출
            display_title = video_file.display_title or video_file.file_name
            catalog_title = video_file.catalog_title
            project_code = await self._get_project_code(video_file)
            year = None
            event_number = None
            episode_number = None
            day_number = None
            category = None
            tags = None
            extra_metadata = None

        catalog_item = CatalogItem(
            display_title=display_title,
            catalog_title=catalog_title,
            duration_seconds=video_file.duration_seconds,
            project_code=project_code,
            category=category,
            content_type=video_file.content_type,
            tags=tags,
            year=year,
            event_number=event_number,
            episode_number=episode_number,
            day_number=day_number,
            extra_metadata=extra_metadata,
            video_file_id=video_file.id,
            episode_id=video_file.episode_id,
        )

        self.session.add(catalog_item)
        await self.session.flush()
        await self.session.refresh(catalog_item)
        return catalog_item

    async def get_by_video_file_id(
        self, video_file_id: UUID
    ) -> Optional[CatalogItem]:
        """VideoFile ID로 CatalogItem 조회."""
        result = await self.session.execute(
            select(CatalogItem).where(CatalogItem.video_file_id == video_file_id)
        )
        return result.scalar_one_or_none()

    async def sync_from_video_files(
        self,
        video_files: Sequence[VideoFile],
        metadata_map: Optional[dict[UUID, ParsedMetadata]] = None,
    ) -> tuple[int, int]:
        """여러 VideoFile을 CatalogItem으로 동기화.

        Args:
            video_files: 동기화할 VideoFile 리스트
            metadata_map: video_file_id → ParsedMetadata 매핑

        Returns:
            (생성 수, 스킵 수) 튜플
        """
        created = 0
        skipped = 0
        metadata_map = metadata_map or {}

        for vf in video_files:
            # 숨김 파일 스킵
            if vf.is_hidden:
                skipped += 1
                continue

            # 이미 존재하면 스킵
            existing = await self.get_by_video_file_id(vf.id)
            if existing:
                skipped += 1
                continue

            # CatalogItem 생성
            metadata = metadata_map.get(vf.id)
            await self.create_from_video_file(vf, metadata)
            created += 1

        return created, skipped

    # ============================================
    # Featured/Top10 관리
    # ============================================

    async def set_featured(
        self,
        catalog_item_id: UUID,
        rank: int,
    ) -> Optional[CatalogItem]:
        """CatalogItem을 Featured로 설정."""
        item = await self.get_by_id(catalog_item_id)
        if not item:
            return None

        item.is_featured = True
        item.featured_rank = rank
        await self.session.flush()
        await self.session.refresh(item)
        return item

    async def set_top10(
        self,
        catalog_item_id: UUID,
        rank: int,
    ) -> Optional[CatalogItem]:
        """CatalogItem을 Top10으로 설정."""
        if rank < 1 or rank > 10:
            raise ValueError("Top10 rank must be between 1 and 10")

        item = await self.get_by_id(catalog_item_id)
        if not item:
            return None

        item.top10_rank = rank
        await self.session.flush()
        await self.session.refresh(item)
        return item

    # ============================================
    # 헬퍼 메서드
    # ============================================

    def _determine_category(self, metadata: ParsedMetadata) -> Optional[str]:
        """메타데이터에서 카테고리 결정."""
        project = metadata.project_code or ""

        if project in ("WSOP", "WSOP_BRACELET", "WSOP_CIRCUIT", "MPP"):
            return "tournament"
        elif project == "HCL":
            return "cash_game"
        elif project in ("GOG", "PAD"):
            return "tv_series"
        elif project == "GGMILLIONS":
            return "tournament"  # High Roller도 토너먼트
        return None

    def _extract_tags(self, metadata: ParsedMetadata) -> Optional[list[str]]:
        """메타데이터에서 태그 추출."""
        tags = []

        if metadata.table_type:
            tags.append(metadata.table_type)
        if metadata.game_type:
            tags.append(metadata.game_type.lower())
        if metadata.extra.get("sub_category"):
            tags.append(metadata.extra["sub_category"].lower())
        if metadata.version_type and metadata.version_type != "generic":
            tags.append(metadata.version_type)

        return tags if tags else None

    def _build_extra_metadata(self, metadata: ParsedMetadata) -> Optional[dict]:
        """추가 메타데이터 JSON 구성."""
        extra = {}

        if metadata.buy_in:
            extra["buy_in"] = metadata.buy_in
        if metadata.game_type:
            extra["game_type"] = metadata.game_type
        if metadata.location:
            extra["venue"] = metadata.location
        if metadata.featured_player:
            extra["featured_player"] = metadata.featured_player

        return extra if extra else None

    async def _get_project_code(self, video_file: VideoFile) -> str:
        """VideoFile에서 project_code 추출."""
        if not video_file.episode_id:
            return "OTHER"

        # Episode → Event → Season → Project 조회
        result = await self.session.execute(
            select(Project.code)
            .select_from(Episode)
            .join(Event, Episode.event_id == Event.id)
            .join(Season, Event.season_id == Season.id)
            .join(Project, Season.project_id == Project.id)
            .where(Episode.id == video_file.episode_id)
        )
        code = result.scalar_one_or_none()
        return code or "OTHER"

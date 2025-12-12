"""CatalogBuilder Service - NAS 파일에서 카탈로그 엔티티 자동 생성.

NAS 파일 파싱 결과를 기반으로 Project → Season → Event → Episode → VideoFile
엔티티를 자동 생성하고 연결합니다.
"""

from dataclasses import dataclass
from typing import Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from decimal import Decimal

from ...models.project import Project
from ...models.season import Season
from ...models.event import Event
from ...models.episode import Episode
from ...models.video_file import VideoFile
from ...models.nas_file import NASFile, FileCategory
from ..file_parser import ParserFactory, ParsedMetadata, TitleGenerator


# 카탈로그 빌드 시 제외할 경로 패턴
EXCLUDED_PATHS = [
    "/Clips/",
    "\\Clips\\",
    "Clips/",
    "/Player Emotion",
    "\\Player Emotion",
    "Player Emotion/",
]


@dataclass
class BuildStats:
    """카탈로그 빌드 통계."""

    nas_files_processed: int = 0
    projects_created: int = 0
    seasons_created: int = 0
    events_created: int = 0
    episodes_created: int = 0
    video_files_created: int = 0
    links_created: int = 0
    skipped: int = 0
    errors: int = 0
    error_messages: list[str] = None

    def __post_init__(self):
        if self.error_messages is None:
            self.error_messages = []


class CatalogBuilderService:
    """NAS 파일에서 카탈로그 엔티티를 자동 생성하는 서비스."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.title_generator = TitleGenerator()
        self._project_cache: dict[str, Project] = {}
        self._season_cache: dict[tuple[UUID, int], Season] = {}
        self._event_cache: dict[tuple[UUID, int], Event] = {}

    async def build_catalog_from_nas(
        self,
        *,
        limit: int = 10000,
        skip_linked: bool = True,
    ) -> BuildStats:
        """NAS 파일에서 카탈로그 엔티티를 자동 생성합니다.

        Args:
            limit: 처리할 최대 파일 수
            skip_linked: 이미 VideoFile에 연결된 파일은 스킵

        Returns:
            빌드 통계
        """
        stats = BuildStats()

        # 비디오 파일 조회
        query = (
            select(NASFile)
            .where(NASFile.file_category == FileCategory.VIDEO)
        )
        if skip_linked:
            query = query.where(NASFile.video_file_id == None)  # noqa: E711

        query = query.limit(limit)
        result = await self.session.execute(query)
        nas_files = result.scalars().all()

        for nas_file in nas_files:
            stats.nas_files_processed += 1

            try:
                # 제외 경로 확인
                if self._is_excluded_path(nas_file.file_path):
                    stats.skipped += 1
                    continue

                # 파일명 파싱
                parser = ParserFactory.get_parser(nas_file.file_name, nas_file.file_path)
                metadata = parser.parse(nas_file.file_name, nas_file.file_path)

                if not metadata.project_code or metadata.project_code == "UNKNOWN":
                    stats.skipped += 1
                    continue

                # Project 생성 또는 조회
                project = await self._get_or_create_project(metadata, stats)
                if not project:
                    stats.errors += 1
                    continue

                # Season 생성 또는 조회
                season = await self._get_or_create_season(project.id, metadata, stats)
                if not season:
                    stats.errors += 1
                    continue

                # Event 생성 또는 조회
                event = await self._get_or_create_event(season.id, metadata, stats)
                if not event:
                    stats.errors += 1
                    continue

                # Episode 생성 또는 조회
                episode = await self._get_or_create_episode(event.id, metadata, stats)
                if not episode:
                    stats.errors += 1
                    continue

                # VideoFile 생성 및 NASFile 연결
                video_file = await self._create_video_file(
                    nas_file, episode.id, metadata, stats
                )
                if video_file:
                    # NASFile → VideoFile 연결
                    nas_file.video_file_id = video_file.id
                    stats.links_created += 1

            except Exception as e:
                stats.errors += 1
                stats.error_messages.append(f"{nas_file.file_name}: {str(e)}")

        # 커밋
        await self.session.commit()

        return stats

    async def _get_or_create_project(
        self, metadata: ParsedMetadata, stats: BuildStats
    ) -> Optional[Project]:
        """프로젝트 조회 또는 생성."""
        code = metadata.project_code

        # 캐시 확인
        if code in self._project_cache:
            return self._project_cache[code]

        # DB 조회
        result = await self.session.execute(
            select(Project).where(Project.code == code)
        )
        project = result.scalar_one_or_none()

        if not project:
            # 새 프로젝트 생성
            project = Project(
                code=code,
                name=self._get_project_name(code),
                description=f"Auto-generated from NAS files",
            )
            self.session.add(project)
            await self.session.flush()
            stats.projects_created += 1

        self._project_cache[code] = project
        return project

    async def _get_or_create_season(
        self, project_id: UUID, metadata: ParsedMetadata, stats: BuildStats
    ) -> Optional[Season]:
        """시즌 조회 또는 생성."""
        year = metadata.year or 2024
        cache_key = (project_id, year)

        # 캐시 확인
        if cache_key in self._season_cache:
            return self._season_cache[cache_key]

        # DB 조회
        result = await self.session.execute(
            select(Season)
            .where(Season.project_id == project_id)
            .where(Season.year == year)
        )
        season = result.scalar_one_or_none()

        if not season:
            # 새 시즌 생성
            season = Season(
                project_id=project_id,
                year=year,
                name=f"{year} Season",
                location=metadata.venue or metadata.location,
            )
            self.session.add(season)
            await self.session.flush()
            stats.seasons_created += 1

        self._season_cache[cache_key] = season
        return season

    async def _get_or_create_event(
        self, season_id: UUID, metadata: ParsedMetadata, stats: BuildStats
    ) -> Optional[Event]:
        """이벤트 조회 또는 생성."""
        event_num = metadata.event_number or 1
        cache_key = (season_id, event_num)

        # 캐시 확인
        if cache_key in self._event_cache:
            return self._event_cache[cache_key]

        # DB 조회
        result = await self.session.execute(
            select(Event)
            .where(Event.season_id == season_id)
            .where(Event.event_number == event_num)
        )
        event = result.scalar_one_or_none()

        if not event:
            # 새 이벤트 생성
            event_name = metadata.event_name or f"Event #{event_num}"

            # buy_in 변환 (문자열 → Decimal)
            buy_in_decimal = None
            if metadata.buy_in:
                buy_in_decimal = self._parse_buy_in(metadata.buy_in)

            event = Event(
                season_id=season_id,
                event_number=event_num,
                name=event_name,
                name_short=metadata.event_name_short,
                event_type=metadata.event_type,
                game_type=metadata.game_type,
                buy_in=buy_in_decimal,
            )
            self.session.add(event)
            await self.session.flush()
            stats.events_created += 1

        self._event_cache[cache_key] = event
        return event

    async def _get_or_create_episode(
        self, event_id: UUID, metadata: ParsedMetadata, stats: BuildStats
    ) -> Optional[Episode]:
        """에피소드 조회 또는 생성."""
        ep_num = metadata.episode_number or 1
        day_num = metadata.day_number

        # DB 조회 (이벤트 + 에피소드 번호 + 데이 번호로 매칭)
        query = (
            select(Episode)
            .where(Episode.event_id == event_id)
            .where(Episode.episode_number == ep_num)
        )
        if day_num:
            query = query.where(Episode.day_number == day_num)

        result = await self.session.execute(query)
        episode = result.scalar_one_or_none()

        if not episode:
            # 새 에피소드 생성
            title = metadata.display_title or f"Episode {ep_num}"
            if day_num:
                title = f"Day {day_num} - {title}"

            episode = Episode(
                event_id=event_id,
                episode_number=ep_num,
                day_number=day_num,
                part_number=metadata.part_number,
                title=title,
                episode_type=metadata.episode_type,
                table_type=metadata.table_type,
            )
            self.session.add(episode)
            await self.session.flush()
            stats.episodes_created += 1

        return episode

    async def _create_video_file(
        self,
        nas_file: NASFile,
        episode_id: UUID,
        metadata: ParsedMetadata,
        stats: BuildStats,
    ) -> Optional[VideoFile]:
        """VideoFile 생성."""
        # 이미 같은 경로로 VideoFile이 있는지 확인
        result = await self.session.execute(
            select(VideoFile).where(VideoFile.file_path == nas_file.file_path)
        )
        existing = result.scalar_one_or_none()

        if existing:
            # 이미 존재하면 NASFile만 연결
            nas_file.video_file_id = existing.id
            return existing

        # 제목 생성
        display_title, catalog_title = self.title_generator.generate(metadata)

        # 새 VideoFile 생성
        video_file = VideoFile(
            episode_id=episode_id,
            file_path=nas_file.file_path,
            file_name=nas_file.file_name,
            file_size_bytes=nas_file.file_size_bytes,
            file_format=nas_file.file_extension,
            file_mtime=nas_file.file_mtime,
            display_title=display_title,
            catalog_title=catalog_title,
            content_type=metadata.content_type,
            version_type=metadata.version_type,
            is_catalog_item=True,
            scan_status="parsed",
        )
        self.session.add(video_file)
        await self.session.flush()
        stats.video_files_created += 1

        return video_file

    def _get_project_name(self, code: str) -> str:
        """프로젝트 코드에서 이름 생성."""
        names = {
            "WSOP": "World Series of Poker",
            "WSOP_BRACELET": "World Series of Poker",
            "WSOP_CIRCUIT": "WSOP Circuit",
            "WSOP_ARCHIVE": "WSOP Archive",
            "GGM": "GG Millions",
            "GGMILLIONS": "GG Millions",
            "GOG": "Game of Gold",
            "PAD": "Poker After Dark",
            "MPP": "MPP Tournament",
            "HCL": "Hustler Casino Live",
        }
        return names.get(code, code)

    def _parse_buy_in(self, buy_in_str: str) -> Optional[Decimal]:
        """Buy-in 문자열을 Decimal로 변환.

        예: '25K' → 25000, '1M' → 1000000, '10000' → 10000
        """
        if not buy_in_str:
            return None

        try:
            buy_in_str = buy_in_str.upper().replace(",", "").strip()

            if buy_in_str.endswith("K"):
                return Decimal(buy_in_str[:-1]) * 1000
            elif buy_in_str.endswith("M"):
                return Decimal(buy_in_str[:-1]) * 1000000
            else:
                return Decimal(buy_in_str)
        except Exception:
            return None

    def _is_excluded_path(self, file_path: str) -> bool:
        """제외 경로 여부 확인.

        Clips, Player Emotion 등 카탈로그에 포함하지 않을 폴더 경로 확인.
        """
        if not file_path:
            return False

        for pattern in EXCLUDED_PATHS:
            if pattern in file_path:
                return True
        return False

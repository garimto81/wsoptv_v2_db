"""Path Matcher - PRD 15.3 NAS ↔ Sheets 경로 매칭.

Google Sheets의 "Nas Folder Link" 경로와 NASFile.file_path를 매칭합니다.
"""

import re
from dataclasses import dataclass
from typing import Optional, Sequence
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ...models.hand_clip import HandClip
from ...models.nas_file import NASFile


@dataclass
class MatchResult:
    """경로 매칭 결과."""

    hand_clip_id: UUID
    nas_folder_link: str
    matched_nas_file_id: Optional[UUID] = None
    matched_file_path: Optional[str] = None
    match_type: str = "none"  # exact, partial, fuzzy, none
    confidence: float = 0.0


@dataclass
class MatchStats:
    """매칭 통계."""

    total_clips: int = 0
    matched: int = 0
    unmatched: int = 0
    match_rate: float = 0.0
    exact_matches: int = 0
    partial_matches: int = 0
    fuzzy_matches: int = 0


class PathNormalizer:
    """경로 정규화 유틸리티."""

    # UNC 프리픽스 패턴
    UNC_PREFIX_PATTERN = re.compile(r"^\\\\[^\\]+\\[^\\]+\\")

    # 대체 UNC 패턴 (smb://, file://)
    SMB_PREFIX_PATTERN = re.compile(r"^smb://[^/]+/[^/]+/")
    FILE_PREFIX_PATTERN = re.compile(r"^file://[^/]+/[^/]+/")

    @classmethod
    def normalize(cls, path: str) -> str:
        """경로 정규화.

        1. UNC 프리픽스 제거 (\\\\10.10.100.122\\docker\\)
        2. 백슬래시 → 슬래시 변환
        3. 소문자 변환
        4. 연속 슬래시 정리
        5. 끝 슬래시 제거

        Args:
            path: 원본 경로

        Returns:
            정규화된 경로
        """
        if not path:
            return ""

        # UNC 프리픽스 제거
        path = cls.UNC_PREFIX_PATTERN.sub("", path)
        path = cls.SMB_PREFIX_PATTERN.sub("", path)
        path = cls.FILE_PREFIX_PATTERN.sub("", path)

        # 백슬래시 → 슬래시
        path = path.replace("\\", "/")

        # 소문자 변환
        path = path.lower()

        # 연속 슬래시 정리
        while "//" in path:
            path = path.replace("//", "/")

        # 끝 슬래시 제거
        path = path.rstrip("/")

        return path

    @classmethod
    def extract_folder_path(cls, file_path: str) -> str:
        """파일 경로에서 폴더 경로 추출.

        Args:
            file_path: 파일 전체 경로

        Returns:
            폴더 경로 (파일명 제외)
        """
        normalized = cls.normalize(file_path)
        last_slash = normalized.rfind("/")
        if last_slash > 0:
            return normalized[:last_slash]
        return normalized

    @classmethod
    def extract_filename(cls, file_path: str) -> str:
        """파일 경로에서 파일명 추출.

        Args:
            file_path: 파일 전체 경로

        Returns:
            파일명
        """
        normalized = cls.normalize(file_path)
        last_slash = normalized.rfind("/")
        if last_slash >= 0:
            return normalized[last_slash + 1:]
        return normalized


class PathMatcher:
    """NAS ↔ Sheets 경로 매칭 서비스."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self._nas_cache: dict[str, NASFile] = {}  # normalized_path → NASFile

    async def build_nas_index(self, limit: int = 50000) -> int:
        """NAS 파일 인덱스 구축.

        Args:
            limit: 최대 파일 수

        Returns:
            인덱싱된 파일 수
        """
        result = await self.session.execute(
            select(NASFile).limit(limit)
        )
        nas_files = result.scalars().all()

        self._nas_cache.clear()
        for nas_file in nas_files:
            # 파일 경로로 인덱싱
            normalized = PathNormalizer.normalize(nas_file.file_path)
            self._nas_cache[normalized] = nas_file

            # 폴더 경로로도 인덱싱 (폴더 매칭용)
            folder_path = PathNormalizer.extract_folder_path(nas_file.file_path)
            if folder_path not in self._nas_cache:
                self._nas_cache[folder_path] = nas_file

        return len(nas_files)

    def match_path(self, nas_folder_link: str) -> Optional[MatchResult]:
        """단일 경로 매칭.

        Args:
            nas_folder_link: Sheets의 NAS 폴더 링크

        Returns:
            매칭 결과
        """
        if not nas_folder_link:
            return None

        normalized = PathNormalizer.normalize(nas_folder_link)

        # 1. 정확히 일치
        if normalized in self._nas_cache:
            nas_file = self._nas_cache[normalized]
            return MatchResult(
                hand_clip_id=None,  # 호출자가 설정
                nas_folder_link=nas_folder_link,
                matched_nas_file_id=nas_file.id,
                matched_file_path=nas_file.file_path,
                match_type="exact",
                confidence=1.0,
            )

        # 2. 부분 일치 (경로 접두사)
        for cached_path, nas_file in self._nas_cache.items():
            if cached_path.startswith(normalized) or normalized.startswith(cached_path):
                return MatchResult(
                    hand_clip_id=None,
                    nas_folder_link=nas_folder_link,
                    matched_nas_file_id=nas_file.id,
                    matched_file_path=nas_file.file_path,
                    match_type="partial",
                    confidence=0.8,
                )

        # 3. 퍼지 매칭 (마지막 2-3개 폴더명 비교)
        path_parts = normalized.split("/")
        if len(path_parts) >= 2:
            last_parts = "/".join(path_parts[-3:])  # 마지막 3개 세그먼트

            for cached_path, nas_file in self._nas_cache.items():
                if last_parts in cached_path:
                    return MatchResult(
                        hand_clip_id=None,
                        nas_folder_link=nas_folder_link,
                        matched_nas_file_id=nas_file.id,
                        matched_file_path=nas_file.file_path,
                        match_type="fuzzy",
                        confidence=0.5,
                    )

        # 4. 매칭 실패
        return MatchResult(
            hand_clip_id=None,
            nas_folder_link=nas_folder_link,
            match_type="none",
            confidence=0.0,
        )

    async def match_all_clips(self, limit: int = 10000) -> tuple[list[MatchResult], MatchStats]:
        """모든 HandClip의 nas_folder_link 매칭.

        Args:
            limit: 처리할 최대 클립 수

        Returns:
            (매칭 결과 리스트, 통계)
        """
        # 인덱스가 비어있으면 구축
        if not self._nas_cache:
            await self.build_nas_index()

        # nas_folder_link가 있는 HandClip 조회
        result = await self.session.execute(
            select(HandClip)
            .where(HandClip.nas_folder_link != None)  # noqa: E711
            .limit(limit)
        )
        clips = result.scalars().all()

        results: list[MatchResult] = []
        stats = MatchStats(total_clips=len(clips))

        for clip in clips:
            match_result = self.match_path(clip.nas_folder_link)
            if match_result:
                match_result.hand_clip_id = clip.id
                results.append(match_result)

                if match_result.match_type == "exact":
                    stats.exact_matches += 1
                    stats.matched += 1
                elif match_result.match_type == "partial":
                    stats.partial_matches += 1
                    stats.matched += 1
                elif match_result.match_type == "fuzzy":
                    stats.fuzzy_matches += 1
                    stats.matched += 1
                else:
                    stats.unmatched += 1

        if stats.total_clips > 0:
            stats.match_rate = stats.matched / stats.total_clips * 100

        return results, stats

    async def apply_matches(
        self,
        results: list[MatchResult],
        min_confidence: float = 0.8,
    ) -> int:
        """매칭 결과를 HandClip에 적용 (video_file_id 연결).

        Args:
            results: 매칭 결과 리스트
            min_confidence: 최소 신뢰도 (이상만 적용)

        Returns:
            적용된 수
        """
        applied = 0

        for match in results:
            if match.confidence < min_confidence:
                continue
            if not match.matched_nas_file_id:
                continue

            # NASFile의 video_file_id 가져오기
            nas_file = await self.session.get(NASFile, match.matched_nas_file_id)
            if not nas_file or not nas_file.video_file_id:
                continue

            # HandClip 업데이트
            clip = await self.session.get(HandClip, match.hand_clip_id)
            if clip and not clip.video_file_id:
                clip.video_file_id = nas_file.video_file_id
                applied += 1

        await self.session.commit()
        return applied


class TitleMatcher:
    """제목 기반 매칭 (NAS 파일명 ↔ Sheets 제목)."""

    @staticmethod
    def normalize_title(title: str) -> str:
        """제목 정규화.

        Args:
            title: 원본 제목

        Returns:
            정규화된 제목
        """
        if not title:
            return ""

        # 소문자 변환
        title = title.lower()

        # 특수문자 제거 (알파벳, 숫자, 공백만 유지)
        title = re.sub(r"[^a-z0-9\s]", "", title)

        # 연속 공백 정리
        title = " ".join(title.split())

        return title

    @staticmethod
    def calculate_similarity(title1: str, title2: str) -> float:
        """두 제목의 유사도 계산 (0.0 ~ 1.0).

        Args:
            title1: 첫 번째 제목
            title2: 두 번째 제목

        Returns:
            유사도 (0.0 ~ 1.0)
        """
        norm1 = TitleMatcher.normalize_title(title1)
        norm2 = TitleMatcher.normalize_title(title2)

        if not norm1 or not norm2:
            return 0.0

        if norm1 == norm2:
            return 1.0

        # 포함 관계 확인
        if norm1 in norm2 or norm2 in norm1:
            shorter = min(len(norm1), len(norm2))
            longer = max(len(norm1), len(norm2))
            return shorter / longer

        # 단어 기반 유사도
        words1 = set(norm1.split())
        words2 = set(norm2.split())

        if not words1 or not words2:
            return 0.0

        intersection = words1 & words2
        union = words1 | words2

        return len(intersection) / len(union)

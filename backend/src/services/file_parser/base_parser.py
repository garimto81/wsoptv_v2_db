"""Base Parser - 블럭 A (NAS Inventory Agent)."""

import re
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class ParsedMetadata:
    """파일명 파싱 결과."""

    # 공통
    project_code: Optional[str] = None
    year: Optional[int] = None
    version_type: str = "generic"

    # WSOP 관련
    event_number: Optional[int] = None
    buy_in: Optional[str] = None
    game_type: Optional[str] = None
    table_type: Optional[str] = None
    clip_number: Optional[int] = None
    location: Optional[str] = None

    # 에피소드 관련
    episode_number: Optional[int] = None
    season_number: Optional[int] = None
    day_number: Optional[int] = None
    day_info: Optional[str] = None

    # 기타
    featured_player: Optional[str] = None
    edit_date: Optional[str] = None
    event_name: Optional[str] = None
    gtd_amount: Optional[int] = None
    description: Optional[str] = None

    # 카탈로그 표시용
    display_title: Optional[str] = None
    catalog_title: Optional[str] = None
    content_type: Optional[str] = None
    event_type: Optional[str] = None
    event_name_short: Optional[str] = None
    venue: Optional[str] = None
    episode_type: Optional[str] = None
    part_number: Optional[int] = None

    # 원본 데이터
    raw_filename: str = ""
    raw_path: str = ""
    parse_success: bool = False
    parser_used: str = ""

    # 추가 필드
    extra: dict = field(default_factory=dict)


class BaseParser(ABC):
    """파일명 파서 기본 클래스."""

    name: str = "base"

    @abstractmethod
    def can_parse(self, file_name: str, file_path: str) -> bool:
        """이 파서로 파싱 가능한지 확인."""
        pass

    @abstractmethod
    def parse(self, file_name: str, file_path: str = "") -> ParsedMetadata:
        """파일명 파싱."""
        pass

    def _normalize_game_type(self, raw: str) -> str:
        """게임 타입 정규화."""
        mapping = {
            "nlh": "NLHE",
            "nlhe": "NLHE",
            "plo": "PLO",
            "plo8": "PLO8",
            "horse": "HORSE",
            "stud": "Stud",
            "razz": "Razz",
        }
        return mapping.get(raw.lower(), raw.upper())

    def _normalize_table_type(self, raw: str) -> str:
        """테이블 타입 정규화."""
        mapping = {
            "ft": "final_table",
            "final": "final_table",
            "hu": "heads_up",
            "d1": "day1",
            "d2": "day2",
            "d3": "day3",
        }
        return mapping.get(raw.lower(), raw.lower())

    def _extract_year(self, text: str) -> Optional[int]:
        """연도 추출."""
        # 4자리 연도
        match = re.search(r"(19|20)\d{2}", text)
        if match:
            return int(match.group())

        # 2자리 연도 (24 → 2024)
        match = re.search(r"(?<!\d)(\d{2})(?!\d)", text)
        if match:
            year = int(match.group())
            return 2000 + year if year < 50 else 1900 + year

        return None

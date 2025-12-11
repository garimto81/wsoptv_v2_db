"""Parser Factory - 블럭 A (NAS Inventory Agent)."""

from typing import Optional

from .base_parser import BaseParser, ParsedMetadata
from .other_parsers import (
    GenericParser,
    GGMillionsParser,
    GOGParser,
    MPPParser,
    PADParser,
)
from .wsop_parser import WSOPArchiveParser, WSOPBraceletParser, WSOPCircuitParser


class ParserFactory:
    """파일명 파서 팩토리.

    7개 전문 파서 + 1개 범용 파서를 관리합니다.
    """

    # 파서 우선순위 순서
    _parsers: list[BaseParser] = [
        WSOPBraceletParser(),
        WSOPCircuitParser(),
        WSOPArchiveParser(),
        GGMillionsParser(),
        GOGParser(),
        PADParser(),
        MPPParser(),
        GenericParser(),  # Fallback
    ]

    @classmethod
    def get_parser(cls, file_name: str, file_path: str = "") -> BaseParser:
        """적합한 파서 반환."""
        for parser in cls._parsers:
            if parser.can_parse(file_name, file_path):
                return parser
        return GenericParser()

    @classmethod
    def parse(cls, file_name: str, file_path: str = "") -> ParsedMetadata:
        """파일명 파싱."""
        parser = cls.get_parser(file_name, file_path)
        return parser.parse(file_name, file_path)

    @classmethod
    def get_all_parsers(cls) -> list[BaseParser]:
        """모든 파서 목록 반환."""
        return cls._parsers.copy()

    @classmethod
    def get_parser_by_name(cls, name: str) -> Optional[BaseParser]:
        """이름으로 파서 조회."""
        for parser in cls._parsers:
            if parser.name == name:
                return parser
        return None


def detect_version_type(file_path: str, file_name: str) -> str:
    """버전 타입 감지."""
    name_lower = file_name.lower()
    path_lower = file_path.lower()

    if "-clean" in name_lower or "클린본" in file_name:
        return "clean"
    if "/mastered/" in path_lower or "\\mastered\\" in path_lower:
        return "mastered"
    if "/stream/" in path_lower or "\\stream\\" in path_lower:
        return "stream"
    if "/subclip/" in path_lower or "\\subclip\\" in path_lower:
        return "subclip"
    if "final_edit" in name_lower:
        return "final_edit"
    if "-nobug" in name_lower:
        return "nobug"
    if "pgm" in name_lower:
        return "pgm"
    if "hires" in name_lower:
        return "hires"

    return "generic"


def should_hide_file(file_name: str) -> tuple[bool, Optional[str]]:
    """숨김 파일 여부 및 이유 반환."""
    if file_name.startswith("._"):
        return True, "macos_metadata"
    if file_name.lower() == "thumbs.db":
        return True, "windows_thumbnail"
    if file_name == ".DS_Store":
        return True, "macos_system"
    return False, None


def get_file_category(file_extension: str) -> str:
    """파일 카테고리 반환."""
    video_extensions = {".mp4", ".mov", ".mxf", ".avi", ".mkv", ".wmv"}
    archive_extensions = {".zip", ".rar", ".7z", ".tar", ".gz"}

    ext_lower = file_extension.lower() if file_extension else ""

    if ext_lower in video_extensions:
        return "video"
    if ext_lower in archive_extensions:
        return "archive"
    if ext_lower in {".xml", ".json", ".txt", ".srt"}:
        return "metadata"

    return "other"

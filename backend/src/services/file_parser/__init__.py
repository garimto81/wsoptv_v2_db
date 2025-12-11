"""File Parser Module - 블럭 A (NAS Inventory Agent).

7개 전문 파서 + 1개 범용 파서로 NAS 파일명을 파싱합니다.
"""

from .base_parser import BaseParser, ParsedMetadata
from .other_parsers import (
    GenericParser,
    GGMillionsParser,
    GOGParser,
    MPPParser,
    PADParser,
)
from .parser_factory import (
    ParserFactory,
    detect_version_type,
    get_file_category,
    should_hide_file,
)
from .wsop_parser import WSOPArchiveParser, WSOPBraceletParser, WSOPCircuitParser
from .title_generator import TitleGenerator

__all__ = [
    # Base
    "BaseParser",
    "ParsedMetadata",
    # Factory
    "ParserFactory",
    "detect_version_type",
    "should_hide_file",
    "get_file_category",
    # WSOP Parsers
    "WSOPBraceletParser",
    "WSOPCircuitParser",
    "WSOPArchiveParser",
    # Other Parsers
    "GGMillionsParser",
    "GOGParser",
    "PADParser",
    "MPPParser",
    "GenericParser",
    # Title Generator
    "TitleGenerator",
]

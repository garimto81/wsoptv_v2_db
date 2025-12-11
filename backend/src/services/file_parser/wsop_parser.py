"""WSOP Parsers - 블럭 A (NAS Inventory Agent)."""

import re
from typing import Optional

from .base_parser import BaseParser, ParsedMetadata


class WSOPBraceletParser(BaseParser):
    """WSOP Bracelet Event 파서.

    패턴: {번호}-wsop-{연도}-be-ev-{이벤트}-{바이인}-{게임}-{추가정보}.mp4
    예시: 10-wsop-2024-be-ev-21-25k-nlh-hr-ft-schutten-reclaims-chip-lead.mp4
    """

    name = "wsop_bracelet"

    # 정규식 패턴
    PATTERN = re.compile(
        r"^(\d+)-wsop-(\d{4})-be-ev-(\d+)-"  # 클립번호, 연도, 이벤트
        r"(\d+k?)-"  # 바이인
        r"([a-z0-9]+)-"  # 게임타입
        r"(.+)\.(mp4|mov|mxf)$",  # 나머지 + 확장자
        re.IGNORECASE,
    )

    def can_parse(self, file_name: str, file_path: str) -> bool:
        return bool(self.PATTERN.match(file_name))

    def parse(self, file_name: str, file_path: str = "") -> ParsedMetadata:
        match = self.PATTERN.match(file_name)
        if not match:
            return ParsedMetadata(
                raw_filename=file_name,
                raw_path=file_path,
                parse_success=False,
                parser_used=self.name,
            )

        clip_number, year, event_num, buy_in, game_type, rest = match.groups()[:6]

        # 추가 정보 파싱 (hr, ft 등)
        parts = rest.lower().split("-")
        table_type = None
        description_parts = []

        for part in parts:
            if part in ("ft", "final"):
                table_type = "final_table"
            elif part in ("hu", "headsup"):
                table_type = "heads_up"
            elif part in ("d1", "d2", "d3"):
                table_type = f"day{part[-1]}"
            elif part == "hr":
                pass  # High Roller 표시
            else:
                description_parts.append(part)

        return ParsedMetadata(
            project_code="WSOP",
            year=int(year),
            event_number=int(event_num),
            buy_in=buy_in.upper(),
            game_type=self._normalize_game_type(game_type),
            table_type=table_type,
            clip_number=int(clip_number),
            location="LAS VEGAS",
            description="-".join(description_parts) if description_parts else None,
            raw_filename=file_name,
            raw_path=file_path,
            parse_success=True,
            parser_used=self.name,
        )


class WSOPCircuitParser(BaseParser):
    """WSOP Circuit 파서.

    패턴: WCLA{YY}-{번호}.mp4
    예시: WCLA24-15.mp4
    """

    name = "wsop_circuit"

    PATTERN = re.compile(r"^WCLA(\d{2})-(\d+)\.(mp4|mov)$", re.IGNORECASE)

    def can_parse(self, file_name: str, file_path: str) -> bool:
        return bool(self.PATTERN.match(file_name))

    def parse(self, file_name: str, file_path: str = "") -> ParsedMetadata:
        match = self.PATTERN.match(file_name)
        if not match:
            return ParsedMetadata(
                raw_filename=file_name,
                raw_path=file_path,
                parse_success=False,
                parser_used=self.name,
            )

        year_short, clip_number = match.groups()[:2]
        year = 2000 + int(year_short)

        return ParsedMetadata(
            project_code="WSOP",
            year=year,
            clip_number=int(clip_number),
            location="LOS ANGELES",
            extra={"sub_category": "CIRCUIT"},
            raw_filename=file_name,
            raw_path=file_path,
            parse_success=True,
            parser_used=self.name,
        )


class WSOPArchiveParser(BaseParser):
    """WSOP Archive (PRE-2016) 파서.

    패턴: wsop-{연도}-me-{버전}.mp4
    예시: wsop-1973-me-nobug.mp4
    """

    name = "wsop_archive"

    PATTERN = re.compile(
        r"^wsop-(\d{4})-(me|ep\d+)(?:-([a-z]+))?\.(mp4|mov|avi)$", re.IGNORECASE
    )

    def can_parse(self, file_name: str, file_path: str) -> bool:
        return bool(self.PATTERN.match(file_name)) or "ARCHIVE" in file_path.upper()

    def parse(self, file_name: str, file_path: str = "") -> ParsedMetadata:
        match = self.PATTERN.match(file_name)

        if match:
            year, event_type, version = match.groups()[:3]
            return ParsedMetadata(
                project_code="WSOP",
                year=int(year),
                event_name="Main Event" if event_type.lower() == "me" else event_type,
                version_type=version if version else "generic",
                extra={"sub_category": "ARCHIVE"},
                raw_filename=file_name,
                raw_path=file_path,
                parse_success=True,
                parser_used=self.name,
            )

        # 폴더 경로에서 연도 추출 시도
        year = self._extract_year(file_path)
        return ParsedMetadata(
            project_code="WSOP",
            year=year,
            extra={"sub_category": "ARCHIVE"},
            raw_filename=file_name,
            raw_path=file_path,
            parse_success=year is not None,
            parser_used=self.name,
        )

"""Other Project Parsers - 블럭 A (NAS Inventory Agent)."""

import re
from typing import Optional

from .base_parser import BaseParser, ParsedMetadata


class GGMillionsParser(BaseParser):
    """GGMillions Super High Roller 파서.

    패턴 A: {YYMMDD}_Super High Roller Poker FINAL TABLE with {플레이어}.mp4
    패턴 B: Super High Roller Poker FINAL TABLE with {플레이어}.mp4
    예시: 250507_Super High Roller Poker FINAL TABLE with Joey ingram.mp4
    """

    name = "ggmillions"

    PATTERN = re.compile(
        r"^(\d{6})?_?Super High Roller Poker FINAL TABLE with (.+)\.(mp4|mov)$",
        re.IGNORECASE,
    )

    def can_parse(self, file_name: str, file_path: str) -> bool:
        return "GGMillions" in file_path or "Super High Roller" in file_name

    def parse(self, file_name: str, file_path: str = "") -> ParsedMetadata:
        match = self.PATTERN.match(file_name)

        if match:
            date_str, player, _ = match.groups()

            year = None
            if date_str:
                year = 2000 + int(date_str[:2])
                edit_date = f"20{date_str[:2]}-{date_str[2:4]}-{date_str[4:6]}"
            else:
                edit_date = None

            return ParsedMetadata(
                project_code="GGMILLIONS",
                year=year,
                featured_player=player.strip(),
                table_type="final_table",
                edit_date=edit_date,
                raw_filename=file_name,
                raw_path=file_path,
                parse_success=True,
                parser_used=self.name,
            )

        return ParsedMetadata(
            project_code="GGMILLIONS",
            raw_filename=file_name,
            raw_path=file_path,
            parse_success=False,
            parser_used=self.name,
        )


class GOGParser(BaseParser):
    """Game of Gold 파서.

    패턴 A: E{번호}_GOG_final_edit_{YYYYMMDD}[_수정|_최종].mp4
    패턴 B: E{번호}_GOG_final_edit_클린본_{YYYYMMDD}.mp4
    패턴 C: E{번호}_GOG_final_edit_{YYYYMMDD}_최종.mp4 (8자리 날짜)
    예시: E01_GOG_final_edit_231106.mp4, E07_GOG_final_edit_20231121_최종.mp4
    """

    name = "gog"

    # 6자리 날짜 패턴 (YYMMDD)
    PATTERN_6 = re.compile(
        r"^E(\d{1,3})_GOG_final_edit_(클린본_)?(\d{6})(?:_수정|_최종)?\.(mp4|mov)$",
        re.IGNORECASE,
    )
    # 8자리 날짜 패턴 (YYYYMMDD)
    PATTERN_8 = re.compile(
        r"^E(\d{1,3})_GOG_final_edit_(클린본_)?(\d{8})(?:_수정|_최종)?\.(mp4|mov)$",
        re.IGNORECASE,
    )

    def can_parse(self, file_name: str, file_path: str) -> bool:
        return "GOG" in file_path or "_GOG_" in file_name

    def parse(self, file_name: str, file_path: str = "") -> ParsedMetadata:
        # 8자리 날짜 패턴 먼저 시도
        match = self.PATTERN_8.match(file_name)
        if match:
            ep_num, is_clean, date_str = match.groups()[:3]
            year = int(date_str[:4])
            edit_date = f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:8]}"
            version_type = "clean" if is_clean else "final"

            # _최종 체크
            if "_최종" in file_name:
                version_type = "final"

            return ParsedMetadata(
                project_code="GOG",
                year=year,
                episode_number=int(ep_num),
                version_type=version_type,
                edit_date=edit_date,
                extra={"is_final": "_최종" in file_name or "final" in file_name.lower()},
                raw_filename=file_name,
                raw_path=file_path,
                parse_success=True,
                parser_used=self.name,
            )

        # 6자리 날짜 패턴
        match = self.PATTERN_6.match(file_name)
        if match:
            ep_num, is_clean, date_str = match.groups()[:3]
            year = 2000 + int(date_str[:2])
            edit_date = f"20{date_str[:2]}-{date_str[2:4]}-{date_str[4:6]}"
            version_type = "clean" if is_clean else "final_edit"

            return ParsedMetadata(
                project_code="GOG",
                year=year,
                episode_number=int(ep_num),
                version_type=version_type,
                edit_date=edit_date,
                raw_filename=file_name,
                raw_path=file_path,
                parse_success=True,
                parser_used=self.name,
            )

        return ParsedMetadata(
            project_code="GOG",
            raw_filename=file_name,
            raw_path=file_path,
            parse_success=False,
            parser_used=self.name,
        )


class PADParser(BaseParser):
    """Poker After Dark 파서.

    패턴 S12: pad-s{시즌}-ep{에피소드}-{코드}.mp4
    패턴 S13: PAD_S{시즌}_EP{에피소드}_{버전}-{코드}.mp4
    예시: pad-s12-ep01-12345.mp4
    """

    name = "pad"

    PATTERN_S12 = re.compile(r"^pad-s(\d+)-ep(\d+)-(\d+)\.(mp4|mov)$", re.IGNORECASE)
    PATTERN_S13 = re.compile(
        r"^PAD_S(\d+)_EP(\d+)_?([^-]*)?-?(\d+)?\.(mp4|mov)$", re.IGNORECASE
    )

    def can_parse(self, file_name: str, file_path: str) -> bool:
        return "PAD" in file_path or file_name.upper().startswith("PAD")

    def parse(self, file_name: str, file_path: str = "") -> ParsedMetadata:
        # S12 패턴
        match = self.PATTERN_S12.match(file_name)
        if match:
            season, episode, code = match.groups()[:3]
            return ParsedMetadata(
                project_code="PAD",
                season_number=int(season),
                episode_number=int(episode),
                extra={"version_code": code},
                raw_filename=file_name,
                raw_path=file_path,
                parse_success=True,
                parser_used=self.name,
            )

        # S13 패턴
        match = self.PATTERN_S13.match(file_name)
        if match:
            season, episode, version, code = match.groups()[:4]
            return ParsedMetadata(
                project_code="PAD",
                season_number=int(season),
                episode_number=int(episode),
                version_type=version.lower() if version else "generic",
                extra={"version_code": code} if code else {},
                raw_filename=file_name,
                raw_path=file_path,
                parse_success=True,
                parser_used=self.name,
            )

        return ParsedMetadata(
            project_code="PAD",
            raw_filename=file_name,
            raw_path=file_path,
            parse_success=False,
            parser_used=self.name,
        )


class MPPParser(BaseParser):
    """Mediterranean Poker Party 파서.

    패턴: ${GTD금액} GTD   ${바이인} {이벤트명} ? {Day/Final}.mp4
    예시: $1M GTD   $1K PokerOK Mystery Bounty ? Day 1A.mp4
    """

    name = "mpp"

    PATTERN = re.compile(
        r"^\$(\d+[MK]?) GTD\s+\$(\d+[MK]?) (.+) [?？] (.+)\.(mp4|mov)$", re.IGNORECASE
    )

    def can_parse(self, file_name: str, file_path: str) -> bool:
        return "MPP" in file_path or "GTD" in file_name

    def parse(self, file_name: str, file_path: str = "") -> ParsedMetadata:
        match = self.PATTERN.match(file_name)

        if match:
            gtd, buy_in, event_name, day_info = match.groups()[:4]

            # GTD 금액 파싱
            gtd_amount = self._parse_amount(gtd)

            return ParsedMetadata(
                project_code="MPP",
                year=2025,  # Cyprus 2025
                event_name=event_name.strip(),
                buy_in=buy_in,
                gtd_amount=gtd_amount,
                day_info=day_info.strip(),
                table_type="final_table" if "Final" in day_info else None,
                raw_filename=file_name,
                raw_path=file_path,
                parse_success=True,
                parser_used=self.name,
            )

        return ParsedMetadata(
            project_code="MPP",
            raw_filename=file_name,
            raw_path=file_path,
            parse_success=False,
            parser_used=self.name,
        )

    def _parse_amount(self, amount_str: str) -> Optional[int]:
        """금액 문자열 파싱 (1M → 1000000, 1K → 1000)."""
        amount_str = amount_str.upper()
        if amount_str.endswith("M"):
            return int(amount_str[:-1]) * 1_000_000
        elif amount_str.endswith("K"):
            return int(amount_str[:-1]) * 1_000
        return int(amount_str) if amount_str.isdigit() else None


class GenericParser(BaseParser):
    """범용 파서 (Fallback)."""

    name = "generic"

    def can_parse(self, file_name: str, file_path: str) -> bool:
        return True  # 항상 파싱 가능

    def parse(self, file_name: str, file_path: str = "") -> ParsedMetadata:
        year = self._extract_year(file_name) or self._extract_year(file_path)

        # 프로젝트 추론
        project_code = None
        if "WSOP" in file_path.upper():
            project_code = "WSOP"
        elif "HCL" in file_path.upper():
            project_code = "HCL"
        elif "GGMillions" in file_path:
            project_code = "GGMILLIONS"
        elif "MPP" in file_path:
            project_code = "MPP"
        elif "PAD" in file_path:
            project_code = "PAD"
        elif "GOG" in file_path:
            project_code = "GOG"

        return ParsedMetadata(
            project_code=project_code,
            year=year,
            raw_filename=file_name,
            raw_path=file_path,
            parse_success=True,
            parser_used=self.name,
        )

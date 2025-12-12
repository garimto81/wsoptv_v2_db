"""Title Generator - ParsedMetadata에서 display_title, catalog_title 생성.

PRD 15.2 제목 자동 생성 규칙 구현.
"""

from typing import Optional
from .base_parser import ParsedMetadata


class TitleGenerator:
    """ParsedMetadata에서 display_title, catalog_title 생성."""

    PROJECT_NAMES = {
        "WSOP": "WSOP",
        "WSOP_BRACELET": "WSOP",
        "WSOP_CIRCUIT": "WSOP Circuit",
        "GGMILLIONS": "GG Millions",
        "GOG": "Game of Gold",
        "PAD": "Poker After Dark",
        "MPP": "MPP",
        "HCL": "Hustler Casino Live",
    }

    PROJECT_ABBREV = {
        "WSOP": "WSOP",
        "WSOP_BRACELET": "WSOP",
        "WSOP_CIRCUIT": "WSOP-C",
        "GGMILLIONS": "GGM",
        "GOG": "GOG",
        "PAD": "PAD",
        "MPP": "MPP",
        "HCL": "HCL",
    }

    TABLE_TYPE_NAMES = {
        "final_table": "Final Table",
        "ft": "Final Table",
        "heads_up": "Heads Up",
        "hu": "Heads Up",
        "day1": "Day 1",
        "day2": "Day 2",
        "day3": "Day 3",
        "d1": "Day 1",
        "d2": "Day 2",
        "d3": "Day 3",
        "preliminary": "Preliminary",
    }

    GAME_TYPE_DISPLAY = {
        "NLHE": "NLH",
        "NLH": "NLH",
        "PLO": "PLO",
        "PLO8": "PLO Hi-Lo",
        "HORSE": "HORSE",
        "STUD": "Stud",
        "RAZZ": "Razz",
    }

    def generate(self, metadata: ParsedMetadata) -> tuple[str, str]:
        """display_title과 catalog_title 생성.

        Args:
            metadata: 파싱된 메타데이터

        Returns:
            (display_title, catalog_title) 튜플
        """
        display_title = self._generate_display_title(metadata)
        catalog_title = self._generate_catalog_title(metadata)
        return display_title, catalog_title

    def _generate_display_title(self, m: ParsedMetadata) -> str:
        """전체 제목 생성.

        예시:
        - WSOP 2024 Event #21 $25K NLH High Roller Final Table
        - 2024 WSOP Circuit LA - Clip #15
        - GG Millions Super High Roller Final Table ft. Joey Ingram
        - Game of Gold Episode 5 (Clean Version)
        - Poker After Dark S13 Episode 10
        """
        parts = []
        project_code = m.project_code or ""

        # PAD: 시즌 먼저
        if project_code == "PAD" and m.season_number:
            project_name = self.PROJECT_NAMES.get(project_code, project_code)
            parts.append(f"{project_name} S{m.season_number}")
            if m.episode_number:
                parts.append(f"Episode {m.episode_number}")
            return " ".join(parts) if parts else self._fallback_title(m)

        # GOG: 에피소드 기반
        if project_code == "GOG":
            parts.append("Game of Gold")
            if m.year:
                parts.append(str(m.year))
            if m.episode_number:
                parts.append(f"Episode {m.episode_number}")
            if m.extra.get("is_final"):
                parts.append("(Final)")
            elif m.version_type == "clean":
                parts.append("(Clean)")
            return " ".join(parts) if parts else self._fallback_title(m)

        # GGMillions: 피처드 플레이어
        if project_code == "GGMILLIONS":
            parts.append("GG Millions Super High Roller Final Table")
            if m.featured_player:
                parts.append(f"ft. {m.featured_player}")
            if m.edit_date:
                parts.append(f"({m.edit_date})")
            return " ".join(parts) if parts else self._fallback_title(m)

        # MPP
        if project_code == "MPP":
            parts.append("MPP")
            if m.year:
                parts.append(str(m.year))
            if m.buy_in:
                buy_in = m.buy_in.upper()
                if not buy_in.startswith("$"):
                    buy_in = f"${buy_in}"
                parts.append(buy_in)
            if m.event_name:
                parts.append(m.event_name)
            if m.day_info:
                parts.append(f"- {m.day_info}")
            elif m.table_type:
                table_name = self.TABLE_TYPE_NAMES.get(m.table_type, m.table_type)
                parts.append(f"- {table_name}")
            return " ".join(parts) if parts else self._fallback_title(m)

        # WSOP Circuit
        if project_code == "WSOP" and m.extra.get("sub_category") == "CIRCUIT":
            if m.year:
                parts.append(str(m.year))
            parts.append("WSOP Circuit")
            if m.location:
                loc_short = self._shorten_location(m.location)
                parts.append(loc_short)
            if m.clip_number:
                parts.append(f"- Clip #{m.clip_number}")
            return " ".join(parts) if parts else self._fallback_title(m)

        # WSOP Archive
        if project_code == "WSOP" and m.extra.get("sub_category") == "ARCHIVE":
            parts.append("WSOP")
            if m.year:
                parts.append(str(m.year))
            if m.event_name:
                parts.append(m.event_name)
            if m.version_type and m.version_type != "generic":
                parts.append(f"({m.version_type})")
            return " ".join(parts) if parts else self._fallback_title(m)

        # WSOP Bracelet (기본)
        if project_code in ("WSOP", "WSOP_BRACELET"):
            parts.append("WSOP")
            if m.year:
                parts.append(str(m.year))
            if m.event_number:
                parts.append(f"Event #{m.event_number}")
            if m.buy_in:
                buy_in = m.buy_in.upper()
                if not buy_in.startswith("$"):
                    buy_in = f"${buy_in}"
                parts.append(buy_in)
            if m.game_type:
                game = self.GAME_TYPE_DISPLAY.get(m.game_type.upper(), m.game_type)
                parts.append(game)
            if m.table_type:
                table_name = self.TABLE_TYPE_NAMES.get(m.table_type, m.table_type)
                parts.append(table_name)
            return " ".join(parts) if parts else self._fallback_title(m)

        # 기타 프로젝트
        project_name = self.PROJECT_NAMES.get(project_code, project_code)
        if project_name:
            parts.append(project_name)
        if m.year:
            parts.append(str(m.year))
        if m.event_number:
            parts.append(f"Event #{m.event_number}")
        if m.episode_number:
            parts.append(f"Episode {m.episode_number}")

        return " ".join(parts) if parts else self._fallback_title(m)

    def _generate_catalog_title(self, m: ParsedMetadata) -> str:
        """카드용 짧은 제목 생성.

        예시:
        - WSOP '24 #21 FT
        - WSOP-C LA #15
        - GGM FT
        - GOG E05
        - PAD S13 E10
        """
        parts = []
        project_code = m.project_code or ""

        # 프로젝트 약어
        abbrev = self.PROJECT_ABBREV.get(project_code, project_code)
        if abbrev:
            parts.append(abbrev)

        # PAD
        if project_code == "PAD":
            if m.season_number:
                parts.append(f"S{m.season_number}")
            if m.episode_number:
                parts.append(f"E{m.episode_number:02d}")
            return " ".join(parts) if parts else m.raw_filename[:30]

        # GOG
        if project_code == "GOG":
            if m.year:
                parts.append(f"'{str(m.year)[-2:]}")
            if m.episode_number:
                parts.append(f"E{m.episode_number:02d}")
            if m.extra.get("is_final"):
                parts.append("Final")
            elif m.version_type == "clean":
                parts.append("Clean")
            return " ".join(parts) if parts else m.raw_filename[:30]

        # GGMillions
        if project_code == "GGMILLIONS":
            parts.append("FT")
            if m.featured_player:
                # 이름의 첫 번째 단어만
                first_name = m.featured_player.split()[0] if m.featured_player else ""
                if first_name:
                    parts.append(f"({first_name})")
            return " ".join(parts) if parts else m.raw_filename[:30]

        # MPP
        if project_code == "MPP":
            if m.buy_in:
                parts.append(f"${m.buy_in}")
            if m.table_type in ("final_table", "ft"):
                parts.append("FT")
            elif m.day_info:
                parts.append(m.day_info[:10])
            return " ".join(parts) if parts else m.raw_filename[:30]

        # WSOP Circuit
        if project_code == "WSOP" and m.extra.get("sub_category") == "CIRCUIT":
            if m.location:
                loc_short = self._shorten_location(m.location)
                parts[0] = f"WSOP-C {loc_short}"
            if m.clip_number:
                parts.append(f"#{m.clip_number}")
            return " ".join(parts) if parts else m.raw_filename[:30]

        # WSOP (일반)
        # 연도 (2자리)
        if m.year:
            parts.append(f"'{str(m.year)[-2:]}")

        # 이벤트 번호
        if m.event_number:
            parts.append(f"#{m.event_number}")

        # 테이블 타입 약어
        if m.table_type in ("final_table", "ft"):
            parts.append("FT")
        elif m.table_type in ("heads_up", "hu"):
            parts.append("HU")
        elif m.table_type and m.table_type.startswith("day"):
            parts.append(m.table_type.upper().replace("DAY", "D"))

        return " ".join(parts) if parts else m.raw_filename[:30]

    def _fallback_title(self, m: ParsedMetadata) -> str:
        """파싱 실패 시 파일명에서 제목 생성."""
        name = m.raw_filename
        # 확장자 제거
        if "." in name:
            name = name.rsplit(".", 1)[0]
        # 언더스코어/하이픈을 공백으로
        name = name.replace("_", " ").replace("-", " ")
        # 연속 공백 제거
        name = " ".join(name.split())
        # 타이틀 케이스 (100자 제한)
        return name.title()[:100]

    def _shorten_location(self, location: str) -> str:
        """위치명 축약."""
        shortcuts = {
            "LOS ANGELES": "LA",
            "LAS VEGAS": "LV",
            "PARADISE": "PAR",
            "EUROPE": "EU",
            "CYPRUS": "CYP",
        }
        return shortcuts.get(location.upper(), location[:10])

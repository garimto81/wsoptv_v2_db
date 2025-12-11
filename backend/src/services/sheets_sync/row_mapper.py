"""Row Mapper - Block D (Sheets Sync Agent).

Map sheet rows to database entities.
"""

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Any, Optional


@dataclass
class MappedHandClip:
    """Mapped hand clip data from sheet row."""

    row_number: int
    sheet_source: str

    # Content
    title: Optional[str] = None
    timecode: Optional[str] = None
    timecode_end: Optional[str] = None
    duration_seconds: Optional[int] = None
    notes: Optional[str] = None

    # Hand info
    hand_grade: Optional[str] = None
    pot_size: Optional[int] = None
    winner_hand: Optional[str] = None
    hands_involved: Optional[str] = None

    # Related
    video_filename: Optional[str] = None
    player_names: list[str] = None
    tag_names: list[str] = None

    # NAS 매칭용 (PRD 15.3)
    nas_folder_link: Optional[str] = None
    sheet_file_name: Optional[str] = None

    def __post_init__(self):
        if self.player_names is None:
            self.player_names = []
        if self.tag_names is None:
            self.tag_names = []


class RowMapper:
    """Map sheet rows to entity data."""

    # Column indices for METADATA_ARCHIVE sheet
    # PRD 4.1 기준: 0=타임코드, 1=타임코드끝, 2=제목, 3=NAS폴더링크, 4=등급, 5=플레이어, ...
    ARCHIVE_COLUMNS = {
        "timecode": 0,
        "timecode_end": 1,
        "title": 2,
        "nas_folder_link": 3,  # PRD 15.3: NAS 매칭용
        "hand_grade": 4,
        "players": 5,
        "tags": 6,
        "notes": 7,
        "video_filename": 8,
        "pot_size": 9,
        "winner_hand": 10,
        "hands_involved": 11,
    }

    # Column indices for ICONIK_METADATA sheet
    ICONIK_COLUMNS = {
        "title": 0,
        "timecode": 1,
        "duration": 2,
        "tags": 3,
        "players": 4,
        "notes": 5,
    }

    @classmethod
    def map_archive_row(
        cls,
        row: list[Any],
        row_number: int,
        sheet_source: str = "METADATA_ARCHIVE",
    ) -> Optional[MappedHandClip]:
        """Map a row from METADATA_ARCHIVE sheet.

        Args:
            row: List of cell values.
            row_number: Row number in sheet.
            sheet_source: Source sheet identifier.

        Returns:
            MappedHandClip or None if row is empty/invalid.
        """
        if not row or len(row) < 3:
            return None

        def get_cell(idx: int) -> Optional[str]:
            if idx < len(row) and row[idx]:
                return str(row[idx]).strip()
            return None

        timecode = get_cell(cls.ARCHIVE_COLUMNS["timecode"])
        title = get_cell(cls.ARCHIVE_COLUMNS["title"])

        if not timecode and not title:
            return None

        # Parse players (comma-separated)
        players_str = get_cell(cls.ARCHIVE_COLUMNS["players"])
        player_names = []
        if players_str:
            player_names = [p.strip() for p in players_str.split(",") if p.strip()]

        # Parse tags (comma-separated)
        tags_str = get_cell(cls.ARCHIVE_COLUMNS["tags"])
        tag_names = []
        if tags_str:
            tag_names = [t.strip() for t in tags_str.split(",") if t.strip()]

        # Parse pot size
        pot_size = None
        pot_str = get_cell(cls.ARCHIVE_COLUMNS["pot_size"])
        if pot_str:
            try:
                # Remove currency symbols and commas
                clean = pot_str.replace("$", "").replace(",", "").strip()
                pot_size = int(float(clean))
            except (ValueError, TypeError):
                pass

        # NAS folder link 추출 (PRD 15.3)
        nas_folder_link = get_cell(cls.ARCHIVE_COLUMNS["nas_folder_link"])

        return MappedHandClip(
            row_number=row_number,
            sheet_source=sheet_source,
            timecode=timecode,
            timecode_end=get_cell(cls.ARCHIVE_COLUMNS["timecode_end"]),
            title=title,
            hand_grade=get_cell(cls.ARCHIVE_COLUMNS["hand_grade"]),
            player_names=player_names,
            tag_names=tag_names,
            notes=get_cell(cls.ARCHIVE_COLUMNS["notes"]),
            video_filename=get_cell(cls.ARCHIVE_COLUMNS["video_filename"]),
            pot_size=pot_size,
            winner_hand=get_cell(cls.ARCHIVE_COLUMNS["winner_hand"]),
            hands_involved=get_cell(cls.ARCHIVE_COLUMNS["hands_involved"]),
            nas_folder_link=nas_folder_link,
        )

    @classmethod
    def map_iconik_row(
        cls,
        row: list[Any],
        row_number: int,
        sheet_source: str = "ICONIK_METADATA",
    ) -> Optional[MappedHandClip]:
        """Map a row from ICONIK_METADATA sheet.

        Args:
            row: List of cell values.
            row_number: Row number in sheet.
            sheet_source: Source sheet identifier.

        Returns:
            MappedHandClip or None if row is empty/invalid.
        """
        if not row or len(row) < 2:
            return None

        def get_cell(idx: int) -> Optional[str]:
            if idx < len(row) and row[idx]:
                return str(row[idx]).strip()
            return None

        title = get_cell(cls.ICONIK_COLUMNS["title"])
        timecode = get_cell(cls.ICONIK_COLUMNS["timecode"])

        if not title and not timecode:
            return None

        # Parse duration to seconds
        duration_seconds = None
        duration_str = get_cell(cls.ICONIK_COLUMNS["duration"])
        if duration_str:
            duration_seconds = cls._parse_duration(duration_str)

        # Parse players
        players_str = get_cell(cls.ICONIK_COLUMNS["players"])
        player_names = []
        if players_str:
            player_names = [p.strip() for p in players_str.split(",") if p.strip()]

        # Parse tags
        tags_str = get_cell(cls.ICONIK_COLUMNS["tags"])
        tag_names = []
        if tags_str:
            tag_names = [t.strip() for t in tags_str.split(",") if t.strip()]

        return MappedHandClip(
            row_number=row_number,
            sheet_source=sheet_source,
            title=title,
            timecode=timecode,
            duration_seconds=duration_seconds,
            player_names=player_names,
            tag_names=tag_names,
            notes=get_cell(cls.ICONIK_COLUMNS["notes"]),
        )

    @staticmethod
    def _parse_duration(duration_str: str) -> Optional[int]:
        """Parse duration string to seconds.

        Supports formats: "1:30", "01:30:00", "90"
        """
        try:
            parts = duration_str.split(":")
            if len(parts) == 1:
                return int(float(parts[0]))
            elif len(parts) == 2:
                minutes, seconds = int(parts[0]), int(parts[1])
                return minutes * 60 + seconds
            elif len(parts) == 3:
                hours, minutes, seconds = int(parts[0]), int(parts[1]), int(parts[2])
                return hours * 3600 + minutes * 60 + seconds
        except (ValueError, TypeError):
            pass
        return None

    @staticmethod
    def _parse_timecode(timecode_str: str) -> Optional[str]:
        """Normalize timecode format.

        Ensures format is HH:MM:SS or MM:SS.
        """
        if not timecode_str:
            return None

        parts = timecode_str.strip().split(":")
        if len(parts) == 2:
            return f"00:{parts[0].zfill(2)}:{parts[1].zfill(2)}"
        elif len(parts) == 3:
            return f"{parts[0].zfill(2)}:{parts[1].zfill(2)}:{parts[2].zfill(2)}"
        return timecode_str

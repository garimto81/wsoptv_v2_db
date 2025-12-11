"""Tests for Row Mapper - Block D (Sheets Sync Agent).

TDD: RED -> GREEN -> REFACTOR
"""

import pytest
from src.services.sheets_sync.row_mapper import RowMapper, MappedHandClip


class TestRowMapper:
    """Test cases for RowMapper."""

    # ==================== ARCHIVE SHEET ====================

    def test_map_archive_row_success(self):
        """Test mapping a valid archive row."""
        row = [
            "00:15:30",      # timecode
            "00:16:45",      # timecode_end
            "Amazing Bluff", # title
            "★★★",          # hand_grade
            "Phil Ivey, Tom Dwan",  # players
            "bluff, hero",   # tags
            "Great hand!",   # notes
            "WSOP_2024.mp4", # video_filename
            "$500,000",      # pot_size
            "Ace High",      # winner_hand
            "AA vs KK",      # hands_involved
        ]

        result = RowMapper.map_archive_row(row, row_number=5)

        assert result is not None
        assert result.row_number == 5
        assert result.sheet_source == "METADATA_ARCHIVE"
        assert result.timecode == "00:15:30"
        assert result.timecode_end == "00:16:45"
        assert result.title == "Amazing Bluff"
        assert result.hand_grade == "★★★"
        assert result.pot_size == 500000
        assert "Phil Ivey" in result.player_names
        assert "Tom Dwan" in result.player_names
        assert "bluff" in result.tag_names

    def test_map_archive_row_empty(self):
        """Test mapping empty row returns None."""
        result = RowMapper.map_archive_row([], row_number=1)

        assert result is None

    def test_map_archive_row_minimal(self):
        """Test mapping row with minimal data."""
        row = ["00:01:00", "", "Title Only"]

        result = RowMapper.map_archive_row(row, row_number=1)

        assert result is not None
        assert result.title == "Title Only"
        assert result.player_names == []
        assert result.tag_names == []

    def test_map_archive_row_pot_size_formats(self):
        """Test parsing different pot size formats."""
        rows = [
            (["", "", "T1", "", "", "", "", "", "$100,000"], 100000),
            (["", "", "T2", "", "", "", "", "", "50000"], 50000),
            (["", "", "T3", "", "", "", "", "", "$1,234,567"], 1234567),
        ]

        for row, expected_pot in rows:
            result = RowMapper.map_archive_row(row, row_number=1)
            assert result.pot_size == expected_pot

    # ==================== ICONIK SHEET ====================

    def test_map_iconik_row_success(self):
        """Test mapping a valid iconik row."""
        row = [
            "Cool Hand",     # title
            "01:30:00",      # timecode
            "2:30",          # duration (2m 30s)
            "cooler, epic",  # tags
            "Daniel Negreanu",  # players
            "Some notes",    # notes
        ]

        result = RowMapper.map_iconik_row(row, row_number=10)

        assert result is not None
        assert result.row_number == 10
        assert result.sheet_source == "ICONIK_METADATA"
        assert result.title == "Cool Hand"
        assert result.timecode == "01:30:00"
        assert result.duration_seconds == 150  # 2m 30s
        assert "cooler" in result.tag_names
        assert "Daniel Negreanu" in result.player_names

    def test_map_iconik_row_empty(self):
        """Test mapping empty row returns None."""
        result = RowMapper.map_iconik_row([], row_number=1)

        assert result is None

    # ==================== DURATION PARSING ====================

    def test_parse_duration_minutes_seconds(self):
        """Test parsing MM:SS format."""
        assert RowMapper._parse_duration("2:30") == 150

    def test_parse_duration_hours_minutes_seconds(self):
        """Test parsing HH:MM:SS format."""
        assert RowMapper._parse_duration("01:30:00") == 5400

    def test_parse_duration_seconds_only(self):
        """Test parsing seconds only."""
        assert RowMapper._parse_duration("90") == 90

    def test_parse_duration_invalid(self):
        """Test parsing invalid duration returns None."""
        assert RowMapper._parse_duration("invalid") is None
        assert RowMapper._parse_duration("") is None

    # ==================== PLAYER/TAG PARSING ====================

    def test_parse_comma_separated_players(self):
        """Test parsing comma-separated player names."""
        row = ["", "", "T", "", "Phil, Tom, Daniel", ""]

        result = RowMapper.map_archive_row(row, row_number=1)

        assert len(result.player_names) == 3
        assert "Phil" in result.player_names
        assert "Tom" in result.player_names
        assert "Daniel" in result.player_names

    def test_parse_comma_separated_tags(self):
        """Test parsing comma-separated tag names."""
        row = ["", "", "T", "", "", "bluff, cooler, hero_call"]

        result = RowMapper.map_archive_row(row, row_number=1)

        assert len(result.tag_names) == 3
        assert "bluff" in result.tag_names
        assert "cooler" in result.tag_names
        assert "hero_call" in result.tag_names

    def test_strip_whitespace_from_players_and_tags(self):
        """Test whitespace is stripped from players and tags."""
        row = ["", "", "T", "", "  Phil  ,  Tom  ", "  bluff  ,  hero  "]

        result = RowMapper.map_archive_row(row, row_number=1)

        assert result.player_names == ["Phil", "Tom"]
        assert result.tag_names == ["bluff", "hero"]


class TestMappedHandClip:
    """Test cases for MappedHandClip dataclass."""

    def test_default_empty_lists(self):
        """Test default empty lists for players and tags."""
        clip = MappedHandClip(row_number=1, sheet_source="TEST")

        assert clip.player_names == []
        assert clip.tag_names == []

    def test_all_fields_optional(self):
        """Test all content fields are optional."""
        clip = MappedHandClip(row_number=1, sheet_source="TEST")

        assert clip.title is None
        assert clip.timecode is None
        assert clip.pot_size is None

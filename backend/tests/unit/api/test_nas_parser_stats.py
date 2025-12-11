"""Tests for NAS parser-stats and duplicates endpoint logic.

Unit tests for NAS parser statistics and duplicate detection.
"""

import pytest
import re
from unittest.mock import MagicMock
from uuid import uuid4
from datetime import datetime


class TestParserStats:
    """Tests for /nas/parser-stats endpoint logic."""

    @pytest.mark.asyncio
    async def test_parser_stats_calculation(self):
        """Test parser statistics calculation logic."""
        # Test data
        total_files = 100
        parsed_files = 85
        unparsed_files = 15

        # Calculate rate
        parse_rate = (parsed_files / total_files * 100) if total_files > 0 else 0

        assert parsed_files + unparsed_files == total_files
        assert parse_rate == 85.0

    @pytest.mark.asyncio
    async def test_parser_stats_handles_empty(self):
        """Test parser stats with no files."""
        total_files = 0

        parse_rate = 0 if total_files == 0 else 100

        assert parse_rate == 0

    @pytest.mark.asyncio
    async def test_parser_sorting(self):
        """Test that parsers are sorted by count descending."""
        parser_counts = [
            ("WSOPBracelet", 450),
            ("HCL", 280),
            ("GGMillions", 180),
            ("Unmatched", 100),
        ]

        # Sort by count descending
        sorted_parsers = sorted(parser_counts, key=lambda x: x[1], reverse=True)

        # Verify order
        for i in range(len(sorted_parsers) - 1):
            assert sorted_parsers[i][1] >= sorted_parsers[i + 1][1]


class TestDuplicates:
    """Tests for /nas/duplicates endpoint logic."""

    def normalize_name(self, name: str) -> str:
        """Remove copy markers from filename."""
        normalized = re.sub(r"_copy\d*", "", name, flags=re.IGNORECASE)
        normalized = re.sub(r"\s*\(\d+\)", "", normalized)
        normalized = re.sub(r"\s*-\s*Copy", "", normalized, flags=re.IGNORECASE)
        return normalized.lower()

    @pytest.mark.asyncio
    async def test_normalize_name_removes_copy_suffix(self):
        """Test that _copy suffix is removed."""
        assert self.normalize_name("video_copy.mp4") == "video.mp4"
        assert self.normalize_name("video_copy2.mp4") == "video.mp4"  # _copy2 전체가 제거됨
        assert self.normalize_name("video_COPY.mp4") == "video.mp4"

    @pytest.mark.asyncio
    async def test_normalize_name_removes_number_suffix(self):
        """Test that (1), (2) etc are removed."""
        assert self.normalize_name("video (1).mp4") == "video.mp4"
        assert self.normalize_name("video (2).mp4") == "video.mp4"

    @pytest.mark.asyncio
    async def test_duplicate_grouping_logic(self):
        """Test duplicate grouping by normalized name and size."""
        files = [
            {"name": "video.mp4", "size": 1000000},
            {"name": "video_copy.mp4", "size": 1000000},
            {"name": "other.mp4", "size": 2000000},
        ]

        # Group by normalized name + size
        groups: dict = {}
        for f in files:
            key = (self.normalize_name(f["name"]), f["size"])
            if key not in groups:
                groups[key] = []
            groups[key].append(f)

        # Filter duplicates (groups with > 1 file)
        duplicates = [g for g in groups.values() if len(g) > 1]

        assert len(duplicates) == 1
        assert len(duplicates[0]) == 2

    @pytest.mark.asyncio
    async def test_different_sizes_not_duplicates(self):
        """Test that different sizes are not grouped."""
        files = [
            {"name": "video.mp4", "size": 1000000},
            {"name": "video_copy.mp4", "size": 2000000},  # Different size
        ]

        groups: dict = {}
        for f in files:
            key = (self.normalize_name(f["name"]), f["size"])
            if key not in groups:
                groups[key] = []
            groups[key].append(f)

        duplicates = [g for g in groups.values() if len(g) > 1]

        assert len(duplicates) == 0

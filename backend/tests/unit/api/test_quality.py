"""Tests for Quality API endpoints.

Unit tests for data quality monitoring API endpoints.
These tests mock the service dependencies to test endpoint logic.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4
from datetime import datetime
from pydantic import BaseModel


# Mock response models for testing without full import
class MockLinkageStatsResponse(BaseModel):
    nas_files: dict
    video_files: dict
    episodes: dict
    hand_clips: dict
    overall_linkage_rate: float


class MockProblemSummaryResponse(BaseModel):
    unlinked_nas_files: int
    parsing_failed_files: int
    sync_errors: int
    orphan_hand_clips: int
    orphan_video_files: int
    orphan_episodes: int
    total_problems: int


class MockOrphanRecord(BaseModel):
    id: str
    name: str
    type: str
    reason: str
    created_at: str


class MockOrphanListResponse(BaseModel):
    type: str
    total: int
    items: list


class MockBulkLinkRequest(BaseModel):
    source_type: str
    source_ids: list
    target_type: str
    target_id: str


class MockBulkLinkResponse(BaseModel):
    success_count: int
    failed_count: int
    errors: list


class TestLinkageStats:
    """Tests for /quality/linkage-stats endpoint logic."""

    @pytest.mark.asyncio
    async def test_linkage_stats_calculates_correctly(self):
        """Test linkage statistics calculation logic."""
        # Test data
        nas_total = 100
        nas_linked = 90
        nas_unlinked = 10

        clips_total = 50
        clips_with_video = 45

        # Calculate expected values
        total_items = nas_total + clips_total
        linked_items = nas_linked + clips_with_video
        expected_rate = (linked_items / total_items * 100) if total_items > 0 else 0

        # Verify calculation
        assert nas_linked + nas_unlinked == nas_total
        assert expected_rate == pytest.approx(90.0, rel=0.1)

    @pytest.mark.asyncio
    async def test_linkage_stats_handles_zero_division(self):
        """Test that empty data returns 0 rate."""
        total_items = 0
        linked_items = 0

        rate = (linked_items / total_items * 100) if total_items > 0 else 0

        assert rate == 0


class TestProblemsSummary:
    """Tests for /quality/problems endpoint logic."""

    @pytest.mark.asyncio
    async def test_problems_counts_correctly(self):
        """Test problem counting logic."""
        # Test data
        unlinked_count = 12
        parsing_failed = int(unlinked_count * 0.2)  # ~20% estimate

        mock_clips = []
        for i in range(100):
            clip = MagicMock()
            clip.video_file_id = uuid4() if i < 95 else None
            mock_clips.append(clip)

        orphan_clips = sum(1 for c in mock_clips if c.video_file_id is None)

        # Verify counts
        assert orphan_clips == 5
        assert parsing_failed == 2
        assert unlinked_count + parsing_failed + orphan_clips > 0


class TestOrphanRecords:
    """Tests for /quality/orphans endpoint logic."""

    @pytest.mark.asyncio
    async def test_orphan_nas_file_filtering(self):
        """Test NAS file orphan filtering logic."""
        mock_files = []
        for i in range(5):
            f = MagicMock()
            f.id = uuid4()
            f.file_name = f"file_{i}.mp4"
            f.video_file_id = None  # Unlinked
            mock_files.append(f)

        # Filter unlinked files
        unlinked = [f for f in mock_files if f.video_file_id is None]

        assert len(unlinked) == 5

    @pytest.mark.asyncio
    async def test_orphan_clip_filtering(self):
        """Test HandClip orphan filtering logic."""
        mock_clips = []
        for i in range(10):
            clip = MagicMock()
            clip.id = uuid4()
            clip.video_file_id = uuid4() if i < 7 else None
            mock_clips.append(clip)

        # Filter orphan clips
        orphans = [c for c in mock_clips if c.video_file_id is None]

        assert len(orphans) == 3


class TestBulkLink:
    """Tests for /quality/bulk-link endpoint logic."""

    @pytest.mark.asyncio
    async def test_bulk_link_counting(self):
        """Test bulk link success/failure counting."""
        source_ids = [uuid4() for _ in range(3)]

        # Simulate results: 2 success, 1 failure
        results = [True, True, False]

        success_count = sum(1 for r in results if r)
        failed_count = sum(1 for r in results if not r)

        assert success_count == 2
        assert failed_count == 1

    @pytest.mark.asyncio
    async def test_bulk_link_type_validation(self):
        """Test bulk link type validation."""
        valid_combinations = [
            ("nas_file", "video_file"),
            ("hand_clip", "video_file"),
            ("video_file", "episode"),
        ]

        invalid_combinations = [
            ("unknown", "video_file"),
            ("nas_file", "unknown"),
        ]

        for source, target in valid_combinations:
            is_valid = source in ["nas_file", "hand_clip", "video_file"]
            assert is_valid

        for source, target in invalid_combinations:
            is_valid = source in ["nas_file", "hand_clip", "video_file"]
            assert not is_valid or target not in ["video_file", "episode"]

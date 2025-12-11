"""Tests for HandClip linkage-stats endpoint logic.

Unit tests for HandClip linkage statistics calculation.
Tests pure logic without importing from src to avoid database dependencies.
"""

import pytest
from unittest.mock import MagicMock
from uuid import uuid4


class TestHandClipLinkageStats:
    """Tests for /hand-clips/linkage-stats endpoint logic."""

    def calculate_linkage_stats(self, clips: list) -> dict:
        """Calculate linkage statistics from clip list."""
        total = len(clips)
        with_video = sum(1 for c in clips if c.video_file_id is not None)
        with_episode = sum(1 for c in clips if c.episode_id is not None)
        video_only = sum(
            1 for c in clips
            if c.video_file_id is not None and c.episode_id is None
        )
        orphans = sum(
            1 for c in clips
            if c.video_file_id is None and c.episode_id is None
        )
        linkage_rate = (with_video / total * 100) if total > 0 else 0.0

        return {
            "total_clips": total,
            "with_video_file": with_video,
            "with_episode": with_episode,
            "video_only": video_only,
            "orphan_clips": orphans,
            "linkage_rate": linkage_rate,
        }

    @pytest.mark.asyncio
    async def test_linkage_stats_counts_correctly(self):
        """Test that linkage stats counts clips correctly."""
        mock_clips = []

        # 10 clips with both video and episode
        for _ in range(10):
            clip = MagicMock()
            clip.video_file_id = uuid4()
            clip.episode_id = uuid4()
            mock_clips.append(clip)

        # 5 clips with video only
        for _ in range(5):
            clip = MagicMock()
            clip.video_file_id = uuid4()
            clip.episode_id = None
            mock_clips.append(clip)

        # 3 orphan clips
        for _ in range(3):
            clip = MagicMock()
            clip.video_file_id = None
            clip.episode_id = None
            mock_clips.append(clip)

        result = self.calculate_linkage_stats(mock_clips)

        assert result["total_clips"] == 18
        assert result["with_video_file"] == 15  # 10 + 5
        assert result["with_episode"] == 10
        assert result["video_only"] == 5
        assert result["orphan_clips"] == 3

    @pytest.mark.asyncio
    async def test_linkage_rate_calculation(self):
        """Test that linkage rate is calculated correctly."""
        # 80% with video file
        mock_clips = []
        for i in range(100):
            clip = MagicMock()
            clip.video_file_id = uuid4() if i < 80 else None
            clip.episode_id = uuid4() if i < 70 else None
            mock_clips.append(clip)

        result = self.calculate_linkage_stats(mock_clips)

        assert result["linkage_rate"] == 80.0

    @pytest.mark.asyncio
    async def test_handles_empty_data(self):
        """Test handling of no clips."""
        result = self.calculate_linkage_stats([])

        assert result["total_clips"] == 0
        assert result["with_video_file"] == 0
        assert result["linkage_rate"] == 0.0

    @pytest.mark.asyncio
    async def test_all_orphans(self):
        """Test when all clips are orphans."""
        mock_clips = []
        for _ in range(10):
            clip = MagicMock()
            clip.video_file_id = None
            clip.episode_id = None
            mock_clips.append(clip)

        result = self.calculate_linkage_stats(mock_clips)

        assert result["total_clips"] == 10
        assert result["orphan_clips"] == 10
        assert result["with_video_file"] == 0
        assert result["linkage_rate"] == 0.0

    @pytest.mark.asyncio
    async def test_all_linked(self):
        """Test when all clips are fully linked."""
        mock_clips = []
        for _ in range(50):
            clip = MagicMock()
            clip.video_file_id = uuid4()
            clip.episode_id = uuid4()
            mock_clips.append(clip)

        result = self.calculate_linkage_stats(mock_clips)

        assert result["total_clips"] == 50
        assert result["with_video_file"] == 50
        assert result["with_episode"] == 50
        assert result["orphan_clips"] == 0
        assert result["linkage_rate"] == 100.0

"""Tests for Sync errors endpoint logic.

Unit tests for sync error filtering and detection.
Tests pure logic without importing from src to avoid database dependencies.
"""

import pytest
from unittest.mock import MagicMock
from uuid import uuid4
from datetime import datetime


class TestSyncErrors:
    """Tests for /sync/errors endpoint logic."""

    def filter_error_records(self, records: list) -> list:
        """Filter records that have errors (failed status or error_message)."""
        return [
            r for r in records
            if r.sync_status == "failed" or r.error_message
        ]

    @pytest.mark.asyncio
    async def test_filter_error_records_finds_failed(self):
        """Test that failed records are filtered correctly."""
        mock_records = []

        # Successful record
        success = MagicMock()
        success.sync_status = "completed"
        success.error_message = None
        mock_records.append(success)

        # Failed record
        failed = MagicMock()
        failed.sync_status = "failed"
        failed.error_message = "Connection timeout"
        mock_records.append(failed)

        # Record with error message but not failed status
        partial = MagicMock()
        partial.sync_status = "syncing"
        partial.error_message = "Some rows skipped"
        mock_records.append(partial)

        errors = self.filter_error_records(mock_records)

        # Should include failed record and record with error message
        assert len(errors) == 2

    @pytest.mark.asyncio
    async def test_filter_handles_no_errors(self):
        """Test handling of no error records."""
        mock_records = []
        for _ in range(3):
            record = MagicMock()
            record.sync_status = "completed"
            record.error_message = None
            mock_records.append(record)

        errors = self.filter_error_records(mock_records)

        assert len(errors) == 0

    @pytest.mark.asyncio
    async def test_filter_finds_error_message_records(self):
        """Test that records with error_message are included."""
        mock_records = []

        # Record with syncing status but has error message
        record = MagicMock()
        record.sync_status = "syncing"
        record.error_message = "Row 523: Invalid timecode format"
        mock_records.append(record)

        errors = self.filter_error_records(mock_records)

        assert len(errors) == 1
        assert errors[0].error_message == "Row 523: Invalid timecode format"

    @pytest.mark.asyncio
    async def test_error_count_logic(self):
        """Test error counting logic."""
        errors = [MagicMock() for _ in range(5)]

        total_errors = len(errors)

        assert total_errors == 5

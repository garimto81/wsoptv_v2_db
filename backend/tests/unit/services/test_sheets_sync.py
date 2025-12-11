"""Unit tests for Sheets Sync services - Block D.

Tests cover:
- RowMapper (row parsing)
- TagClassifier (tag categorization)
- PlayerMatcher (name normalization)
- SheetsDataMapper (data persistence)
- SheetsSyncEngine (sync orchestration)
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4
from datetime import datetime, timezone

from src.services.sheets_sync import (
    RowMapper,
    MappedHandClip,
    TagClassifier,
    PlayerMatcher,
    SheetsDataMapper,
    SyncResult,
    SheetsSyncEngine,
    EngineSyncResult,
)
from src.models.tag import TagCategory
from src.models.google_sheet_sync import SyncStatus


# ====================
# RowMapper Tests
# ====================

class TestRowMapper:
    """Tests for RowMapper class."""

    def test_map_archive_row_valid(self):
        """Test mapping valid METADATA_ARCHIVE row."""
        # Format: timecode, timecode_end, title, hand_grade, players, tags, notes, video_filename, pot_size, winner_hand, hands_involved
        row = [
            "01:23:45",
            "01:24:30",
            "Epic Bluff by Phil Ivey",
            "A+",
            "Phil Ivey, Tom Dwan",
            "bluff, hero_call",
            "Amazing hand",
            "wsop_2024_ep1.mp4",
            "$250,000",
            "AA",
            "AA vs KK",
        ]

        result = RowMapper.map_archive_row(row, 5)

        assert result is not None
        assert result.row_number == 5
        assert result.sheet_source == "METADATA_ARCHIVE"
        assert result.timecode == "01:23:45"
        assert result.timecode_end == "01:24:30"
        assert result.title == "Epic Bluff by Phil Ivey"
        assert result.hand_grade == "A+"
        assert result.player_names == ["Phil Ivey", "Tom Dwan"]
        assert result.tag_names == ["bluff", "hero_call"]
        assert result.notes == "Amazing hand"
        assert result.pot_size == 250000
        assert result.winner_hand == "AA"
        assert result.hands_involved == "AA vs KK"

    def test_map_archive_row_minimal(self):
        """Test mapping archive row with minimal data."""
        row = ["01:00:00", "", "Simple Hand"]

        result = RowMapper.map_archive_row(row, 1)

        assert result is not None
        assert result.timecode == "01:00:00"
        assert result.title == "Simple Hand"
        assert result.player_names == []
        assert result.tag_names == []

    def test_map_archive_row_empty(self):
        """Test that empty row returns None."""
        assert RowMapper.map_archive_row([], 1) is None
        assert RowMapper.map_archive_row(["", "", ""], 1) is None

    def test_map_archive_row_pot_size_parsing(self):
        """Test various pot size formats."""
        # With dollar sign and comma
        row = ["01:00:00", "", "Hand", "", "", "", "", "", "$1,234,567"]
        result = RowMapper.map_archive_row(row, 1)
        assert result.pot_size == 1234567

        # Plain number
        row[8] = "50000"
        result = RowMapper.map_archive_row(row, 1)
        assert result.pot_size == 50000

        # Invalid
        row[8] = "invalid"
        result = RowMapper.map_archive_row(row, 1)
        assert result.pot_size is None

    def test_map_iconik_row_valid(self):
        """Test mapping valid ICONIK_METADATA row."""
        # Format: title, timecode, duration, tags, players, notes
        row = [
            "River Bluff",
            "00:15:30",
            "1:45",
            "bluff, river",
            "Daniel Negreanu",
            "Great play",
        ]

        result = RowMapper.map_iconik_row(row, 10)

        assert result is not None
        assert result.row_number == 10
        assert result.sheet_source == "ICONIK_METADATA"
        assert result.title == "River Bluff"
        assert result.timecode == "00:15:30"
        assert result.duration_seconds == 105  # 1:45
        assert result.tag_names == ["bluff", "river"]
        assert result.player_names == ["Daniel Negreanu"]
        assert result.notes == "Great play"

    def test_map_iconik_row_empty(self):
        """Test that empty row returns None."""
        assert RowMapper.map_iconik_row([], 1) is None
        assert RowMapper.map_iconik_row(["", ""], 1) is None

    def test_parse_duration_formats(self):
        """Test duration parsing with various formats."""
        # MM:SS
        assert RowMapper._parse_duration("1:30") == 90
        assert RowMapper._parse_duration("10:00") == 600

        # HH:MM:SS
        assert RowMapper._parse_duration("01:30:00") == 5400
        assert RowMapper._parse_duration("00:01:30") == 90

        # Seconds only
        assert RowMapper._parse_duration("90") == 90

        # Invalid
        assert RowMapper._parse_duration("invalid") is None

    def test_parse_timecode_normalization(self):
        """Test timecode normalization."""
        assert RowMapper._parse_timecode("1:30") == "00:01:30"
        assert RowMapper._parse_timecode("01:30") == "00:01:30"
        assert RowMapper._parse_timecode("01:30:45") == "01:30:45"
        assert RowMapper._parse_timecode(None) is None


# ====================
# TagClassifier Tests
# ====================

class TestTagClassifier:
    """Tests for TagClassifier class."""

    def test_classify_poker_play(self):
        """Test classification of poker play tags."""
        assert TagClassifier.classify("bluff") == TagCategory.POKER_PLAY
        assert TagClassifier.classify("Hero Call") == TagCategory.POKER_PLAY
        assert TagClassifier.classify("3bet_light") == TagCategory.POKER_PLAY
        assert TagClassifier.classify("올인") == TagCategory.POKER_PLAY
        assert TagClassifier.classify("value_bet") == TagCategory.POKER_PLAY

    def test_classify_emotion(self):
        """Test classification of emotion tags."""
        assert TagClassifier.classify("stress") == TagCategory.EMOTION
        assert TagClassifier.classify("excited") == TagCategory.EMOTION
        assert TagClassifier.classify("frustration") == TagCategory.EMOTION
        assert TagClassifier.classify("긴장감") == TagCategory.EMOTION

    def test_classify_epic_hand(self):
        """Test classification of epic hand tags."""
        assert TagClassifier.classify("royal_flush") == TagCategory.EPIC_HAND
        assert TagClassifier.classify("quads") == TagCategory.EPIC_HAND
        assert TagClassifier.classify("포카드") == TagCategory.EPIC_HAND
        assert TagClassifier.classify("full_house") == TagCategory.EPIC_HAND

    def test_classify_runout(self):
        """Test classification of runout tags."""
        assert TagClassifier.classify("runner_runner") == TagCategory.RUNOUT
        assert TagClassifier.classify("backdoor_draw") == TagCategory.RUNOUT
        assert TagClassifier.classify("러너러너") == TagCategory.RUNOUT
        # Note: backdoor_flush matches EPIC_HAND due to "flush" keyword

    def test_classify_default_adjective(self):
        """Test default classification to adjective."""
        assert TagClassifier.classify("interesting") == TagCategory.ADJECTIVE
        assert TagClassifier.classify("highlight") == TagCategory.ADJECTIVE
        assert TagClassifier.classify("unknown_tag") == TagCategory.ADJECTIVE


# ====================
# PlayerMatcher Tests
# ====================

class TestPlayerMatcher:
    """Tests for PlayerMatcher class."""

    def test_normalize_known_player(self):
        """Test normalization of known players."""
        assert PlayerMatcher.normalize_name("phil ivey") == "Phil Ivey"
        assert PlayerMatcher.normalize_name("PHIL IVEY") == "Phil Ivey"
        assert PlayerMatcher.normalize_name("tom dwan") == "Tom Dwan"
        assert PlayerMatcher.normalize_name("daniel negreanu") == "Daniel Negreanu"

    def test_normalize_unknown_player(self):
        """Test title case for unknown players."""
        assert PlayerMatcher.normalize_name("john smith") == "John Smith"
        assert PlayerMatcher.normalize_name("JANE DOE") == "Jane Doe"

    def test_normalize_whitespace(self):
        """Test whitespace cleanup."""
        assert PlayerMatcher.normalize_name("  Phil   Ivey  ") == "Phil Ivey"
        assert PlayerMatcher.normalize_name("Tom\t\nDwan") == "Tom Dwan"

    def test_normalize_empty(self):
        """Test empty input."""
        assert PlayerMatcher.normalize_name("") == ""
        assert PlayerMatcher.normalize_name(None) is None


# ====================
# SyncResult Tests
# ====================

class TestSyncResult:
    """Tests for SyncResult dataclass."""

    def test_default_values(self):
        """Test default initialization."""
        result = SyncResult()

        assert result.total_rows == 0
        assert result.created == 0
        assert result.updated == 0
        assert result.skipped == 0
        assert result.errors == 0
        assert result.error_messages == []

    def test_with_values(self):
        """Test initialization with values."""
        result = SyncResult(
            total_rows=100,
            created=80,
            updated=10,
            skipped=5,
            errors=5,
            error_messages=["Error 1", "Error 2"],
        )

        assert result.total_rows == 100
        assert result.created == 80
        assert result.errors == 5
        assert len(result.error_messages) == 2


# ====================
# MappedHandClip Tests
# ====================

class TestMappedHandClip:
    """Tests for MappedHandClip dataclass."""

    def test_default_lists(self):
        """Test default list initialization."""
        clip = MappedHandClip(row_number=1, sheet_source="TEST")

        assert clip.player_names == []
        assert clip.tag_names == []

    def test_with_lists(self):
        """Test initialization with lists."""
        clip = MappedHandClip(
            row_number=1,
            sheet_source="TEST",
            player_names=["Player 1"],
            tag_names=["tag1", "tag2"],
        )

        assert clip.player_names == ["Player 1"]
        assert clip.tag_names == ["tag1", "tag2"]


# ====================
# SheetsDataMapper Tests (Mocked)
# ====================

class TestSheetsDataMapper:
    """Tests for SheetsDataMapper class with mocked services."""

    @pytest.fixture
    def mock_session(self):
        """Create mock AsyncSession."""
        return AsyncMock()

    @pytest.fixture
    def mock_services(self, mock_session):
        """Create mock service instances."""
        hand_clip_service = AsyncMock()
        player_service = AsyncMock()
        tag_service = AsyncMock()

        return {
            "session": mock_session,
            "hand_clip_service": hand_clip_service,
            "player_service": player_service,
            "tag_service": tag_service,
        }

    @pytest.fixture
    def data_mapper(self, mock_services):
        """Create SheetsDataMapper with mocked services."""
        return SheetsDataMapper(
            mock_services["session"],
            mock_services["hand_clip_service"],
            mock_services["player_service"],
            mock_services["tag_service"],
        )

    @pytest.mark.asyncio
    async def test_get_or_create_player_cached(self, data_mapper, mock_services):
        """Test player caching."""
        mock_player = MagicMock(id=uuid4(), name="Phil Ivey")
        mock_services["player_service"].get_or_create.return_value = mock_player

        # First call
        player1 = await data_mapper.get_or_create_player("Phil Ivey")
        # Second call (should use cache)
        player2 = await data_mapper.get_or_create_player("phil ivey")

        assert player1 == mock_player
        assert player2 == mock_player
        # Should only call service once due to caching
        assert mock_services["player_service"].get_or_create.call_count == 1

    @pytest.mark.asyncio
    async def test_get_or_create_tag_with_classification(self, data_mapper, mock_services):
        """Test tag creation with auto-classification."""
        mock_tag = MagicMock(id=uuid4(), name="bluff")
        mock_services["tag_service"].get_or_create.return_value = mock_tag

        tag = await data_mapper.get_or_create_tag("bluff")

        assert tag == mock_tag
        mock_services["tag_service"].get_or_create.assert_called_once_with(
            TagCategory.POKER_PLAY, "bluff"
        )

    @pytest.mark.asyncio
    async def test_sync_archive_rows_success(self, data_mapper, mock_services):
        """Test syncing archive rows."""
        # Create clips with matching row numbers
        mock_clip1 = MagicMock(id=uuid4(), sheet_row_number=1)
        mock_clip2 = MagicMock(id=uuid4(), sheet_row_number=2)
        mock_services["hand_clip_service"].get_by_sheet_row.return_value = None
        mock_services["hand_clip_service"].create.side_effect = [mock_clip1, mock_clip2]

        rows = [
            ["01:00:00", "", "Hand 1", "", "", "", ""],
            ["01:05:00", "", "Hand 2", "", "", "", ""],
        ]

        result = await data_mapper.sync_archive_rows(rows, start_row=1)

        assert result.total_rows == 2
        assert result.created == 2
        assert result.errors == 0

    @pytest.mark.asyncio
    async def test_sync_archive_rows_skip_duplicates(self, data_mapper, mock_services):
        """Test that duplicate rows are skipped."""
        # Return existing clip with different row number to trigger skip
        existing_clip = MagicMock(id=uuid4(), sheet_row_number=99)  # Different from row 1
        mock_services["hand_clip_service"].get_by_sheet_row.return_value = existing_clip

        rows = [["01:00:00", "", "Hand 1"]]

        result = await data_mapper.sync_archive_rows(rows, start_row=1)

        assert result.total_rows == 1
        assert result.skipped == 1
        assert result.created == 0

    @pytest.mark.asyncio
    async def test_sync_iconik_rows_success(self, data_mapper, mock_services):
        """Test syncing iconik rows."""
        mock_clip = MagicMock(id=uuid4(), sheet_row_number=1)
        mock_services["hand_clip_service"].get_by_sheet_row.return_value = None
        mock_services["hand_clip_service"].create.return_value = mock_clip

        rows = [
            ["Hand 1", "01:00:00", "1:30", "tag1", "Player1", "notes"],
        ]

        result = await data_mapper.sync_iconik_rows(rows, start_row=1)

        assert result.total_rows == 1
        assert result.created == 1

    def test_clear_cache(self, data_mapper):
        """Test cache clearing."""
        # Add items to cache
        data_mapper._player_cache["test"] = MagicMock()
        data_mapper._tag_cache[("cat", "tag")] = MagicMock()

        data_mapper.clear_cache()

        assert len(data_mapper._player_cache) == 0
        assert len(data_mapper._tag_cache) == 0


# ====================
# EngineSyncResult Tests
# ====================

class TestEngineSyncResult:
    """Tests for EngineSyncResult dataclass."""

    def test_creation(self):
        """Test EngineSyncResult creation."""
        now = datetime.now(timezone.utc)
        result = EngineSyncResult(
            sheet_id="spreadsheet123",
            sheet_name="METADATA_ARCHIVE",
            entity_type="hand_clip",
            status=SyncStatus.COMPLETED,
            started_at=now,
            completed_at=now,
            last_row_synced=100,
        )

        assert result.sheet_id == "spreadsheet123"
        assert result.sheet_name == "METADATA_ARCHIVE"
        assert result.status == SyncStatus.COMPLETED
        assert result.last_row_synced == 100


# ====================
# SheetsSyncEngine Tests (Mocked)
# ====================

class TestSheetsSyncEngine:
    """Tests for SheetsSyncEngine class with mocked dependencies."""

    @pytest.fixture
    def mock_session(self):
        """Create mock AsyncSession."""
        session = AsyncMock()
        session.commit = AsyncMock()
        session.rollback = AsyncMock()
        session.flush = AsyncMock()
        return session

    @pytest.fixture
    def mock_sheets_client(self):
        """Create mock SheetsClient."""
        client = MagicMock()
        return client

    @pytest.fixture
    def engine(self, mock_session, mock_sheets_client):
        """Create SheetsSyncEngine with mocks."""
        with patch("src.services.sheets_sync.sync_engine.SheetsSyncService") as mock_service_class, \
             patch("src.services.sheets_sync.sync_engine.SheetsDataMapper") as mock_mapper_class:

            mock_sync_service = AsyncMock()
            mock_data_mapper = AsyncMock()

            mock_service_class.return_value = mock_sync_service
            mock_mapper_class.return_value = mock_data_mapper

            engine = SheetsSyncEngine(mock_session, mock_sheets_client)
            engine.sync_service = mock_sync_service
            engine.data_mapper = mock_data_mapper

            return engine

    @pytest.mark.asyncio
    async def test_sync_sheet_no_rows(self, engine, mock_sheets_client):
        """Test sync when no new rows."""
        # Setup
        mock_record = MagicMock(id=uuid4(), last_row_synced=100)
        engine.sync_service.start_sync.return_value = mock_record
        engine.sync_service.complete_sync.return_value = None

        mock_range = MagicMock()
        mock_range.values = []
        mock_sheets_client.read_rows_from.return_value = mock_range

        result = await engine.sync_sheet(
            "spreadsheet123",
            "METADATA_ARCHIVE",
            "hand_clip",
        )

        assert result.status == SyncStatus.COMPLETED
        assert result.sync_result.total_rows == 0

    @pytest.mark.asyncio
    async def test_sync_sheet_with_rows(self, engine, mock_sheets_client):
        """Test sync with new rows."""
        # Setup
        mock_record = MagicMock(id=uuid4(), last_row_synced=0)
        engine.sync_service.start_sync.return_value = mock_record
        engine.sync_service.complete_sync.return_value = None

        mock_range = MagicMock()
        mock_range.values = [
            ["01:00:00", "", "Hand 1"],
            ["01:05:00", "", "Hand 2"],
        ]
        mock_sheets_client.read_rows_from.return_value = mock_range

        mock_sync_result = SyncResult(total_rows=2, created=2)
        engine.data_mapper.sync_archive_rows.return_value = mock_sync_result

        result = await engine.sync_sheet(
            "spreadsheet123",
            "METADATA_ARCHIVE",
            "hand_clip",
        )

        assert result.status == SyncStatus.COMPLETED
        assert result.sync_result.total_rows == 2
        assert result.sync_result.created == 2

    @pytest.mark.asyncio
    async def test_sync_sheet_full_sync(self, engine, mock_sheets_client):
        """Test full sync mode."""
        mock_record = MagicMock(id=uuid4(), last_row_synced=50)
        engine.sync_service.start_sync.return_value = mock_record

        mock_range = MagicMock()
        mock_range.values = [["01:00:00", "", "Hand 1"]]
        mock_sheets_client.read_all_rows.return_value = mock_range

        mock_sync_result = SyncResult(total_rows=1, created=1)
        engine.data_mapper.sync_archive_rows.return_value = mock_sync_result

        result = await engine.sync_sheet(
            "spreadsheet123",
            "METADATA_ARCHIVE",
            "hand_clip",
            full_sync=True,
        )

        # Should use read_all_rows instead of read_rows_from
        mock_sheets_client.read_all_rows.assert_called_once()
        assert result.status == SyncStatus.COMPLETED

    @pytest.mark.asyncio
    async def test_sync_sheet_all_errors(self, engine, mock_sheets_client):
        """Test sync with all rows failing."""
        mock_record = MagicMock(id=uuid4(), last_row_synced=0)
        engine.sync_service.start_sync.return_value = mock_record
        engine.sync_service.fail_sync.return_value = None

        mock_range = MagicMock()
        mock_range.values = [["01:00:00", "", "Hand 1"]]
        mock_sheets_client.read_rows_from.return_value = mock_range

        # All rows failed
        mock_sync_result = SyncResult(
            total_rows=1,
            errors=1,
            error_messages=["Error in row 1"],
        )
        engine.data_mapper.sync_archive_rows.return_value = mock_sync_result

        result = await engine.sync_sheet(
            "spreadsheet123",
            "METADATA_ARCHIVE",
            "hand_clip",
        )

        assert result.status == SyncStatus.FAILED
        assert "All 1 rows failed" in result.error_message

    @pytest.mark.asyncio
    async def test_get_sync_status_not_started(self, engine):
        """Test status for unsynced sheet."""
        engine.sync_service.get_by_sheet_and_entity.return_value = None

        status = await engine.get_sync_status("spreadsheet123", "hand_clip")

        assert status["status"] == "not_started"
        assert status["last_row_synced"] == 0

    @pytest.mark.asyncio
    async def test_get_sync_status_existing(self, engine):
        """Test status for previously synced sheet."""
        mock_record = MagicMock()
        mock_record.sync_status = SyncStatus.COMPLETED
        mock_record.last_row_synced = 150
        mock_record.last_synced_at = datetime.now(timezone.utc)
        mock_record.error_message = None

        engine.sync_service.get_by_sheet_and_entity.return_value = mock_record

        status = await engine.get_sync_status("spreadsheet123", "hand_clip")

        assert status["status"] == SyncStatus.COMPLETED
        assert status["last_row_synced"] == 150

    @pytest.mark.asyncio
    async def test_reset_sync(self, engine, mock_session):
        """Test sync reset."""
        mock_record = MagicMock()
        mock_record.last_row_synced = 100

        engine.sync_service.get_by_sheet_and_entity.return_value = mock_record

        result = await engine.reset_sync("spreadsheet123", "hand_clip")

        assert result is True
        assert mock_record.last_row_synced == 0
        assert mock_record.sync_status == SyncStatus.IDLE
        mock_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_reset_sync_not_found(self, engine):
        """Test reset for non-existent record."""
        engine.sync_service.get_by_sheet_and_entity.return_value = None

        result = await engine.reset_sync("spreadsheet123", "hand_clip")

        assert result is False

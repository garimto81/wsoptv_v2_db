"""Tests for HandClipService - Block C (Hand Analysis Agent).

TDD: RED -> GREEN -> REFACTOR
"""

import pytest
import pytest_asyncio
from uuid import uuid4

from src.services.hand_analysis import HandClipService, TagService, PlayerService


class TestHandClipService:
    """Test cases for HandClipService."""

    @pytest_asyncio.fixture
    async def service(self, async_session):
        """Create HandClipService instance."""
        return HandClipService(async_session)

    @pytest_asyncio.fixture
    async def tag_service(self, async_session):
        """Create TagService instance."""
        return TagService(async_session)

    @pytest_asyncio.fixture
    async def player_service(self, async_session):
        """Create PlayerService instance."""
        return PlayerService(async_session)

    # ==================== CREATE ====================

    @pytest.mark.asyncio
    async def test_create_hand_clip_success(self, service, sample_hand_clip_data):
        """Test creating a hand clip successfully."""
        clip = await service.create_hand_clip(**sample_hand_clip_data)

        assert clip is not None
        assert clip.id is not None
        assert clip.title == sample_hand_clip_data["title"]
        assert clip.timecode == sample_hand_clip_data["timecode"]
        assert clip.hand_grade == sample_hand_clip_data["hand_grade"]
        assert clip.pot_size == sample_hand_clip_data["pot_size"]

    @pytest.mark.asyncio
    async def test_create_hand_clip_with_sheet_tracking(self, service):
        """Test creating a hand clip with sheet tracking info."""
        clip = await service.create_hand_clip(
            title="Test",
            sheet_source="METADATA_ARCHIVE",
            sheet_row_number=42,
        )

        assert clip is not None
        assert clip.sheet_source == "METADATA_ARCHIVE"
        assert clip.sheet_row_number == 42

    # ==================== READ ====================

    @pytest.mark.asyncio
    async def test_get_by_id_success(self, service, sample_hand_clip_data):
        """Test getting a hand clip by ID."""
        created = await service.create_hand_clip(**sample_hand_clip_data)

        found = await service.get_by_id(created.id)

        assert found is not None
        assert found.id == created.id

    @pytest.mark.asyncio
    async def test_get_by_id_not_found(self, service):
        """Test getting a non-existent hand clip."""
        found = await service.get_by_id(uuid4())

        assert found is None

    @pytest.mark.asyncio
    async def test_get_by_sheet_row(self, service):
        """Test getting hand clip by sheet source and row."""
        await service.create_hand_clip(
            title="Test",
            sheet_source="ARCHIVE",
            sheet_row_number=10,
        )

        found = await service.get_by_sheet_row("ARCHIVE", 10)

        assert found is not None
        assert found.sheet_row_number == 10

    @pytest.mark.asyncio
    async def test_get_by_grade(self, service):
        """Test getting hand clips by grade."""
        await service.create_hand_clip(title="3 Star", hand_grade="★★★")
        await service.create_hand_clip(title="2 Star", hand_grade="★★")
        await service.create_hand_clip(title="Another 3 Star", hand_grade="★★★")

        three_star_clips = await service.get_by_grade("★★★")

        assert len(three_star_clips) == 2

    @pytest.mark.asyncio
    async def test_get_high_pot_clips(self, service):
        """Test getting high pot clips."""
        await service.create_hand_clip(title="Small Pot", pot_size=50000)
        await service.create_hand_clip(title="Big Pot", pot_size=500000)
        await service.create_hand_clip(title="Huge Pot", pot_size=1000000)

        high_pots = await service.get_high_pot_clips(min_pot=100000)

        assert len(high_pots) == 2
        assert high_pots[0].pot_size >= high_pots[1].pot_size  # Sorted desc

    @pytest.mark.asyncio
    async def test_search_by_title(self, service):
        """Test searching hand clips by title."""
        await service.create_hand_clip(title="Amazing Bluff")
        await service.create_hand_clip(title="Hero Call")
        await service.create_hand_clip(title="Another Bluff")

        bluff_clips = await service.search_by_title("Bluff")

        assert len(bluff_clips) == 2

    # ==================== UPDATE ====================

    @pytest.mark.asyncio
    async def test_update_hand_clip_success(self, service, sample_hand_clip_data):
        """Test updating a hand clip."""
        created = await service.create_hand_clip(**sample_hand_clip_data)

        updated = await service.update(created.id, title="Updated Title")

        assert updated is not None
        assert updated.title == "Updated Title"

    @pytest.mark.asyncio
    async def test_update_hand_clip_not_found(self, service):
        """Test updating a non-existent hand clip."""
        updated = await service.update(uuid4(), title="New Title")

        assert updated is None

    # ==================== DELETE ====================

    @pytest.mark.asyncio
    async def test_delete_hand_clip_success(self, service, sample_hand_clip_data):
        """Test deleting a hand clip."""
        created = await service.create_hand_clip(**sample_hand_clip_data)

        result = await service.delete(created.id)

        assert result is True
        assert await service.get_by_id(created.id) is None

    @pytest.mark.asyncio
    async def test_delete_hand_clip_not_found(self, service):
        """Test deleting a non-existent hand clip."""
        result = await service.delete(uuid4())

        assert result is False

    # ==================== TAG MANAGEMENT ====================

    @pytest.mark.asyncio
    async def test_add_tag_to_clip(self, service, tag_service):
        """Test adding a tag to a hand clip."""
        clip = await service.create_hand_clip(title="Test Clip")
        tag = await tag_service.create_tag("poker_play", "bluff")

        result = await service.add_tag(clip.id, tag.id)

        assert result is True
        clip_with_tags = await service.get_with_relationships(clip.id)
        assert len(clip_with_tags.tags) == 1
        assert clip_with_tags.tags[0].name == "bluff"

    @pytest.mark.asyncio
    async def test_add_tag_clip_not_found(self, service, tag_service):
        """Test adding tag to non-existent clip."""
        tag = await tag_service.create_tag("poker_play", "bluff")

        result = await service.add_tag(uuid4(), tag.id)

        assert result is False

    @pytest.mark.asyncio
    async def test_add_tag_not_found(self, service):
        """Test adding non-existent tag to clip."""
        clip = await service.create_hand_clip(title="Test Clip")

        result = await service.add_tag(clip.id, uuid4())

        assert result is False

    @pytest.mark.asyncio
    async def test_remove_tag_from_clip(self, service, tag_service):
        """Test removing a tag from a hand clip."""
        clip = await service.create_hand_clip(title="Test Clip")
        tag = await tag_service.create_tag("poker_play", "bluff")
        await service.add_tag(clip.id, tag.id)

        result = await service.remove_tag(clip.id, tag.id)

        assert result is True
        clip_with_tags = await service.get_with_relationships(clip.id)
        assert len(clip_with_tags.tags) == 0

    # ==================== PLAYER MANAGEMENT ====================

    @pytest.mark.asyncio
    async def test_add_player_to_clip(self, service, player_service):
        """Test adding a player to a hand clip."""
        clip = await service.create_hand_clip(title="Test Clip")
        player = await player_service.create_player("Phil Ivey")

        result = await service.add_player(clip.id, player.id)

        assert result is True
        clip_with_players = await service.get_with_relationships(clip.id)
        assert len(clip_with_players.players) == 1
        assert clip_with_players.players[0].name == "Phil Ivey"

    @pytest.mark.asyncio
    async def test_add_player_clip_not_found(self, service, player_service):
        """Test adding player to non-existent clip."""
        player = await player_service.create_player("Phil Ivey")

        result = await service.add_player(uuid4(), player.id)

        assert result is False

    @pytest.mark.asyncio
    async def test_remove_player_from_clip(self, service, player_service):
        """Test removing a player from a hand clip."""
        clip = await service.create_hand_clip(title="Test Clip")
        player = await player_service.create_player("Phil Ivey")
        await service.add_player(clip.id, player.id)

        result = await service.remove_player(clip.id, player.id)

        assert result is True
        clip_with_players = await service.get_with_relationships(clip.id)
        assert len(clip_with_players.players) == 0

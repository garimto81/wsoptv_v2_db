"""Data Mapper - Block D (Sheets Sync Agent).

Maps sheet rows to database entities and persists them.
"""

from dataclasses import dataclass
from typing import Optional, Sequence
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from ...models.hand_clip import HandClip
from ...models.player import Player
from ...models.tag import Tag, TagCategory
from ..hand_analysis import HandClipService, PlayerService, TagService
from .row_mapper import MappedHandClip, RowMapper


@dataclass
class SyncResult:
    """Result of a sync operation."""

    total_rows: int = 0
    created: int = 0
    updated: int = 0
    skipped: int = 0
    errors: int = 0
    error_messages: list[str] = None

    def __post_init__(self):
        if self.error_messages is None:
            self.error_messages = []


class TagClassifier:
    """Classify tag names into categories."""

    # Tag category mappings
    POKER_PLAY_KEYWORDS = {
        "bluff", "블러프", "call", "콜", "raise", "레이즈", "fold", "폴드",
        "bet", "벳", "check", "체크", "allin", "올인", "hero", "히어로",
        "value", "밸류", "slow", "슬로우", "cooler", "쿨러", "suckout",
        "bad_beat", "배드비트", "river", "리버", "preflop", "프리플랍",
        "postflop", "포스트플랍", "3bet", "4bet", "squeeze",
    }

    EMOTION_KEYWORDS = {
        "stress", "긴장", "excite", "흥분", "relief", "안도", "pain", "고통",
        "laugh", "웃음", "frustrat", "좌절", "shock", "충격", "happy", "행복",
        "sad", "슬픔", "angry", "화남", "joy", "기쁨",
    }

    EPIC_HAND_KEYWORDS = {
        "royal", "로열", "quads", "포카드", "straight_flush", "스트레이트플러시",
        "full_house", "풀하우스", "flush", "플러시", "straight", "스트레이트",
        "trips", "트립스", "set", "셋", "aces", "에이스", "kings", "킹",
    }

    RUNOUT_KEYWORDS = {
        "runner", "러너", "backdoor", "백도어", "outer", "아우터",
        "river", "리버", "turn", "턴",
    }

    @classmethod
    def classify(cls, tag_name: str) -> str:
        """Classify a tag name into a category.

        Args:
            tag_name: Tag name to classify.

        Returns:
            TagCategory constant.
        """
        name_lower = tag_name.lower()

        # Check each category
        for keyword in cls.POKER_PLAY_KEYWORDS:
            if keyword in name_lower:
                return TagCategory.POKER_PLAY

        for keyword in cls.EMOTION_KEYWORDS:
            if keyword in name_lower:
                return TagCategory.EMOTION

        for keyword in cls.EPIC_HAND_KEYWORDS:
            if keyword in name_lower:
                return TagCategory.EPIC_HAND

        for keyword in cls.RUNOUT_KEYWORDS:
            if keyword in name_lower:
                return TagCategory.RUNOUT

        # Default to adjective if no match
        return TagCategory.ADJECTIVE


class PlayerMatcher:
    """Normalize and match player names."""

    # Known player name variations
    NAME_NORMALIZATIONS = {
        "phil ivey": "Phil Ivey",
        "tom dwan": "Tom Dwan",
        "daniel negreanu": "Daniel Negreanu",
        "doyle brunson": "Doyle Brunson",
        "phil hellmuth": "Phil Hellmuth",
        "antonio esfandiari": "Antonio Esfandiari",
        "patrik antonius": "Patrik Antonius",
        "gus hansen": "Gus Hansen",
        "jason koon": "Jason Koon",
        "stephen chidwick": "Stephen Chidwick",
        "bryn kenney": "Bryn Kenney",
        "justin bonomo": "Justin Bonomo",
        "fedor holz": "Fedor Holz",
        "dan smith": "Dan Smith",
        "isaac haxton": "Isaac Haxton",
        "chris moneymaker": "Chris Moneymaker",
        "vanessa selbst": "Vanessa Selbst",
        "liv boeree": "Liv Boeree",
        "jason mercier": "Jason Mercier",
        "erik seidel": "Erik Seidel",
    }

    @classmethod
    def normalize_name(cls, name: str) -> str:
        """Normalize a player name.

        Args:
            name: Player name to normalize.

        Returns:
            Normalized name.
        """
        if not name:
            return name

        # Clean up whitespace
        name = " ".join(name.split())

        # Check known normalizations
        name_lower = name.lower()
        if name_lower in cls.NAME_NORMALIZATIONS:
            return cls.NAME_NORMALIZATIONS[name_lower]

        # Title case if not in known list
        return name.title()


class SheetsDataMapper:
    """Maps sheet rows to database entities and persists them."""

    def __init__(
        self,
        session: AsyncSession,
        hand_clip_service: Optional[HandClipService] = None,
        player_service: Optional[PlayerService] = None,
        tag_service: Optional[TagService] = None,
    ):
        self.session = session
        self.hand_clip_service = hand_clip_service or HandClipService(session)
        self.player_service = player_service or PlayerService(session)
        self.tag_service = tag_service or TagService(session)

        # Caches for performance
        self._player_cache: dict[str, Player] = {}
        self._tag_cache: dict[tuple[str, str], Tag] = {}

    async def get_or_create_player(self, name: str) -> Player:
        """Get or create a player with caching."""
        normalized = PlayerMatcher.normalize_name(name)

        if normalized in self._player_cache:
            return self._player_cache[normalized]

        player = await self.player_service.get_or_create(normalized)
        self._player_cache[normalized] = player
        return player

    async def get_or_create_tag(self, name: str) -> Tag:
        """Get or create a tag with automatic category classification."""
        category = TagClassifier.classify(name)
        cache_key = (category, name)

        if cache_key in self._tag_cache:
            return self._tag_cache[cache_key]

        tag = await self.tag_service.get_or_create(category, name)
        self._tag_cache[cache_key] = tag
        return tag

    async def map_and_save_archive_row(
        self,
        row: list,
        row_number: int,
        video_file_id: Optional[UUID] = None,
        episode_id: Optional[UUID] = None,
    ) -> Optional[HandClip]:
        """Map and save a METADATA_ARCHIVE row.

        Args:
            row: Sheet row data.
            row_number: Row number in sheet.
            video_file_id: Optional video file ID to link.
            episode_id: Optional episode ID to link.

        Returns:
            Created HandClip or None if skipped.
        """
        # Map row to data class
        mapped = RowMapper.map_archive_row(row, row_number)
        if mapped is None:
            return None

        # Check for existing clip by row number
        existing = await self.hand_clip_service.get_by_sheet_row(
            mapped.sheet_source, row_number
        )
        if existing:
            return existing  # Skip duplicates

        # Create hand clip
        clip = await self.hand_clip_service.create(
            title=mapped.title,
            sheet_source=mapped.sheet_source,
            sheet_row_number=row_number,
            timecode=mapped.timecode,
            timecode_end=mapped.timecode_end,
            duration_seconds=mapped.duration_seconds,
            hand_grade=mapped.hand_grade,
            pot_size=mapped.pot_size,
            winner_hand=mapped.winner_hand,
            hands_involved=mapped.hands_involved,
            notes=mapped.notes,
            video_file_id=video_file_id,
            episode_id=episode_id,
            nas_folder_link=mapped.nas_folder_link,  # PRD 15.3: NAS 매칭용
        )

        # Add players
        for player_name in mapped.player_names:
            player = await self.get_or_create_player(player_name)
            await self.hand_clip_service.add_player(clip.id, player.id)

        # Add tags
        for tag_name in mapped.tag_names:
            tag = await self.get_or_create_tag(tag_name)
            await self.hand_clip_service.add_tag(clip.id, tag.id)

        return clip

    async def map_and_save_iconik_row(
        self,
        row: list,
        row_number: int,
        video_file_id: Optional[UUID] = None,
        episode_id: Optional[UUID] = None,
    ) -> Optional[HandClip]:
        """Map and save an ICONIK_METADATA row.

        Args:
            row: Sheet row data.
            row_number: Row number in sheet.
            video_file_id: Optional video file ID to link.
            episode_id: Optional episode ID to link.

        Returns:
            Created HandClip or None if skipped.
        """
        # Map row to data class
        mapped = RowMapper.map_iconik_row(row, row_number)
        if mapped is None:
            return None

        # Check for existing clip by row number
        existing = await self.hand_clip_service.get_by_sheet_row(
            mapped.sheet_source, row_number
        )
        if existing:
            return existing  # Skip duplicates

        # Create hand clip
        clip = await self.hand_clip_service.create(
            title=mapped.title,
            sheet_source=mapped.sheet_source,
            sheet_row_number=row_number,
            timecode=mapped.timecode,
            duration_seconds=mapped.duration_seconds,
            notes=mapped.notes,
            video_file_id=video_file_id,
            episode_id=episode_id,
        )

        # Add players
        for player_name in mapped.player_names:
            player = await self.get_or_create_player(player_name)
            await self.hand_clip_service.add_player(clip.id, player.id)

        # Add tags
        for tag_name in mapped.tag_names:
            tag = await self.get_or_create_tag(tag_name)
            await self.hand_clip_service.add_tag(clip.id, tag.id)

        return clip

    async def sync_archive_rows(
        self,
        rows: list[list],
        start_row: int = 1,
    ) -> SyncResult:
        """Sync multiple METADATA_ARCHIVE rows.

        Args:
            rows: List of row data.
            start_row: Starting row number.

        Returns:
            SyncResult with statistics.
        """
        result = SyncResult(total_rows=len(rows))

        for i, row in enumerate(rows):
            row_number = start_row + i
            try:
                clip = await self.map_and_save_archive_row(row, row_number)
                if clip:
                    if clip.sheet_row_number == row_number:
                        result.created += 1
                    else:
                        result.skipped += 1  # Duplicate
                else:
                    result.skipped += 1  # Invalid row
            except Exception as e:
                result.errors += 1
                result.error_messages.append(f"Row {row_number}: {str(e)}")

        return result

    async def sync_iconik_rows(
        self,
        rows: list[list],
        start_row: int = 1,
    ) -> SyncResult:
        """Sync multiple ICONIK_METADATA rows.

        Args:
            rows: List of row data.
            start_row: Starting row number.

        Returns:
            SyncResult with statistics.
        """
        result = SyncResult(total_rows=len(rows))

        for i, row in enumerate(rows):
            row_number = start_row + i
            try:
                clip = await self.map_and_save_iconik_row(row, row_number)
                if clip:
                    if clip.sheet_row_number == row_number:
                        result.created += 1
                    else:
                        result.skipped += 1  # Duplicate
                else:
                    result.skipped += 1  # Invalid row
            except Exception as e:
                result.errors += 1
                result.error_messages.append(f"Row {row_number}: {str(e)}")

        return result

    def clear_cache(self):
        """Clear internal caches."""
        self._player_cache.clear()
        self._tag_cache.clear()

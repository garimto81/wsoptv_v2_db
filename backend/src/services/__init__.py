"""Services Module.

Block A: File Parser Services
Block B: Catalog Services (CRUD)
Block C: Hand Analysis Services (CRUD)
Block D: Sheets Sync Services
"""

from .catalog import (
    EpisodeService,
    EventService,
    ProjectService,
    SeasonService,
)
from .file_parser import ParserFactory, ParsedMetadata
from .hand_analysis import (
    HandClipService,
    PlayerService,
    TagService,
)
from .sheets_sync import (
    SheetsClient,
    SheetsSyncService,
)

__all__ = [
    # Block B - Catalog
    "ProjectService",
    "SeasonService",
    "EventService",
    "EpisodeService",
    # Block A - File Parser
    "ParserFactory",
    "ParsedMetadata",
    # Block C - Hand Analysis
    "HandClipService",
    "TagService",
    "PlayerService",
    # Block D - Sheets Sync
    "SheetsClient",
    "SheetsSyncService",
]

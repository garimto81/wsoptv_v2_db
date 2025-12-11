"""Matching Service Module - PRD 15.3 NAS ↔ Sheets 매칭.

경로와 제목 기반의 NAS ↔ Sheets 데이터 매칭을 제공합니다.
"""

from .path_matcher import (
    MatchResult,
    MatchStats,
    PathMatcher,
    PathNormalizer,
    TitleMatcher,
)

__all__ = [
    "MatchResult",
    "MatchStats",
    "PathMatcher",
    "PathNormalizer",
    "TitleMatcher",
]

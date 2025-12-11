"""PathMatcher 단위 테스트."""

import pytest

from src.services.matching import PathNormalizer, TitleMatcher


class TestPathNormalizer:
    """PathNormalizer 테스트 클래스."""

    def test_unc_prefix_removal(self):
        """UNC 프리픽스 제거 테스트."""
        path = r"\\10.10.100.122\docker\wsop\2024\video.mp4"
        normalized = PathNormalizer.normalize(path)

        assert "10.10.100.122" not in normalized
        assert "docker" not in normalized

    def test_backslash_to_slash(self):
        """백슬래시 → 슬래시 변환 테스트."""
        path = r"wsop\2024\video.mp4"
        normalized = PathNormalizer.normalize(path)

        assert "\\" not in normalized
        assert "/" in normalized or "wsop" in normalized

    def test_lowercase_conversion(self):
        """소문자 변환 테스트."""
        path = "WSOP/2024/VIDEO.MP4"
        normalized = PathNormalizer.normalize(path)

        assert normalized == normalized.lower()

    def test_double_slash_cleanup(self):
        """연속 슬래시 정리 테스트."""
        path = "wsop//2024///video.mp4"
        normalized = PathNormalizer.normalize(path)

        assert "//" not in normalized

    def test_trailing_slash_removal(self):
        """끝 슬래시 제거 테스트."""
        path = "wsop/2024/"
        normalized = PathNormalizer.normalize(path)

        assert not normalized.endswith("/")

    def test_empty_path(self):
        """빈 경로 테스트."""
        assert PathNormalizer.normalize("") == ""
        assert PathNormalizer.normalize(None) == ""

    def test_smb_prefix_removal(self):
        """SMB 프리픽스 제거 테스트."""
        path = "smb://server/share/wsop/video.mp4"
        normalized = PathNormalizer.normalize(path)

        assert "smb://" not in normalized

    def test_extract_folder_path(self):
        """폴더 경로 추출 테스트."""
        file_path = r"\\server\share\wsop\2024\video.mp4"
        folder = PathNormalizer.extract_folder_path(file_path)

        assert "video.mp4" not in folder
        assert "2024" in folder or "wsop" in folder

    def test_extract_filename(self):
        """파일명 추출 테스트."""
        file_path = r"\\server\share\wsop\2024\video.mp4"
        filename = PathNormalizer.extract_filename(file_path)

        assert filename == "video.mp4"


class TestTitleMatcher:
    """TitleMatcher 테스트 클래스."""

    def test_normalize_title_lowercase(self):
        """제목 정규화 - 소문자 변환."""
        title = "WSOP Main Event 2024"
        normalized = TitleMatcher.normalize_title(title)

        assert normalized == normalized.lower()

    def test_normalize_title_special_chars(self):
        """제목 정규화 - 특수문자 제거."""
        title = "WSOP Main Event - Day 3 (Final)"
        normalized = TitleMatcher.normalize_title(title)

        assert "-" not in normalized
        assert "(" not in normalized
        assert ")" not in normalized

    def test_normalize_title_whitespace(self):
        """제목 정규화 - 공백 정리."""
        title = "WSOP   Main   Event"
        normalized = TitleMatcher.normalize_title(title)

        assert "   " not in normalized

    def test_exact_match_similarity(self):
        """완전 일치 유사도 테스트."""
        similarity = TitleMatcher.calculate_similarity(
            "WSOP Main Event",
            "WSOP Main Event"
        )

        assert similarity == 1.0

    def test_partial_match_similarity(self):
        """부분 일치 유사도 테스트."""
        similarity = TitleMatcher.calculate_similarity(
            "WSOP Main Event 2024",
            "WSOP Main Event"
        )

        assert similarity > 0.5
        assert similarity < 1.0

    def test_no_match_similarity(self):
        """불일치 유사도 테스트."""
        similarity = TitleMatcher.calculate_similarity(
            "WSOP Main Event",
            "GG Millions Manila"
        )

        assert similarity < 0.5

    def test_empty_title_similarity(self):
        """빈 제목 유사도 테스트."""
        assert TitleMatcher.calculate_similarity("", "WSOP") == 0.0
        assert TitleMatcher.calculate_similarity("WSOP", "") == 0.0
        assert TitleMatcher.calculate_similarity("", "") == 0.0

    def test_substring_similarity(self):
        """부분 문자열 유사도 테스트."""
        # One title contains the other
        similarity = TitleMatcher.calculate_similarity(
            "WSOP",
            "WSOP 2024 Main Event Day 3"
        )

        assert similarity > 0.0

    def test_word_based_similarity(self):
        """단어 기반 유사도 테스트."""
        # Same words, different order
        similarity = TitleMatcher.calculate_similarity(
            "Main Event WSOP 2024",
            "WSOP 2024 Main Event"
        )

        assert similarity == 1.0  # Same normalized words

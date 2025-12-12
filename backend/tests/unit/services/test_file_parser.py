"""Tests for File Parser - Block A (NAS Inventory Agent).

TDD: RED -> GREEN -> REFACTOR

이 테스트는 PRD Section 7.2의 패턴 정의를 기반으로 작성됨.
"""

import pytest
from src.services.file_parser import ParserFactory, ParsedMetadata
from src.services.file_parser.wsop_parser import (
    WSOPBraceletParser,
    WSOPCircuitParser,
    WSOPArchiveParser,
)
from src.services.file_parser.other_parsers import (
    GGMillionsParser,
    GOGParser,
    PADParser,
    MPPParser,
    GenericParser,
)
from src.services.file_parser.parser_factory import should_hide_file


class TestWSOPBraceletParser:
    """Test cases for WSOP Bracelet Parser.

    PRD Pattern: ^(\d+)-wsop-(\d{4})-be-ev-(\d+)-(\d+k?)-([a-z0-9]+)-(.+)\.(mp4|mov|mxf)$
    예시: 10-wsop-2024-be-ev-21-25k-nlh-hr-ft-schutten-reclaims-chip-lead.mp4
    """

    def test_parse_standard_filename(self):
        """Test parsing standard WSOP bracelet filename (PRD 7.2)."""
        parser = WSOPBraceletParser()
        # PRD 패턴에 맞는 파일명
        filename = "10-wsop-2024-be-ev-21-25k-nlh-hr-ft-schutten-reclaims-chip-lead.mp4"

        result = parser.parse(filename, "")

        assert result is not None
        assert result.project_code == "WSOP"
        assert result.year == 2024
        assert result.event_number == 21
        assert result.clip_number == 10
        assert result.buy_in == "25K"
        assert result.game_type == "NLHE"  # nlh → NLHE로 정규화됨
        assert result.parse_success is True

    def test_parse_with_different_game_types(self):
        """Test parsing filenames with different game types."""
        parser = WSOPBraceletParser()

        nlh = parser.parse("01-wsop-2024-be-ev-01-10k-nlhe-ft-day1.mp4", "")
        plo = parser.parse("02-wsop-2024-be-ev-02-1500-plo-day1-recap.mp4", "")

        assert nlh.game_type == "NLHE"
        assert plo.game_type == "PLO"

    def test_parse_invalid_filename(self):
        """Test parsing invalid filename returns parse_success=False."""
        parser = WSOPBraceletParser()

        result = parser.parse("random_video.mp4", "")

        assert result.parse_success is False

    def test_parse_final_table_indicator(self):
        """Test parsing final table indicator from filename."""
        parser = WSOPBraceletParser()
        filename = "05-wsop-2024-be-ev-15-50k-nlh-ft-final-showdown.mp4"

        result = parser.parse(filename, "")

        assert result.table_type == "final_table"


class TestWSOPCircuitParser:
    """Test cases for WSOP Circuit Parser.

    PRD Pattern: ^WCLA(\d{2})-(\d+)\.(mp4|mov)$
    예시: WCLA24-15.mp4
    """

    def test_parse_circuit_filename(self):
        """Test parsing WSOP Circuit filename (PRD 7.2)."""
        parser = WSOPCircuitParser()
        filename = "WCLA24-15.mp4"

        result = parser.parse(filename, "")

        assert result is not None
        assert result.project_code == "WSOP"
        assert result.year == 2024
        assert result.clip_number == 15
        assert result.extra.get("sub_category") == "CIRCUIT"
        assert result.parse_success is True

    def test_parse_circuit_different_years(self):
        """Test parsing Circuit files from different years."""
        parser = WSOPCircuitParser()

        result_23 = parser.parse("WCLA23-01.mp4", "")
        result_25 = parser.parse("WCLA25-99.mov", "")

        assert result_23.year == 2023
        assert result_25.year == 2025


class TestWSOPArchiveParser:
    """Test cases for WSOP Archive Parser.

    PRD Pattern: wsop-{연도}-me-{버전}.mp4
    예시: wsop-1973-me-nobug.mp4
    """

    def test_parse_archive_filename(self):
        """Test parsing WSOP Archive filename (PRD 7.2)."""
        parser = WSOPArchiveParser()
        filename = "wsop-1973-me-nobug.mp4"

        result = parser.parse(filename, "")

        assert result is not None
        assert result.project_code == "WSOP"
        assert result.year == 1973
        assert result.extra.get("sub_category") == "ARCHIVE"
        assert result.parse_success is True

    def test_parse_archive_main_event(self):
        """Test parsing Main Event archive files."""
        parser = WSOPArchiveParser()

        result = parser.parse("wsop-2005-me.mp4", "")

        assert result.event_name == "Main Event"
        assert result.year == 2005


class TestGGMillionsParser:
    """Test cases for GG Millions Parser.

    PRD Pattern: ^(\d{6})?_?Super High Roller Poker FINAL TABLE with (.+)\.mp4$
    예시: 250507_Super High Roller Poker FINAL TABLE with Joey ingram.mp4
    """

    def test_parse_gg_millions_filename(self):
        """Test parsing GG Millions filename (PRD 7.2)."""
        parser = GGMillionsParser()
        filename = "250507_Super High Roller Poker FINAL TABLE with Joey Ingram.mp4"

        result = parser.parse(filename, "")

        assert result is not None
        assert result.project_code == "GGMILLIONS"
        assert result.featured_player == "Joey Ingram"
        assert result.year == 2025
        assert result.table_type == "final_table"
        assert result.parse_success is True

    def test_parse_gg_millions_without_date(self):
        """Test parsing GG Millions without date prefix."""
        parser = GGMillionsParser()
        filename = "Super High Roller Poker FINAL TABLE with Daniel Negreanu.mp4"

        result = parser.parse(filename, "")

        assert result.project_code == "GGMILLIONS"
        assert result.featured_player == "Daniel Negreanu"


class TestGOGParser:
    """Test cases for Game of Gold Parser.

    PRD Pattern: ^E(\d{1,3})_GOG_final_edit_(클린본_)?(\d{6})(?:_수정)?\.(mp4|mov)$
    예시: E01_GOG_final_edit_231106.mp4
    """

    def test_parse_gog_filename(self):
        """Test parsing Game of Gold filename (PRD 7.2)."""
        parser = GOGParser()
        filename = "E01_GOG_final_edit_231106.mp4"

        result = parser.parse(filename, "")

        assert result is not None
        assert result.project_code == "GOG"
        assert result.episode_number == 1
        assert result.year == 2023
        assert result.parse_success is True

    def test_parse_gog_clean_version(self):
        """Test parsing GOG clean version."""
        parser = GOGParser()
        filename = "E05_GOG_final_edit_클린본_240315.mp4"

        result = parser.parse(filename, "")

        assert result.version_type == "clean"
        assert result.episode_number == 5


class TestPADParser:
    """Test cases for Poker After Dark Parser.

    PRD Pattern: ^pad-s(\d+)-ep(\d+)-(\d+)\.mp4$
    예시: pad-s12-ep01-12345.mp4
    """

    def test_parse_pad_filename(self):
        """Test parsing Poker After Dark filename (PRD 7.2)."""
        parser = PADParser()
        filename = "pad-s12-ep01-12345.mp4"

        result = parser.parse(filename, "")

        assert result is not None
        assert result.project_code == "PAD"
        assert result.season_number == 12
        assert result.episode_number == 1
        assert result.parse_success is True

    def test_parse_pad_s13_format(self):
        """Test parsing PAD S13+ format."""
        parser = PADParser()
        filename = "PAD_S13_EP05.mp4"

        result = parser.parse(filename, "")

        assert result.project_code == "PAD"
        assert result.season_number == 13
        assert result.episode_number == 5


class TestMPPParser:
    """Test cases for MPP Parser.

    PRD Pattern: ^\$(\d+[MK]) GTD.*\? (.+)\.mp4$
    예시: $1M GTD   $1K PokerOK Mystery Bounty ? Day 1A.mp4
    """

    def test_parse_mpp_filename(self):
        """Test parsing MPP filename (PRD 7.2)."""
        parser = MPPParser()
        filename = "$1M GTD   $1K PokerOK Mystery Bounty ? Day 1A.mp4"

        result = parser.parse(filename, "")

        assert result is not None
        assert result.project_code == "MPP"
        assert result.gtd_amount == 1_000_000
        assert result.buy_in == "1K"
        assert result.day_info == "Day 1A"
        assert result.parse_success is True

    def test_parse_mpp_final_table(self):
        """Test parsing MPP final table."""
        parser = MPPParser()
        filename = "$500K GTD   $5K Main Event ? Final Table.mp4"

        result = parser.parse(filename, "")

        assert result.table_type == "final_table"


class TestGenericParser:
    """Test cases for Generic Parser."""

    def test_parse_any_filename(self):
        """Test generic parser accepts any filename."""
        parser = GenericParser()

        result = parser.parse("any_random_video.mp4", "")

        assert result is not None
        # Generic parser는 project_code를 경로에서 추론하므로 None일 수 있음
        assert result.parse_success is True

    def test_extract_year_from_filename(self):
        """Test extracting year from filename."""
        parser = GenericParser()

        result = parser.parse("Poker_2023_Final.mp4", "")

        assert result.year == 2023

    def test_infer_project_from_path(self):
        """Test inferring project code from file path."""
        parser = GenericParser()

        result = parser.parse("random.mp4", "/nas/WSOP/videos/random.mp4")

        assert result.project_code == "WSOP"


class TestParserFactory:
    """Test cases for ParserFactory."""

    def test_detect_wsop_bracelet(self):
        """Test detecting WSOP Bracelet project."""
        # PRD 패턴에 맞는 파일명 사용
        parser = ParserFactory.get_parser("01-wsop-2024-be-ev-01-10k-nlh-ft.mp4")

        assert isinstance(parser, WSOPBraceletParser)

    def test_detect_wsop_circuit(self):
        """Test detecting WSOP Circuit project."""
        parser = ParserFactory.get_parser("WCLA24-01.mp4")

        assert isinstance(parser, WSOPCircuitParser)

    def test_detect_ggmillions(self):
        """Test detecting GG Millions project."""
        parser = ParserFactory.get_parser(
            "250507_Super High Roller Poker FINAL TABLE with Phil Ivey.mp4"
        )

        assert isinstance(parser, GGMillionsParser)

    def test_detect_gog(self):
        """Test detecting Game of Gold project."""
        parser = ParserFactory.get_parser("E01_GOG_final_edit_231106.mp4")

        assert isinstance(parser, GOGParser)

    def test_fallback_to_generic(self):
        """Test fallback to generic parser."""
        parser = ParserFactory.get_parser("unknown_video.mp4")

        assert isinstance(parser, GenericParser)

    def test_parse_method(self):
        """Test factory parse method."""
        result = ParserFactory.parse("01-wsop-2024-be-ev-01-10k-nlh-ft.mp4")

        assert result is not None
        assert result.project_code == "WSOP"

    def test_should_hide_file_macos_metadata(self):
        """Test detecting macOS metadata files to hide."""
        hidden, reason = should_hide_file("._video.mp4")

        assert hidden is True
        assert reason == "macos_metadata"

    def test_should_hide_file_thumbs_db(self):
        """Test detecting Windows thumbnail files to hide."""
        hidden, reason = should_hide_file("Thumbs.db")

        assert hidden is True
        assert reason == "windows_thumbnail"

    def test_should_hide_file_ds_store(self):
        """Test detecting macOS .DS_Store files to hide."""
        hidden, reason = should_hide_file(".DS_Store")

        assert hidden is True
        assert reason == "macos_system"

    def test_should_not_hide_normal_file(self):
        """Test normal files are not hidden."""
        hidden, reason = should_hide_file("01-wsop-2024-be-ev-01-10k-nlh-ft.mp4")

        assert hidden is False
        assert reason is None


class TestParserConfidence:
    """Test cases for parser confidence values.

    Issue #1: All parsers should set confidence field appropriately.
    - Pattern match: confidence >= 0.7
    - Path inference: confidence 0.3~0.6
    - Parse failure: confidence < 0.3
    """

    def test_wsop_bracelet_confidence_on_match(self):
        """WSOP Bracelet: High confidence on pattern match."""
        parser = WSOPBraceletParser()
        filename = "10-wsop-2024-be-ev-21-25k-nlh-hr-ft.mp4"

        result = parser.parse(filename, "")

        assert result.confidence is not None
        assert result.confidence >= 0.9

    def test_wsop_circuit_confidence_on_match(self):
        """WSOP Circuit: High confidence on pattern match."""
        parser = WSOPCircuitParser()
        filename = "WCLA24-15.mp4"

        result = parser.parse(filename, "")

        assert result.confidence is not None
        assert result.confidence >= 0.85

    def test_wsop_archive_confidence_on_pattern_match(self):
        """WSOP Archive: High confidence on pattern match."""
        parser = WSOPArchiveParser()
        filename = "wsop-2015-me-nobug.mp4"

        result = parser.parse(filename, "")

        assert result.confidence is not None
        assert result.confidence >= 0.8

    def test_wsop_archive_confidence_on_path_inference(self):
        """WSOP Archive: Lower confidence on path-based inference."""
        parser = WSOPArchiveParser()
        filename = "random_video.mp4"
        path = "/ARCHIVE/WSOP/2010/random_video.mp4"

        result = parser.parse(filename, path)

        assert result.confidence is not None
        assert 0.2 <= result.confidence <= 0.5

    def test_ggmillions_confidence_on_match(self):
        """GG Millions: High confidence on pattern match."""
        parser = GGMillionsParser()
        filename = "250507_Super High Roller Poker FINAL TABLE with Phil Ivey.mp4"

        result = parser.parse(filename, "")

        assert result.confidence is not None
        assert result.confidence >= 0.85

    def test_ggmillions_confidence_on_no_match(self):
        """GG Millions: Low confidence when pattern doesn't match."""
        parser = GGMillionsParser()
        filename = "random_video.mp4"

        result = parser.parse(filename, "/GGMillions/random_video.mp4")

        assert result.confidence is not None
        assert result.confidence < 0.5

    def test_gog_confidence_on_8digit_match(self):
        """GOG: Highest confidence on 8-digit date pattern."""
        parser = GOGParser()
        filename = "E07_GOG_final_edit_20231121.mp4"

        result = parser.parse(filename, "")

        assert result.confidence is not None
        assert result.confidence >= 0.9

    def test_gog_confidence_on_6digit_match(self):
        """GOG: High confidence on 6-digit date pattern."""
        parser = GOGParser()
        filename = "E01_GOG_final_edit_231106.mp4"

        result = parser.parse(filename, "")

        assert result.confidence is not None
        assert result.confidence >= 0.85

    def test_pad_confidence_s12_pattern(self):
        """PAD: Highest confidence on S12 pattern."""
        parser = PADParser()
        filename = "pad-s12-ep01-12345.mp4"

        result = parser.parse(filename, "")

        assert result.confidence is not None
        assert result.confidence >= 0.9

    def test_pad_confidence_s13_pattern(self):
        """PAD: High confidence on S13 pattern."""
        parser = PADParser()
        filename = "PAD_S13_EP01_HD-12345.mp4"

        result = parser.parse(filename, "")

        assert result.confidence is not None
        assert result.confidence >= 0.85

    def test_mpp_confidence_on_match(self):
        """MPP: High confidence on pattern match."""
        parser = MPPParser()
        filename = "$1M GTD   $1K PokerOK Mystery Bounty ? Day 1A.mp4"

        result = parser.parse(filename, "")

        assert result.confidence is not None
        assert result.confidence >= 0.8

    def test_generic_confidence_with_project_and_year(self):
        """Generic: Medium-low confidence with project and year extracted."""
        parser = GenericParser()
        filename = "Poker_2023_Final.mp4"
        path = "/WSOP/videos/Poker_2023_Final.mp4"

        result = parser.parse(filename, path)

        assert result.confidence is not None
        assert 0.35 <= result.confidence <= 0.50

    def test_generic_confidence_without_info(self):
        """Generic: Low confidence with minimal info."""
        parser = GenericParser()
        filename = "random_video.mp4"

        result = parser.parse(filename, "")

        assert result.confidence is not None
        assert result.confidence <= 0.30

    def test_factory_parse_returns_confidence(self):
        """ParserFactory.parse() should return metadata with confidence."""
        result = ParserFactory.parse("01-wsop-2024-be-ev-01-10k-nlh-ft.mp4")

        assert result.confidence is not None
        assert result.confidence > 0

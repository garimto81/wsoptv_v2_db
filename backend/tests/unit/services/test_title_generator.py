"""TitleGenerator 단위 테스트."""

import pytest

from src.services.file_parser import TitleGenerator
from src.services.file_parser.base_parser import ParsedMetadata


class TestTitleGenerator:
    """TitleGenerator 테스트 클래스."""

    @pytest.fixture
    def generator(self) -> TitleGenerator:
        """TitleGenerator 인스턴스."""
        return TitleGenerator()

    def test_wsop_bracelet_title(self, generator: TitleGenerator):
        """WSOP Bracelet 제목 생성 테스트."""
        metadata = ParsedMetadata(
            project_code="WSOP_BRACELET",
            year=2024,
            event_number=55,
            event_name="Main Event",
            day_number=7,
            episode_type="Day",
        )
        display, catalog = generator.generate(metadata)

        assert "WSOP" in display
        assert "2024" in display
        assert "WSOP" in catalog

    def test_wsop_circuit_title(self, generator: TitleGenerator):
        """WSOP Circuit 제목 생성 테스트."""
        metadata = ParsedMetadata(
            project_code="WSOP_CIRCUIT",
            year=2024,
            venue="Las Vegas",
            clip_number=26,
        )
        display, catalog = generator.generate(metadata)

        assert "Circuit" in display or "WSOP-C" in catalog
        assert "2024" in display

    def test_pad_title(self, generator: TitleGenerator):
        """Poker After Dark 제목 생성 테스트."""
        metadata = ParsedMetadata(
            project_code="PAD",
            year=2023,
            season_number=12,
            episode_number=5,
        )
        display, catalog = generator.generate(metadata)

        assert "Poker After Dark" in display or "PAD" in display
        assert "PAD" in catalog or "S12" in catalog

    def test_gog_title(self, generator: TitleGenerator):
        """Game of Gold 제목 생성 테스트."""
        metadata = ParsedMetadata(
            project_code="GOG",
            year=2024,
            season_number=2,
            episode_number=8,
        )
        display, catalog = generator.generate(metadata)

        assert "Gold" in display or "GOG" in display

    def test_ggmillions_title(self, generator: TitleGenerator):
        """GG Millions 제목 생성 테스트."""
        metadata = ParsedMetadata(
            project_code="GGMILLIONS",
            year=2024,
            venue="Manila",
            event_number=3,
        )
        display, catalog = generator.generate(metadata)

        assert "GG" in display or "Millions" in display

    def test_generic_title(self, generator: TitleGenerator):
        """Generic 제목 생성 테스트."""
        metadata = ParsedMetadata(
            project_code="UNKNOWN",
            year=2024,
            display_title="Random Poker Video",
        )
        display, catalog = generator.generate(metadata)

        # Should return something, not empty
        assert display
        assert catalog

    def test_year_abbreviation(self, generator: TitleGenerator):
        """연도 축약 테스트."""
        metadata = ParsedMetadata(
            project_code="WSOP",
            year=2024,
        )
        display, catalog = generator.generate(metadata)

        # catalog_title should have abbreviated year
        assert "'24" in catalog or "24" in catalog

    def test_missing_year(self, generator: TitleGenerator):
        """연도 없는 경우 테스트."""
        metadata = ParsedMetadata(
            project_code="WSOP",
            year=None,
        )
        display, catalog = generator.generate(metadata)

        # Should still generate titles
        assert display
        assert catalog

    def test_event_info_in_display(self, generator: TitleGenerator):
        """display_title에 이벤트 정보 포함 테스트."""
        metadata = ParsedMetadata(
            project_code="WSOP_BRACELET",
            year=2024,
            event_number=55,
            event_name="Main Event",
            day_number=3,
            table_type="Final Table",
        )
        display, catalog = generator.generate(metadata)

        # display_title should be more detailed
        assert len(display) >= len(catalog)

    def test_returns_tuple(self, generator: TitleGenerator):
        """반환값이 tuple인지 테스트."""
        metadata = ParsedMetadata(project_code="WSOP", year=2024)
        result = generator.generate(metadata)

        assert isinstance(result, tuple)
        assert len(result) == 2
        assert isinstance(result[0], str)
        assert isinstance(result[1], str)

"""Tests for NAS Inventory Services - Block A (NAS Inventory Agent).

TDD: RED -> GREEN -> REFACTOR
"""

import pytest
import pytest_asyncio
from uuid import uuid4

from src.services.nas_inventory import NASFolderService, NASFileService
from src.models.nas_file import FileCategory


class TestNASFolderService:
    """Test cases for NASFolderService."""

    @pytest_asyncio.fixture
    async def service(self, async_session):
        """Create NASFolderService instance."""
        return NASFolderService(async_session)

    # ==================== 생성 테스트 ====================

    async def test_create_folder(self, service):
        """Test creating a new folder."""
        folder = await service.create_folder(
            folder_path="/nas/wsop/2024",
            folder_name="2024",
            parent_path="/nas/wsop",
            depth=2,
        )

        assert folder is not None
        assert folder.folder_path == "/nas/wsop/2024"
        assert folder.folder_name == "2024"
        assert folder.parent_path == "/nas/wsop"
        assert folder.depth == 2
        assert folder.is_empty is True
        assert folder.file_count == 0

    async def test_create_root_folder(self, service):
        """Test creating a root folder."""
        folder = await service.create_folder(
            folder_path="/nas",
            folder_name="nas",
            depth=0,
        )

        assert folder.depth == 0
        assert folder.parent_path is None

    async def test_create_hidden_folder(self, service):
        """Test creating a hidden folder."""
        folder = await service.create_folder(
            folder_path="/nas/.hidden",
            folder_name=".hidden",
            is_hidden_folder=True,
        )

        assert folder.is_hidden_folder is True

    # ==================== 조회 테스트 ====================

    async def test_get_by_path(self, service):
        """Test getting folder by path."""
        created = await service.create_folder(
            folder_path="/nas/test",
            folder_name="test",
        )

        found = await service.get_by_path("/nas/test")

        assert found is not None
        assert found.id == created.id

    async def test_get_by_path_not_found(self, service):
        """Test getting non-existent folder."""
        found = await service.get_by_path("/nonexistent")

        assert found is None

    async def test_get_root_folders(self, service):
        """Test getting root folders."""
        await service.create_folder(
            folder_path="/nas1",
            folder_name="nas1",
            depth=0,
        )
        await service.create_folder(
            folder_path="/nas2",
            folder_name="nas2",
            depth=0,
        )
        await service.create_folder(
            folder_path="/nas1/child",
            folder_name="child",
            parent_path="/nas1",
            depth=1,
        )

        roots = await service.get_root_folders()

        assert len(roots) == 2
        assert all(f.depth == 0 for f in roots)

    async def test_get_by_parent(self, service):
        """Test getting folders by parent path."""
        await service.create_folder(
            folder_path="/nas",
            folder_name="nas",
            depth=0,
        )
        await service.create_folder(
            folder_path="/nas/child1",
            folder_name="child1",
            parent_path="/nas",
            depth=1,
        )
        await service.create_folder(
            folder_path="/nas/child2",
            folder_name="child2",
            parent_path="/nas",
            depth=1,
        )

        children = await service.get_by_parent("/nas")

        assert len(children) == 2

    async def test_get_children(self, service):
        """Test getting children of a folder."""
        parent = await service.create_folder(
            folder_path="/nas",
            folder_name="nas",
            depth=0,
        )
        await service.create_folder(
            folder_path="/nas/child1",
            folder_name="child1",
            parent_path="/nas",
            depth=1,
        )

        children = await service.get_children(parent.id)

        assert len(children) == 1

    # ==================== 수정 테스트 ====================

    async def test_update_stats(self, service):
        """Test updating folder statistics."""
        folder = await service.create_folder(
            folder_path="/nas/test",
            folder_name="test",
        )

        updated = await service.update_stats(
            folder.id,
            file_count=10,
            folder_count=3,
            total_size_bytes=1_000_000,
        )

        assert updated is not None
        assert updated.file_count == 10
        assert updated.folder_count == 3
        assert updated.total_size_bytes == 1_000_000
        assert updated.is_empty is False

    async def test_increment_file_count(self, service):
        """Test incrementing file count."""
        folder = await service.create_folder(
            folder_path="/nas/test",
            folder_name="test",
        )

        updated = await service.increment_file_count(
            folder.id,
            count=5,
            size_bytes=500_000,
        )

        assert updated.file_count == 5
        assert updated.total_size_bytes == 500_000

    async def test_mark_hidden(self, service):
        """Test marking folder as hidden."""
        folder = await service.create_folder(
            folder_path="/nas/test",
            folder_name="test",
        )

        updated = await service.mark_hidden(folder.id, is_hidden=True)

        assert updated.is_hidden_folder is True

    # ==================== 검색/필터 테스트 ====================

    async def test_get_empty_folders(self, service):
        """Test getting empty folders."""
        await service.create_folder(
            folder_path="/nas/empty",
            folder_name="empty",
        )
        non_empty = await service.create_folder(
            folder_path="/nas/notempty",
            folder_name="notempty",
        )
        await service.update_stats(
            non_empty.id,
            file_count=1,
            folder_count=0,
            total_size_bytes=100,
        )

        empty_folders = await service.get_empty_folders()

        assert len(empty_folders) == 1
        assert empty_folders[0].folder_path == "/nas/empty"

    async def test_get_hidden_folders(self, service):
        """Test getting hidden folders."""
        await service.create_folder(
            folder_path="/nas/visible",
            folder_name="visible",
        )
        await service.create_folder(
            folder_path="/nas/.hidden",
            folder_name=".hidden",
            is_hidden_folder=True,
        )

        hidden = await service.get_hidden_folders()

        assert len(hidden) == 1
        assert hidden[0].is_hidden_folder is True

    async def test_search_by_path(self, service):
        """Test searching folders by path."""
        await service.create_folder(
            folder_path="/nas/wsop/2024",
            folder_name="2024",
        )
        await service.create_folder(
            folder_path="/nas/other",
            folder_name="other",
        )

        results = await service.search_by_path("wsop")

        assert len(results) == 1
        assert "wsop" in results[0].folder_path

    async def test_get_or_create_existing(self, service):
        """Test get_or_create returns existing folder."""
        original = await service.create_folder(
            folder_path="/nas/test",
            folder_name="test",
        )

        folder, created = await service.get_or_create(
            folder_path="/nas/test",
            folder_name="test",
        )

        assert created is False
        assert folder.id == original.id

    async def test_get_or_create_new(self, service):
        """Test get_or_create creates new folder."""
        folder, created = await service.get_or_create(
            folder_path="/nas/new",
            folder_name="new",
        )

        assert created is True
        assert folder.folder_path == "/nas/new"


class TestNASFileService:
    """Test cases for NASFileService."""

    @pytest_asyncio.fixture
    async def service(self, async_session):
        """Create NASFileService instance."""
        return NASFileService(async_session)

    @pytest_asyncio.fixture
    async def folder_service(self, async_session):
        """Create NASFolderService instance."""
        return NASFolderService(async_session)

    # ==================== 생성 테스트 ====================

    async def test_create_file(self, service):
        """Test creating a new file."""
        file = await service.create_file(
            file_path="/nas/wsop/video.mp4",
            file_name="video.mp4",
            file_size_bytes=1_000_000_000,
            file_extension=".mp4",
            file_category=FileCategory.VIDEO,
        )

        assert file is not None
        assert file.file_path == "/nas/wsop/video.mp4"
        assert file.file_name == "video.mp4"
        assert file.file_size_bytes == 1_000_000_000
        assert file.file_extension == ".mp4"
        assert file.file_category == FileCategory.VIDEO

    async def test_create_file_with_folder(self, service, folder_service):
        """Test creating a file with folder reference."""
        folder = await folder_service.create_folder(
            folder_path="/nas/wsop",
            folder_name="wsop",
        )

        file = await service.create_file(
            file_path="/nas/wsop/video.mp4",
            file_name="video.mp4",
            folder_id=folder.id,
        )

        assert file.folder_id == folder.id

    async def test_create_hidden_file(self, service):
        """Test creating a hidden file."""
        file = await service.create_file(
            file_path="/nas/._metadata",
            file_name="._metadata",
            is_hidden_file=True,
        )

        assert file.is_hidden_file is True

    # ==================== 조회 테스트 ====================

    async def test_get_by_path(self, service):
        """Test getting file by path."""
        created = await service.create_file(
            file_path="/nas/test.mp4",
            file_name="test.mp4",
        )

        found = await service.get_by_path("/nas/test.mp4")

        assert found is not None
        assert found.id == created.id

    async def test_get_by_path_not_found(self, service):
        """Test getting non-existent file."""
        found = await service.get_by_path("/nonexistent")

        assert found is None

    async def test_get_by_folder(self, service, folder_service):
        """Test getting files by folder."""
        folder = await folder_service.create_folder(
            folder_path="/nas/wsop",
            folder_name="wsop",
        )
        await service.create_file(
            file_path="/nas/wsop/video1.mp4",
            file_name="video1.mp4",
            folder_id=folder.id,
        )
        await service.create_file(
            file_path="/nas/wsop/video2.mp4",
            file_name="video2.mp4",
            folder_id=folder.id,
        )

        files = await service.get_by_folder(folder.id)

        assert len(files) == 2

    async def test_get_by_category(self, service):
        """Test getting files by category."""
        await service.create_file(
            file_path="/nas/video.mp4",
            file_name="video.mp4",
            file_category=FileCategory.VIDEO,
        )
        await service.create_file(
            file_path="/nas/data.xml",
            file_name="data.xml",
            file_category=FileCategory.METADATA,
        )

        videos = await service.get_by_category(FileCategory.VIDEO)

        assert len(videos) == 1
        assert videos[0].file_category == FileCategory.VIDEO

    async def test_get_by_extension(self, service):
        """Test getting files by extension."""
        await service.create_file(
            file_path="/nas/video1.mp4",
            file_name="video1.mp4",
            file_extension=".mp4",
        )
        await service.create_file(
            file_path="/nas/video2.mov",
            file_name="video2.mov",
            file_extension=".mov",
        )

        mp4_files = await service.get_by_extension("mp4")

        assert len(mp4_files) == 1
        assert mp4_files[0].file_extension == ".mp4"

    async def test_get_video_files(self, service):
        """Test getting video files."""
        await service.create_file(
            file_path="/nas/video.mp4",
            file_name="video.mp4",
            file_category=FileCategory.VIDEO,
        )
        await service.create_file(
            file_path="/nas/system.db",
            file_name="system.db",
            file_category=FileCategory.SYSTEM,
        )

        videos = await service.get_video_files()

        assert len(videos) == 1

    # ==================== 수정 테스트 ====================

    async def test_update_metadata(self, service):
        """Test updating file metadata."""
        from datetime import datetime, timezone

        file = await service.create_file(
            file_path="/nas/test.mp4",
            file_name="test.mp4",
        )

        mtime = datetime.now(timezone.utc)
        updated = await service.update_metadata(
            file.id,
            file_size_bytes=2_000_000_000,
            file_mtime=mtime,
        )

        assert updated.file_size_bytes == 2_000_000_000
        assert updated.file_mtime is not None

    async def test_set_category(self, service):
        """Test setting file category."""
        file = await service.create_file(
            file_path="/nas/test.mp4",
            file_name="test.mp4",
            file_category=FileCategory.OTHER,
        )

        updated = await service.set_category(file.id, FileCategory.VIDEO)

        assert updated.file_category == FileCategory.VIDEO

    async def test_mark_hidden(self, service):
        """Test marking file as hidden."""
        file = await service.create_file(
            file_path="/nas/test.mp4",
            file_name="test.mp4",
        )

        updated = await service.mark_hidden(file.id, is_hidden=True)

        assert updated.is_hidden_file is True

    async def test_link_to_video(self, service):
        """Test linking file to video."""
        file = await service.create_file(
            file_path="/nas/test.mp4",
            file_name="test.mp4",
        )
        video_id = uuid4()

        updated = await service.link_to_video(file.id, video_id)

        assert updated.video_file_id == video_id

    async def test_unlink_video(self, service):
        """Test unlinking file from video."""
        video_id = uuid4()
        file = await service.create_file(
            file_path="/nas/test.mp4",
            file_name="test.mp4",
        )
        await service.link_to_video(file.id, video_id)

        updated = await service.unlink_video(file.id)

        assert updated.video_file_id is None

    # ==================== 검색/필터 테스트 ====================

    async def test_get_hidden_files(self, service):
        """Test getting hidden files."""
        await service.create_file(
            file_path="/nas/visible.mp4",
            file_name="visible.mp4",
        )
        await service.create_file(
            file_path="/nas/._hidden",
            file_name="._hidden",
            is_hidden_file=True,
        )

        hidden = await service.get_hidden_files()

        assert len(hidden) == 1
        assert hidden[0].is_hidden_file is True

    async def test_get_unlinked_videos(self, service):
        """Test getting unlinked video files."""
        await service.create_file(
            file_path="/nas/unlinked.mp4",
            file_name="unlinked.mp4",
            file_category=FileCategory.VIDEO,
        )
        linked = await service.create_file(
            file_path="/nas/linked.mp4",
            file_name="linked.mp4",
            file_category=FileCategory.VIDEO,
        )
        await service.link_to_video(linked.id, uuid4())

        unlinked = await service.get_unlinked_videos()

        assert len(unlinked) == 1
        assert unlinked[0].file_name == "unlinked.mp4"

    async def test_search_by_name(self, service):
        """Test searching files by name."""
        await service.create_file(
            file_path="/nas/wsop_2024_e01.mp4",
            file_name="wsop_2024_e01.mp4",
        )
        await service.create_file(
            file_path="/nas/other.mp4",
            file_name="other.mp4",
        )

        results = await service.search_by_name("wsop")

        assert len(results) == 1
        assert "wsop" in results[0].file_name

    async def test_get_large_files(self, service):
        """Test getting large files."""
        await service.create_file(
            file_path="/nas/small.mp4",
            file_name="small.mp4",
            file_size_bytes=1_000_000,
        )
        await service.create_file(
            file_path="/nas/large.mp4",
            file_name="large.mp4",
            file_size_bytes=10_000_000_000,
        )

        large = await service.get_large_files(min_size_bytes=1_000_000_000)

        assert len(large) == 1
        assert large[0].file_name == "large.mp4"

    async def test_get_or_create_existing(self, service):
        """Test get_or_create returns existing file."""
        original = await service.create_file(
            file_path="/nas/test.mp4",
            file_name="test.mp4",
        )

        file, created = await service.get_or_create(
            file_path="/nas/test.mp4",
            file_name="test.mp4",
        )

        assert created is False
        assert file.id == original.id

    async def test_get_or_create_new(self, service):
        """Test get_or_create creates new file."""
        file, created = await service.get_or_create(
            file_path="/nas/new.mp4",
            file_name="new.mp4",
        )

        assert created is True
        assert file.file_path == "/nas/new.mp4"

    # ==================== 통계 테스트 ====================

    async def test_count_by_category(self, service):
        """Test counting files by category."""
        await service.create_file(
            file_path="/nas/video1.mp4",
            file_name="video1.mp4",
            file_category=FileCategory.VIDEO,
        )
        await service.create_file(
            file_path="/nas/video2.mp4",
            file_name="video2.mp4",
            file_category=FileCategory.VIDEO,
        )
        await service.create_file(
            file_path="/nas/meta.xml",
            file_name="meta.xml",
            file_category=FileCategory.METADATA,
        )

        counts = await service.count_by_category()

        assert counts.get(FileCategory.VIDEO) == 2
        assert counts.get(FileCategory.METADATA) == 1

    async def test_total_size_bytes(self, service):
        """Test getting total size."""
        await service.create_file(
            file_path="/nas/file1.mp4",
            file_name="file1.mp4",
            file_size_bytes=1_000_000,
        )
        await service.create_file(
            file_path="/nas/file2.mp4",
            file_name="file2.mp4",
            file_size_bytes=2_000_000,
        )

        total = await service.total_size_bytes()

        assert total == 3_000_000

"""NAS Inventory API - Block A (NAS Inventory Agent).

REST API endpoints for NAS folder and file inventory management.
"""

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, BackgroundTasks

from .deps import NASFolderServiceDep, NASFileServiceDep, DBSessionDep
from pydantic import BaseModel

from .schemas import (
    NASFolderCreate,
    NASFolderUpdate,
    NASFolderResponse,
    NASFolderStatsResponse,
    NASFileCreate,
    NASFileUpdate,
    NASFileResponse,
    NASFileStatsResponse,
)
from ...services.file_parser import ParserFactory
from ...services.nas_inventory import NASSyncService, SMBScanner

router = APIRouter(prefix="/nas", tags=["nas"])


# ==================== Response Schemas ====================


class ParserStatItem(BaseModel):
    """Parser statistics item."""

    parser_name: str
    matched_count: int
    percentage: float


class ParserStatsResponse(BaseModel):
    """Parser statistics response."""

    total_files: int
    parsed_files: int
    unparsed_files: int
    parse_rate: float
    by_parser: list[ParserStatItem]


class DuplicateFileGroup(BaseModel):
    """Group of potential duplicate files."""

    base_name: str
    file_count: int
    total_size_bytes: int
    files: list[NASFileResponse]


class DuplicatesResponse(BaseModel):
    """Duplicate files response."""

    total_groups: int
    total_duplicate_files: int
    groups: list[DuplicateFileGroup]


# ==================== NAS Folders ====================

@router.get("/folders", response_model=list[NASFolderResponse])
async def list_folders(
    service: NASFolderServiceDep,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    depth: Optional[int] = Query(None, ge=0),
):
    """List NAS folders with optional depth filter."""
    if depth is not None:
        return await service.get_by_depth(depth, skip=skip, limit=limit)
    return await service.get_all(skip=skip, limit=limit)


@router.get("/folders/root", response_model=list[NASFolderResponse])
async def list_root_folders(service: NASFolderServiceDep):
    """List root level folders (depth=0)."""
    return await service.get_root_folders()


@router.get("/folders/empty", response_model=list[NASFolderResponse])
async def list_empty_folders(
    service: NASFolderServiceDep,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
):
    """List empty folders."""
    return await service.get_empty_folders(skip=skip, limit=limit)


@router.get("/folders/hidden", response_model=list[NASFolderResponse])
async def list_hidden_folders(
    service: NASFolderServiceDep,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
):
    """List hidden folders."""
    return await service.get_hidden_folders(skip=skip, limit=limit)


@router.get("/folders/largest", response_model=list[NASFolderResponse])
async def list_largest_folders(
    service: NASFolderServiceDep,
    limit: int = Query(10, ge=1, le=100),
):
    """List folders by size (largest first)."""
    return await service.get_largest_folders(limit=limit)


@router.get("/folders/search", response_model=list[NASFolderResponse])
async def search_folders(
    service: NASFolderServiceDep,
    q: str = Query(..., min_length=1),
    limit: int = Query(50, ge=1, le=200),
):
    """Search folders by path."""
    return await service.search_by_path(q, limit=limit)


@router.get("/folders/{folder_id}", response_model=NASFolderResponse)
async def get_folder(service: NASFolderServiceDep, folder_id: UUID):
    """Get folder by ID."""
    folder = await service.get_by_id(folder_id)
    if folder is None:
        raise HTTPException(status_code=404, detail="Folder not found")
    return folder


@router.get("/folders/{folder_id}/children", response_model=list[NASFolderResponse])
async def get_folder_children(service: NASFolderServiceDep, folder_id: UUID):
    """Get direct child folders."""
    return await service.get_children(folder_id)


@router.get("/folders/{folder_id}/files", response_model=list[NASFileResponse])
async def get_folder_files(
    service: NASFolderServiceDep,
    file_service: NASFileServiceDep,
    folder_id: UUID,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
):
    """Get files in folder."""
    folder = await service.get_by_id(folder_id)
    if folder is None:
        raise HTTPException(status_code=404, detail="Folder not found")
    return await file_service.get_by_folder(folder_id, skip=skip, limit=limit)


@router.post("/folders", response_model=NASFolderResponse, status_code=201)
async def create_folder(service: NASFolderServiceDep, data: NASFolderCreate):
    """Create a new folder entry."""
    existing = await service.get_by_path(data.folder_path)
    if existing:
        raise HTTPException(status_code=409, detail="Folder path already exists")
    return await service.create_folder(
        folder_path=data.folder_path,
        folder_name=data.folder_name,
        parent_path=data.parent_path,
        depth=data.depth,
        is_hidden_folder=data.is_hidden_folder,
    )


@router.patch("/folders/{folder_id}", response_model=NASFolderResponse)
async def update_folder(
    service: NASFolderServiceDep,
    folder_id: UUID,
    data: NASFolderUpdate,
):
    """Update folder metadata."""
    update_data = data.model_dump(exclude_unset=True)
    if not update_data:
        raise HTTPException(status_code=400, detail="No fields to update")

    # Handle stats update separately
    if any(k in update_data for k in ["file_count", "folder_count", "total_size_bytes"]):
        folder = await service.update_stats(
            folder_id,
            file_count=update_data.get("file_count", 0),
            folder_count=update_data.get("folder_count", 0),
            total_size_bytes=update_data.get("total_size_bytes", 0),
        )
    else:
        folder = await service.update(folder_id, **update_data)

    if folder is None:
        raise HTTPException(status_code=404, detail="Folder not found")
    return folder


@router.delete("/folders/{folder_id}", status_code=204)
async def delete_folder(service: NASFolderServiceDep, folder_id: UUID):
    """Delete folder entry."""
    if not await service.delete(folder_id):
        raise HTTPException(status_code=404, detail="Folder not found")


# ==================== NAS Files ====================

@router.get("/files", response_model=list[NASFileResponse])
async def list_files(
    service: NASFileServiceDep,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    category: Optional[str] = Query(None),
    extension: Optional[str] = Query(None),
):
    """List NAS files with optional filters."""
    if category:
        return await service.get_by_category(category, skip=skip, limit=limit)
    if extension:
        return await service.get_by_extension(extension, skip=skip, limit=limit)
    return await service.get_all(skip=skip, limit=limit)


@router.get("/files/videos", response_model=list[NASFileResponse])
async def list_video_files(
    service: NASFileServiceDep,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
):
    """List video category files."""
    return await service.get_video_files(skip=skip, limit=limit)


@router.get("/files/unlinked", response_model=list[NASFileResponse])
async def list_unlinked_videos(
    service: NASFileServiceDep,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
):
    """List video files not linked to VideoFile records."""
    return await service.get_unlinked_videos(skip=skip, limit=limit)


@router.get("/files/linked", response_model=list[NASFileResponse])
async def list_linked_videos(
    service: NASFileServiceDep,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
):
    """List video files linked to VideoFile records."""
    return await service.get_linked_videos(skip=skip, limit=limit)


@router.get("/files/hidden", response_model=list[NASFileResponse])
async def list_hidden_files(
    service: NASFileServiceDep,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
):
    """List hidden files."""
    return await service.get_hidden_files(skip=skip, limit=limit)


@router.get("/files/largest", response_model=list[NASFileResponse])
async def list_largest_files(
    service: NASFileServiceDep,
    limit: int = Query(10, ge=1, le=100),
):
    """List files by size (largest first)."""
    return await service.get_largest_files(limit=limit)


@router.get("/files/search", response_model=list[NASFileResponse])
async def search_files(
    service: NASFileServiceDep,
    q: str = Query(..., min_length=1),
    limit: int = Query(50, ge=1, le=200),
):
    """Search files by name."""
    return await service.search_by_name(q, limit=limit)


@router.get("/files/stats", response_model=NASFileStatsResponse)
async def get_file_stats(service: NASFileServiceDep):
    """Get file statistics."""
    total = await service.count()
    total_size = await service.total_size_bytes()
    by_category = await service.count_by_category()
    by_extension = await service.count_by_extension()
    unlinked_count = await service.count_unlinked_videos()
    linked_count = await service.count_linked_videos()

    return NASFileStatsResponse(
        total_files=total,
        total_size_bytes=total_size,
        by_category=by_category,
        by_extension=by_extension,
        linked_count=linked_count,
        unlinked_count=unlinked_count,
    )


@router.get("/files/{file_id}", response_model=NASFileResponse)
async def get_file(service: NASFileServiceDep, file_id: UUID):
    """Get file by ID."""
    file = await service.get_by_id(file_id)
    if file is None:
        raise HTTPException(status_code=404, detail="File not found")
    return file


@router.post("/files", response_model=NASFileResponse, status_code=201)
async def create_file(service: NASFileServiceDep, data: NASFileCreate):
    """Create a new file entry."""
    existing = await service.get_by_path(data.file_path)
    if existing:
        raise HTTPException(status_code=409, detail="File path already exists")
    return await service.create_file(
        file_path=data.file_path,
        file_name=data.file_name,
        file_size_bytes=data.file_size_bytes,
        folder_id=data.folder_id,
        file_extension=data.file_extension,
        file_mtime=data.file_mtime,
        file_category=data.file_category,
        is_hidden_file=data.is_hidden_file,
    )


@router.patch("/files/{file_id}", response_model=NASFileResponse)
async def update_file(
    service: NASFileServiceDep,
    file_id: UUID,
    data: NASFileUpdate,
):
    """Update file metadata."""
    update_data = data.model_dump(exclude_unset=True)
    if not update_data:
        raise HTTPException(status_code=400, detail="No fields to update")

    file = await service.update(file_id, **update_data)
    if file is None:
        raise HTTPException(status_code=404, detail="File not found")
    return file


@router.post("/files/{file_id}/link/{video_file_id}", response_model=NASFileResponse)
async def link_file_to_video(
    service: NASFileServiceDep,
    file_id: UUID,
    video_file_id: UUID,
):
    """Link NAS file to a VideoFile record."""
    file = await service.link_to_video(file_id, video_file_id)
    if file is None:
        raise HTTPException(status_code=404, detail="File not found")
    return file


@router.delete("/files/{file_id}/link", response_model=NASFileResponse)
async def unlink_file_from_video(service: NASFileServiceDep, file_id: UUID):
    """Unlink NAS file from VideoFile record."""
    file = await service.unlink_video(file_id)
    if file is None:
        raise HTTPException(status_code=404, detail="File not found")
    return file


@router.delete("/files/{file_id}", status_code=204)
async def delete_file(service: NASFileServiceDep, file_id: UUID):
    """Delete file entry."""
    if not await service.delete(file_id):
        raise HTTPException(status_code=404, detail="File not found")


# ==================== Parser Statistics ====================


@router.get("/parser-stats", response_model=ParserStatsResponse)
async def get_parser_stats(
    service: NASFileServiceDep,
    limit: int = Query(10000, ge=1, le=50000),
) -> ParserStatsResponse:
    """Get file parsing statistics by parser.

    Shows which parsers matched files and success rates.
    Parsers: WSOPBracelet, WSOPCircuit, WSOPArchive, GGMillions, GOG, PAD, MPP, Generic
    """
    # Get all video files
    video_files = await service.get_video_files(limit=limit)
    total_files = len(video_files)

    # Count matches per parser
    parser_counts: dict[str, int] = {}
    unparsed_count = 0

    parsers = ParserFactory.get_all_parsers()
    parser_names = [p.name for p in parsers if p.name != "Generic"]

    for file in video_files:
        parser = ParserFactory.get_parser(file.file_name, file.file_path)
        parser_name = parser.name

        if parser_name == "Generic":
            unparsed_count += 1
        else:
            parser_counts[parser_name] = parser_counts.get(parser_name, 0) + 1

    # Build response
    parsed_files = total_files - unparsed_count
    parse_rate = (parsed_files / total_files * 100) if total_files > 0 else 0

    by_parser = []
    for parser_name in parser_names:
        count = parser_counts.get(parser_name, 0)
        percentage = (count / total_files * 100) if total_files > 0 else 0
        by_parser.append(
            ParserStatItem(
                parser_name=parser_name,
                matched_count=count,
                percentage=round(percentage, 1),
            )
        )

    # Add Generic/Unmatched
    by_parser.append(
        ParserStatItem(
            parser_name="Unmatched",
            matched_count=unparsed_count,
            percentage=round((unparsed_count / total_files * 100) if total_files > 0 else 0, 1),
        )
    )

    # Sort by count descending
    by_parser.sort(key=lambda x: x.matched_count, reverse=True)

    return ParserStatsResponse(
        total_files=total_files,
        parsed_files=parsed_files,
        unparsed_files=unparsed_count,
        parse_rate=round(parse_rate, 1),
        by_parser=by_parser,
    )


@router.get("/duplicates", response_model=DuplicatesResponse)
async def get_duplicate_files(
    service: NASFileServiceDep,
    limit: int = Query(50, ge=1, le=200),
) -> DuplicatesResponse:
    """Get potential duplicate video files.

    Detects duplicates based on:
    - Similar file names (ignoring _copy, (1), etc.)
    - Same file size
    """
    import re

    # Get all video files
    video_files = await service.get_video_files(limit=10000)

    # Group by normalized name + size
    def normalize_name(name: str) -> str:
        """Remove copy markers from filename."""
        # Remove common copy patterns
        normalized = re.sub(r"_copy\d*", "", name, flags=re.IGNORECASE)
        normalized = re.sub(r"\s*\(\d+\)", "", normalized)
        normalized = re.sub(r"\s*-\s*Copy", "", normalized, flags=re.IGNORECASE)
        return normalized.lower()

    groups: dict[tuple[str, int], list] = {}
    for file in video_files:
        key = (normalize_name(file.file_name), file.file_size_bytes)
        if key not in groups:
            groups[key] = []
        groups[key].append(file)

    # Filter to only groups with duplicates
    duplicate_groups = [
        (key, files) for key, files in groups.items() if len(files) > 1
    ]

    # Sort by file count and limit
    duplicate_groups.sort(key=lambda x: len(x[1]), reverse=True)
    duplicate_groups = duplicate_groups[:limit]

    # Build response
    result_groups = []
    total_duplicate_files = 0

    for (base_name, _), files in duplicate_groups:
        total_size = sum(f.file_size_bytes for f in files)
        total_duplicate_files += len(files)

        result_groups.append(
            DuplicateFileGroup(
                base_name=base_name,
                file_count=len(files),
                total_size_bytes=total_size,
                files=[NASFileResponse.model_validate(f) for f in files],
            )
        )

    return DuplicatesResponse(
        total_groups=len(result_groups),
        total_duplicate_files=total_duplicate_files,
        groups=result_groups,
    )


# ==================== NAS Scanner ====================


class ScanRequest(BaseModel):
    """Scan request parameters."""

    path: str = ""
    recursive: bool = False
    max_depth: int = 5


class ScanItemResponse(BaseModel):
    """Single scan result item."""

    path: str
    name: str
    is_directory: bool
    size_bytes: int = 0
    is_hidden: bool = False


class ScanResponse(BaseModel):
    """Scan results response."""

    path: str
    items: list[ScanItemResponse]
    total_folders: int
    total_files: int
    total_size_bytes: int


class SyncStatsResponse(BaseModel):
    """Sync statistics response."""

    folders_created: int
    folders_updated: int
    files_created: int
    files_updated: int
    files_skipped: int
    errors: int
    total_size_bytes: int
    duration_seconds: float


class SyncRequest(BaseModel):
    """Sync request parameters."""

    project_code: Optional[str] = None
    max_depth: int = 5


@router.post("/scan", response_model=ScanResponse)
async def scan_nas_path(request: ScanRequest):
    """Scan NAS folder without saving to database.

    This is a quick scan for browsing NAS contents.
    """
    try:
        items: list[ScanItemResponse] = []
        total_files = 0
        total_folders = 0
        total_size = 0

        async with SMBScanner() as scanner:
            async for result in scanner.scan_directory(
                path=request.path,
                recursive=request.recursive,
                max_depth=request.max_depth,
            ):
                items.append(
                    ScanItemResponse(
                        path=result.path.replace("\\", "/"),
                        name=result.name,
                        is_directory=result.is_directory,
                        size_bytes=result.size_bytes,
                        is_hidden=result.is_hidden,
                    )
                )

                if result.is_directory:
                    total_folders += 1
                else:
                    total_files += 1
                    total_size += result.size_bytes

        return ScanResponse(
            path=request.path,
            items=items,
            total_folders=total_folders,
            total_files=total_files,
            total_size_bytes=total_size,
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Scan failed: {str(e)}")


@router.post("/sync", response_model=SyncStatsResponse)
async def sync_nas_to_db(
    session: DBSessionDep,
    request: SyncRequest,
):
    """Sync NAS contents to database.

    Scans NAS and creates/updates folder and file records.
    """
    try:
        async with NASSyncService(session) as sync_service:
            if request.project_code:
                stats = await sync_service.sync_project(
                    request.project_code,
                    max_depth=request.max_depth,
                )
            else:
                stats = await sync_service.sync_all(max_depth=request.max_depth)

        return SyncStatsResponse(
            folders_created=stats.folders_created,
            folders_updated=stats.folders_updated,
            files_created=stats.files_created,
            files_updated=stats.files_updated,
            files_skipped=stats.files_skipped,
            errors=stats.errors,
            total_size_bytes=stats.total_size_bytes,
            duration_seconds=stats.duration_seconds,
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Sync failed: {str(e)}")


@router.get("/connection-test")
async def test_nas_connection():
    """Test NAS connection.

    Verifies connectivity to configured NAS server.
    """
    try:
        async with SMBScanner() as scanner:
            # Just connecting is the test
            return {
                "status": "connected",
                "server": scanner.config.nas_host,
                "share": scanner.config.nas_share,
                "base_path": scanner.config.nas_base_path,
            }
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail={
                "status": "failed",
                "error": str(e),
            },
        )

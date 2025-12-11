"""Sync Endpoints - Block E (API Agent).

Google Sheets synchronization endpoints.
"""

from typing import Any
from uuid import UUID

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from .deps import SheetsSyncServiceDep

router = APIRouter()


class StartSyncRequest(BaseModel):
    """Request to start sync."""

    sheet_id: str
    entity_type: str


class SyncStatusResponse(BaseModel):
    """Sync status response."""

    id: UUID
    sheet_id: str
    entity_type: str
    last_row_synced: int
    last_synced_at: str | None
    sync_status: str
    error_message: str | None


class SyncErrorItem(BaseModel):
    """Individual sync error."""

    record_id: UUID
    sheet_id: str
    entity_type: str
    error_message: str
    failed_at: str | None
    row_number: int | None = None


class SyncErrorsResponse(BaseModel):
    """Sync errors response."""

    total_errors: int
    errors: list[SyncErrorItem]


class HandClipLinkageStats(BaseModel):
    """HandClip linkage statistics."""

    total_clips: int
    with_video_file: int
    with_episode: int
    orphan_clips: int
    linkage_rate: float


@router.get("/summary", response_model=dict)
async def get_sync_summary(
    service: SheetsSyncServiceDep,
) -> dict[str, Any]:
    """Get summary of all sync operations."""
    return await service.get_sync_summary()


@router.get("/records", response_model=list[SyncStatusResponse])
async def list_sync_records(
    service: SheetsSyncServiceDep,
) -> list[SyncStatusResponse]:
    """List all sync records."""
    records = await service.get_all_sync_records()
    return [
        SyncStatusResponse(
            id=r.id,
            sheet_id=r.sheet_id,
            entity_type=r.entity_type,
            last_row_synced=r.last_row_synced,
            last_synced_at=r.last_synced_at.isoformat() if r.last_synced_at else None,
            sync_status=r.sync_status,
            error_message=r.error_message,
        )
        for r in records
    ]


@router.get("/records/{record_id}", response_model=SyncStatusResponse)
async def get_sync_record(
    record_id: UUID,
    service: SheetsSyncServiceDep,
) -> SyncStatusResponse:
    """Get a sync record by ID."""
    record = await service.get_by_id(record_id)
    if record is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Sync record {record_id} not found",
        )
    return SyncStatusResponse(
        id=record.id,
        sheet_id=record.sheet_id,
        entity_type=record.entity_type,
        last_row_synced=record.last_row_synced,
        last_synced_at=(
            record.last_synced_at.isoformat() if record.last_synced_at else None
        ),
        sync_status=record.sync_status,
        error_message=record.error_message,
    )


@router.post("/start", response_model=SyncStatusResponse)
async def start_sync(
    data: StartSyncRequest,
    service: SheetsSyncServiceDep,
) -> SyncStatusResponse:
    """Start a sync operation."""
    record = await service.start_sync(data.sheet_id, data.entity_type)
    return SyncStatusResponse(
        id=record.id,
        sheet_id=record.sheet_id,
        entity_type=record.entity_type,
        last_row_synced=record.last_row_synced,
        last_synced_at=(
            record.last_synced_at.isoformat() if record.last_synced_at else None
        ),
        sync_status=record.sync_status,
        error_message=record.error_message,
    )


@router.post("/complete/{record_id}", response_model=SyncStatusResponse)
async def complete_sync(
    record_id: UUID,
    last_row: int,
    service: SheetsSyncServiceDep,
) -> SyncStatusResponse:
    """Mark a sync as completed."""
    record = await service.complete_sync(record_id, last_row)
    if record is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Sync record {record_id} not found",
        )
    return SyncStatusResponse(
        id=record.id,
        sheet_id=record.sheet_id,
        entity_type=record.entity_type,
        last_row_synced=record.last_row_synced,
        last_synced_at=(
            record.last_synced_at.isoformat() if record.last_synced_at else None
        ),
        sync_status=record.sync_status,
        error_message=record.error_message,
    )


@router.post("/fail/{record_id}", response_model=SyncStatusResponse)
async def fail_sync(
    record_id: UUID,
    error_message: str,
    service: SheetsSyncServiceDep,
) -> SyncStatusResponse:
    """Mark a sync as failed."""
    record = await service.fail_sync(record_id, error_message)
    if record is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Sync record {record_id} not found",
        )
    return SyncStatusResponse(
        id=record.id,
        sheet_id=record.sheet_id,
        entity_type=record.entity_type,
        last_row_synced=record.last_row_synced,
        last_synced_at=(
            record.last_synced_at.isoformat() if record.last_synced_at else None
        ),
        sync_status=record.sync_status,
        error_message=record.error_message,
    )


@router.get("/sheet-info/{sheet_id}", response_model=dict)
async def get_sheet_info(
    sheet_id: str,
    service: SheetsSyncServiceDep,
) -> dict[str, Any]:
    """Get Google Sheet metadata."""
    try:
        return service.get_sheet_info(sheet_id)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Failed to fetch sheet info: {str(e)}",
        )


@router.delete("/records/{record_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_sync_record(
    record_id: UUID,
    service: SheetsSyncServiceDep,
) -> None:
    """Delete a sync record."""
    deleted = await service.delete(record_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Sync record {record_id} not found",
        )


@router.get("/errors", response_model=SyncErrorsResponse)
async def get_sync_errors(
    service: SheetsSyncServiceDep,
) -> SyncErrorsResponse:
    """Get all sync records with errors.

    Returns records that have sync_status='failed' or have error_message set.
    """
    records = await service.get_all_sync_records()

    # Filter for records with errors
    error_records = [
        r for r in records
        if r.sync_status == "failed" or r.error_message
    ]

    errors = [
        SyncErrorItem(
            record_id=r.id,
            sheet_id=r.sheet_id,
            entity_type=r.entity_type,
            error_message=r.error_message or "Unknown error",
            failed_at=r.last_synced_at.isoformat() if r.last_synced_at else None,
            row_number=r.last_row_synced,
        )
        for r in error_records
    ]

    return SyncErrorsResponse(
        total_errors=len(errors),
        errors=errors,
    )

"""Project Endpoints - Block E (API Agent)."""

from uuid import UUID

from fastapi import APIRouter, HTTPException, status

from .deps import ProjectServiceDep
from .schemas import ProjectCreate, ProjectResponse, ProjectUpdate

router = APIRouter()


@router.get("", response_model=list[ProjectResponse])
async def list_projects(
    service: ProjectServiceDep,
    skip: int = 0,
    limit: int = 100,
    active_only: bool = False,
) -> list[ProjectResponse]:
    """List all projects."""
    if active_only:
        projects = await service.get_active_projects()
    else:
        projects = await service.get_all(skip=skip, limit=limit)
    return [ProjectResponse.model_validate(p) for p in projects]


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(
    project_id: UUID,
    service: ProjectServiceDep,
) -> ProjectResponse:
    """Get project by ID."""
    project = await service.get_by_id(project_id)
    if project is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project {project_id} not found",
        )
    return ProjectResponse.model_validate(project)


@router.get("/code/{code}", response_model=ProjectResponse)
async def get_project_by_code(
    code: str,
    service: ProjectServiceDep,
) -> ProjectResponse:
    """Get project by code."""
    project = await service.get_by_code(code)
    if project is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project with code '{code}' not found",
        )
    return ProjectResponse.model_validate(project)


@router.post("", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
async def create_project(
    data: ProjectCreate,
    service: ProjectServiceDep,
) -> ProjectResponse:
    """Create a new project."""
    existing = await service.get_by_code(data.code)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Project with code '{data.code}' already exists",
        )
    project = await service.create_project(
        code=data.code,
        name=data.name,
        description=data.description,
        nas_base_path=data.nas_base_path,
        filename_pattern=data.filename_pattern,
    )
    return ProjectResponse.model_validate(project)


@router.patch("/{project_id}", response_model=ProjectResponse)
async def update_project(
    project_id: UUID,
    data: ProjectUpdate,
    service: ProjectServiceDep,
) -> ProjectResponse:
    """Update a project."""
    update_data = data.model_dump(exclude_unset=True)
    project = await service.update(project_id, **update_data)
    if project is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project {project_id} not found",
        )
    return ProjectResponse.model_validate(project)


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(
    project_id: UUID,
    service: ProjectServiceDep,
) -> None:
    """Delete a project."""
    deleted = await service.delete(project_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project {project_id} not found",
        )


@router.post("/seed", response_model=list[ProjectResponse])
async def seed_default_projects(
    service: ProjectServiceDep,
) -> list[ProjectResponse]:
    """Seed default projects."""
    projects = await service.seed_default_projects()
    return [ProjectResponse.model_validate(p) for p in projects]

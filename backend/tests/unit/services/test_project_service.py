"""Tests for ProjectService - Block B (Catalog Agent).

TDD: RED -> GREEN -> REFACTOR
"""

import pytest
import pytest_asyncio
from uuid import uuid4

from src.models.project import Project, ProjectCode
from src.services.catalog import ProjectService


class TestProjectService:
    """Test cases for ProjectService."""

    @pytest_asyncio.fixture
    async def service(self, async_session):
        """Create ProjectService instance."""
        return ProjectService(async_session)

    # ==================== CREATE ====================

    @pytest.mark.asyncio
    async def test_create_project_success(self, service, sample_project_data):
        """Test creating a project successfully."""
        project = await service.create_project(**sample_project_data)

        assert project is not None
        assert project.id is not None
        assert project.code == sample_project_data["code"]
        assert project.name == sample_project_data["name"]
        assert project.description == sample_project_data["description"]
        assert project.is_active is True

    @pytest.mark.asyncio
    async def test_create_project_minimal(self, service):
        """Test creating a project with minimal data."""
        project = await service.create_project(code="MIN", name="Minimal")

        assert project is not None
        assert project.code == "MIN"
        assert project.name == "Minimal"
        assert project.description is None

    # ==================== READ ====================

    @pytest.mark.asyncio
    async def test_get_by_id_success(self, service, sample_project_data):
        """Test getting a project by ID."""
        created = await service.create_project(**sample_project_data)

        found = await service.get_by_id(created.id)

        assert found is not None
        assert found.id == created.id
        assert found.code == created.code

    @pytest.mark.asyncio
    async def test_get_by_id_not_found(self, service):
        """Test getting a non-existent project."""
        found = await service.get_by_id(uuid4())

        assert found is None

    @pytest.mark.asyncio
    async def test_get_by_code_success(self, service, sample_project_data):
        """Test getting a project by code."""
        await service.create_project(**sample_project_data)

        found = await service.get_by_code(sample_project_data["code"])

        assert found is not None
        assert found.code == sample_project_data["code"]

    @pytest.mark.asyncio
    async def test_get_by_code_not_found(self, service):
        """Test getting a project by non-existent code."""
        found = await service.get_by_code("NONEXISTENT")

        assert found is None

    @pytest.mark.asyncio
    async def test_get_all_projects(self, service):
        """Test getting all projects."""
        await service.create_project(code="P1", name="Project 1")
        await service.create_project(code="P2", name="Project 2")

        projects = await service.get_all()

        assert len(projects) == 2

    @pytest.mark.asyncio
    async def test_get_all_with_pagination(self, service):
        """Test getting projects with pagination."""
        for i in range(5):
            await service.create_project(code=f"P{i}", name=f"Project {i}")

        page1 = await service.get_all(skip=0, limit=2)
        page2 = await service.get_all(skip=2, limit=2)

        assert len(page1) == 2
        assert len(page2) == 2

    @pytest.mark.asyncio
    async def test_get_active_projects(self, service):
        """Test getting only active projects."""
        p1 = await service.create_project(code="ACT", name="Active")
        p2 = await service.create_project(code="INACT", name="Inactive")
        await service.deactivate(p2.code)

        active = await service.get_active_projects()

        assert len(active) == 1
        assert active[0].code == "ACT"

    # ==================== UPDATE ====================

    @pytest.mark.asyncio
    async def test_update_project_success(self, service, sample_project_data):
        """Test updating a project."""
        created = await service.create_project(**sample_project_data)

        updated = await service.update(created.id, name="Updated Name")

        assert updated is not None
        assert updated.name == "Updated Name"
        assert updated.code == sample_project_data["code"]  # unchanged

    @pytest.mark.asyncio
    async def test_update_project_not_found(self, service):
        """Test updating a non-existent project."""
        updated = await service.update(uuid4(), name="New Name")

        assert updated is None

    @pytest.mark.asyncio
    async def test_deactivate_project(self, service, sample_project_data):
        """Test deactivating a project."""
        created = await service.create_project(**sample_project_data)

        deactivated = await service.deactivate(created.code)

        assert deactivated is not None
        assert deactivated.is_active is False

    # ==================== DELETE ====================

    @pytest.mark.asyncio
    async def test_delete_project_success(self, service, sample_project_data):
        """Test deleting a project."""
        created = await service.create_project(**sample_project_data)

        result = await service.delete(created.id)

        assert result is True
        assert await service.get_by_id(created.id) is None

    @pytest.mark.asyncio
    async def test_delete_project_not_found(self, service):
        """Test deleting a non-existent project."""
        result = await service.delete(uuid4())

        assert result is False

    # ==================== SEED ====================

    @pytest.mark.asyncio
    async def test_seed_default_projects(self, service):
        """Test seeding default projects."""
        projects = await service.seed_default_projects()

        assert len(projects) == 7
        codes = [p.code for p in projects]
        assert ProjectCode.WSOP in codes
        assert ProjectCode.HCL in codes
        assert ProjectCode.GGMILLIONS in codes

    @pytest.mark.asyncio
    async def test_seed_default_projects_idempotent(self, service):
        """Test that seeding is idempotent."""
        first_seed = await service.seed_default_projects()
        second_seed = await service.seed_default_projects()

        assert len(first_seed) == 7
        assert len(second_seed) == 0  # No new projects created

    # ==================== COUNT/EXISTS ====================

    @pytest.mark.asyncio
    async def test_count_projects(self, service):
        """Test counting projects."""
        await service.create_project(code="P1", name="Project 1")
        await service.create_project(code="P2", name="Project 2")

        count = await service.count()

        assert count == 2

    @pytest.mark.asyncio
    async def test_exists_true(self, service, sample_project_data):
        """Test exists returns true for existing project."""
        created = await service.create_project(**sample_project_data)

        exists = await service.exists(created.id)

        assert exists is True

    @pytest.mark.asyncio
    async def test_exists_false(self, service):
        """Test exists returns false for non-existent project."""
        exists = await service.exists(uuid4())

        assert exists is False

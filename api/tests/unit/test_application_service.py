"""Tests for ApplicationService."""
import pytest
from uuid import uuid4, UUID
from unittest.mock import MagicMock, patch
from app.applications.core.application_service import ApplicationService
from app.applications.infra.application_repository import ApplicationRepository
from app.applications.api.application_dto import ApplicationCreate, ApplicationUpdate
from app.applications.core.application_validators import (
    ApplicationNotFoundError,
    ApplicationNameAlreadyExistsError
)


@pytest.fixture
def mock_repository():
    """Create a mock ApplicationRepository."""
    return MagicMock(spec=ApplicationRepository)


@pytest.fixture
def application_service(mock_repository):
    """Create ApplicationService instance."""
    return ApplicationService(mock_repository)


def test_create_application_success(application_service, mock_repository):
    """Test successful application creation."""
    dto = ApplicationCreate(name="test-app", repository="https://github.com/test/repo")

    mock_repository.find_by_name.return_value = None  # Name is unique
    mock_application = MagicMock()
    mock_application.uuid = uuid4()
    mock_application.name = dto.name
    mock_application.repository = dto.repository
    mock_application.enabled = True
    mock_repository.create.return_value = mock_application

    # Mock the _build_application_entity to avoid SQLAlchemy initialization issues
    with patch.object(application_service, '_build_application_entity') as mock_build:
        mock_build.return_value = mock_application
        result = application_service.create_application(dto)

    assert result == mock_application
    mock_repository.find_by_name.assert_called_once_with(dto.name)
    mock_repository.create.assert_called_once()


def test_create_application_duplicate_name(application_service, mock_repository):
    """Test application creation with duplicate name."""
    dto = ApplicationCreate(name="test-app", repository="https://github.com/test/repo")

    # Simulate existing application with same name
    existing_app = MagicMock()
    existing_app.name = dto.name
    mock_repository.find_by_name.return_value = existing_app

    with pytest.raises(ApplicationNameAlreadyExistsError):
        application_service.create_application(dto)

    mock_repository.find_by_name.assert_called_once_with(dto.name)
    mock_repository.create.assert_not_called()


def test_update_application_success(application_service, mock_repository):
    """Test successful application update."""
    app_uuid = uuid4()
    dto = ApplicationUpdate(name="updated-app")

    existing_app = MagicMock()
    existing_app.uuid = app_uuid
    existing_app.name = "old-name"
    existing_app.repository = "https://github.com/test/repo"
    existing_app.enabled = True

    updated_app = MagicMock()
    updated_app.uuid = app_uuid
    updated_app.name = dto.name

    mock_repository.find_by_uuid.return_value = existing_app
    mock_repository.find_by_name_excluding_uuid.return_value = None  # New name is unique
    mock_repository.update.return_value = updated_app

    result = application_service.update_application(app_uuid, dto)

    assert result == updated_app
    assert existing_app.name == dto.name
    # Validator calls find_by_uuid, then service calls it again
    assert mock_repository.find_by_uuid.call_count >= 1
    mock_repository.update.assert_called_once()


def test_update_application_not_found(application_service, mock_repository):
    """Test updating non-existent application."""
    app_uuid = uuid4()
    dto = ApplicationUpdate(name="updated-app")

    mock_repository.find_by_uuid.return_value = None

    with pytest.raises(ApplicationNotFoundError):
        application_service.update_application(app_uuid, dto)

    mock_repository.find_by_uuid.assert_called_once_with(app_uuid)
    mock_repository.update.assert_not_called()


def test_get_application_success(application_service, mock_repository):
    """Test getting application by UUID."""
    app_uuid = uuid4()
    mock_application = MagicMock()
    mock_application.uuid = app_uuid
    mock_repository.find_by_uuid.return_value = mock_application

    result = application_service.get_application(app_uuid)

    assert result == mock_application
    # Validator calls find_by_uuid, then service calls it again
    assert mock_repository.find_by_uuid.call_count >= 1
    # Check that it was called with the correct UUID at least once
    assert any(call[0][0] == app_uuid for call in mock_repository.find_by_uuid.call_args_list)


def test_get_application_not_found(application_service, mock_repository):
    """Test getting non-existent application."""
    app_uuid = uuid4()
    mock_repository.find_by_uuid.return_value = None

    with pytest.raises(ApplicationNotFoundError):
        application_service.get_application(app_uuid)

    mock_repository.find_by_uuid.assert_called_once_with(app_uuid)


def test_get_applications(application_service, mock_repository):
    """Test getting all applications."""
    mock_apps = [MagicMock(), MagicMock()]
    mock_repository.find_all.return_value = mock_apps

    result = application_service.get_applications(skip=0, limit=10)

    assert result == mock_apps
    mock_repository.find_all.assert_called_once_with(skip=0, limit=10)


def test_delete_application_success(application_service, mock_repository):
    """Test successful application deletion."""
    app_uuid = uuid4()
    mock_application = MagicMock()
    mock_application.uuid = app_uuid
    mock_application.id = 1
    mock_application.instances = []  # No instances

    mock_repository.find_by_uuid.return_value = mock_application
    mock_db = MagicMock()

    with patch('app.applications.core.application_service.InstanceService') as mock_instance_service_class:
        mock_instance_service = MagicMock()
        mock_instance_service_class.return_value = mock_instance_service

        result = application_service.delete_application(app_uuid, mock_db)

        assert result == {"detail": "Application deleted successfully"}
        # Validator calls find_by_uuid, then service calls it again
        assert mock_repository.find_by_uuid.call_count >= 1
        mock_repository.delete_by_id.assert_called_once_with(mock_application.id)
        mock_db.commit.assert_called()


def test_delete_application_with_instances(application_service, mock_repository):
    """Test application deletion with instances."""
    app_uuid = uuid4()
    mock_application = MagicMock()
    mock_application.uuid = app_uuid
    mock_application.id = 1

    # Create mock instances
    mock_instance1 = MagicMock()
    mock_instance1.uuid = uuid4()
    mock_instance2 = MagicMock()
    mock_instance2.uuid = uuid4()
    mock_application.instances = [mock_instance1, mock_instance2]

    mock_repository.find_by_uuid.return_value = mock_application
    mock_db = MagicMock()

    with patch('app.applications.core.application_service.InstanceService') as mock_instance_service_class, \
         patch('app.applications.core.application_service.InstanceRepository') as mock_instance_repo_class:
        mock_instance_service = MagicMock()
        mock_instance_service.delete_instance.return_value = {"detail": "Instance deleted successfully"}
        mock_instance_service_class.return_value = mock_instance_service

        result = application_service.delete_application(app_uuid, mock_db)

        assert result == {"detail": "Application deleted successfully"}
        # Should delete both instances
        assert mock_instance_service.delete_instance.call_count == 2
        assert mock_instance_service.delete_instance.call_args_list[0][0][0] == mock_instance1.uuid
        assert mock_instance_service.delete_instance.call_args_list[1][0][0] == mock_instance2.uuid
        # Should commit after each instance deletion
        assert mock_db.commit.call_count >= 2
        mock_repository.delete_by_id.assert_called_once_with(mock_application.id)


def test_delete_application_not_found(application_service, mock_repository):
    """Test deleting non-existent application."""
    app_uuid = uuid4()
    mock_repository.find_by_uuid.return_value = None

    with pytest.raises(ApplicationNotFoundError):
        application_service.delete_application(app_uuid, MagicMock())

    mock_repository.delete_by_id.assert_not_called()


def test_update_application_duplicate_name(application_service, mock_repository):
    """Test updating application with duplicate name."""
    app_uuid = uuid4()
    dto = ApplicationUpdate(name="duplicate-name")

    existing_app = MagicMock()
    existing_app.uuid = app_uuid
    existing_app.name = "old-name"

    duplicate_app = MagicMock()
    duplicate_app.uuid = uuid4()  # Different UUID

    mock_repository.find_by_uuid.return_value = existing_app
    mock_repository.find_by_name_excluding_uuid.return_value = duplicate_app

    with pytest.raises(ApplicationNameAlreadyExistsError):
        application_service.update_application(app_uuid, dto)

    mock_repository.update.assert_not_called()


def test_update_application_partial(application_service, mock_repository):
    """Test partial application update."""
    app_uuid = uuid4()
    dto = ApplicationUpdate(repository="https://github.com/new/repo")  # Only update repository

    existing_app = MagicMock()
    existing_app.uuid = app_uuid
    existing_app.name = "test-app"
    existing_app.repository = "https://github.com/old/repo"
    existing_app.enabled = True

    updated_app = MagicMock()
    updated_app.uuid = app_uuid

    mock_repository.find_by_uuid.return_value = existing_app
    mock_repository.update.return_value = updated_app

    result = application_service.update_application(app_uuid, dto)

    assert result == updated_app
    assert existing_app.repository == dto.repository
    # Name should not be updated
    mock_repository.update.assert_called_once()


def test_update_application_enabled_only(application_service, mock_repository):
    """Test updating only enabled field."""
    app_uuid = uuid4()
    dto = ApplicationUpdate(enabled=False)

    existing_app = MagicMock()
    existing_app.uuid = app_uuid
    existing_app.name = "test-app"
    existing_app.repository = "https://github.com/test/repo"
    existing_app.enabled = True

    updated_app = MagicMock()
    updated_app.uuid = app_uuid

    mock_repository.find_by_uuid.return_value = existing_app
    mock_repository.update.return_value = updated_app

    result = application_service.update_application(app_uuid, dto)

    assert result == updated_app
    assert existing_app.enabled == dto.enabled
    # Name and repository should not be updated
    mock_repository.update.assert_called_once()


def test_update_application_multiple_fields(application_service, mock_repository):
    """Test updating multiple fields at once."""
    app_uuid = uuid4()
    dto = ApplicationUpdate(
        name="updated-name",
        repository="https://github.com/updated/repo",
        enabled=False
    )

    existing_app = MagicMock()
    existing_app.uuid = app_uuid
    existing_app.name = "old-name"
    existing_app.repository = "https://github.com/old/repo"
    existing_app.enabled = True

    updated_app = MagicMock()
    updated_app.uuid = app_uuid

    mock_repository.find_by_uuid.return_value = existing_app
    mock_repository.find_by_name_excluding_uuid.return_value = None
    mock_repository.update.return_value = updated_app

    result = application_service.update_application(app_uuid, dto)

    assert result == updated_app
    assert existing_app.name == dto.name
    assert existing_app.repository == dto.repository
    assert existing_app.enabled == dto.enabled
    mock_repository.update.assert_called_once()


def test_create_application_with_enabled_default(application_service, mock_repository):
    """Test application creation with default enabled value."""
    dto = ApplicationCreate(name="test-app", repository="https://github.com/test/repo")

    mock_repository.find_by_name.return_value = None
    mock_application = MagicMock()
    mock_application.uuid = uuid4()
    mock_application.name = dto.name
    mock_application.repository = dto.repository
    mock_application.enabled = True  # Default value
    mock_repository.create.return_value = mock_application

    with patch.object(application_service, '_build_application_entity') as mock_build:
        mock_build.return_value = mock_application
        result = application_service.create_application(dto)

    assert result == mock_application
    mock_repository.create.assert_called_once()


def test_create_application_with_enabled_false(application_service, mock_repository):
    """Test application creation with enabled=False."""
    dto = ApplicationCreate(
        name="test-app",
        repository="https://github.com/test/repo",
        enabled=False
    )

    mock_repository.find_by_name.return_value = None
    mock_application = MagicMock()
    mock_application.uuid = uuid4()
    mock_application.name = dto.name
    mock_application.repository = dto.repository
    mock_application.enabled = False
    mock_repository.create.return_value = mock_application

    with patch.object(application_service, '_build_application_entity') as mock_build:
        mock_build.return_value = mock_application
        result = application_service.create_application(dto)

    assert result == mock_application
    mock_repository.create.assert_called_once()


def test_get_applications_with_pagination(application_service, mock_repository):
    """Test getting applications with different pagination."""
    mock_apps = [MagicMock(), MagicMock(), MagicMock()]
    mock_repository.find_all.return_value = mock_apps

    result = application_service.get_applications(skip=10, limit=20)

    assert len(result) == 3
    mock_repository.find_all.assert_called_once_with(skip=10, limit=20)


def test_get_applications_empty(application_service, mock_repository):
    """Test getting applications when there are none."""
    mock_repository.find_all.return_value = []

    result = application_service.get_applications(skip=0, limit=10)

    assert result == []
    assert len(result) == 0
    mock_repository.find_all.assert_called_once_with(skip=0, limit=10)


def test_delete_application_instance_deletion_error(application_service, mock_repository):
    """Test application deletion when instance deletion fails."""
    app_uuid = uuid4()
    mock_application = MagicMock()
    mock_application.uuid = app_uuid
    mock_application.id = 1

    mock_instance = MagicMock()
    mock_instance.uuid = uuid4()
    mock_application.instances = [mock_instance]

    mock_repository.find_by_uuid.return_value = mock_application
    mock_db = MagicMock()

    with patch('app.applications.core.application_service.InstanceService') as mock_instance_service_class, \
         patch('app.applications.core.application_service.InstanceRepository') as mock_instance_repo_class:
        mock_instance_service = MagicMock()
        mock_instance_service.delete_instance.side_effect = Exception("Failed to delete instance")
        mock_instance_service_class.return_value = mock_instance_service

        with pytest.raises(Exception, match="Failed to delete instance"):
            application_service.delete_application(app_uuid, mock_db)

        mock_db.rollback.assert_called()
        mock_repository.delete_by_id.assert_not_called()


def test_delete_application_application_deletion_error(application_service, mock_repository):
    """Test application deletion when application deletion fails."""
    app_uuid = uuid4()
    mock_application = MagicMock()
    mock_application.uuid = app_uuid
    mock_application.id = 1
    mock_application.instances = []

    mock_repository.find_by_uuid.return_value = mock_application
    mock_repository.delete_by_id.side_effect = Exception("Database error")
    mock_db = MagicMock()

    with patch('app.applications.core.application_service.InstanceService') as mock_instance_service_class:
        mock_instance_service = MagicMock()
        mock_instance_service_class.return_value = mock_instance_service

        with pytest.raises(Exception, match="Failed to delete application"):
            application_service.delete_application(app_uuid, mock_db)

        mock_db.rollback.assert_called()


def test_delete_application_creates_instance_service(application_service, mock_repository):
    """Test that instance service is created when not provided."""
    app_uuid = uuid4()
    mock_application = MagicMock()
    mock_application.uuid = app_uuid
    mock_application.id = 1
    mock_application.instances = []

    mock_repository.find_by_uuid.return_value = mock_application
    mock_db = MagicMock()

    with patch('app.applications.core.application_service.InstanceService') as mock_instance_service_class, \
         patch('app.applications.core.application_service.InstanceRepository') as mock_instance_repo_class:
        mock_instance_service = MagicMock()
        mock_instance_service_class.return_value = mock_instance_service
        mock_instance_repo = MagicMock()
        mock_instance_repo_class.return_value = mock_instance_repo

        # Ensure instance_service is None initially
        application_service.instance_service = None

        result = application_service.delete_application(app_uuid, mock_db)

        assert result == {"detail": "Application deleted successfully"}
        # InstanceService should be created
        mock_instance_repo_class.assert_called_once_with(mock_db)
        mock_instance_service_class.assert_called_once_with(mock_instance_repo, mock_db)
        mock_repository.delete_by_id.assert_called_once_with(mock_application.id)


def test_create_application_validation_error_empty_name(application_service, mock_repository):
    """Test application creation with empty name raises validation error."""
    dto = ApplicationCreate(name="", repository="https://github.com/test/repo")

    with pytest.raises(ValueError, match="Application name is required"):
        application_service.create_application(dto)

    mock_repository.create.assert_not_called()


def test_create_application_validation_error_whitespace_name(application_service, mock_repository):
    """Test application creation with whitespace-only name raises validation error."""
    dto = ApplicationCreate(name="   ", repository="https://github.com/test/repo")

    with pytest.raises(ValueError, match="Application name is required"):
        application_service.create_application(dto)

    mock_repository.create.assert_not_called()


def test_update_application_validation_error_empty_name(application_service, mock_repository):
    """Test application update with empty name raises validation error."""
    app_uuid = uuid4()
    dto = ApplicationUpdate(name="")

    mock_repository.find_by_uuid.return_value = MagicMock()

    with pytest.raises(ValueError, match="Application name cannot be empty"):
        application_service.update_application(app_uuid, dto)

    mock_repository.update.assert_not_called()


def test_update_application_validation_error_whitespace_name(application_service, mock_repository):
    """Test application update with whitespace-only name raises validation error."""
    app_uuid = uuid4()
    dto = ApplicationUpdate(name="   ")

    mock_repository.find_by_uuid.return_value = MagicMock()

    with pytest.raises(ValueError, match="Application name cannot be empty"):
        application_service.update_application(app_uuid, dto)

    mock_repository.update.assert_not_called()
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

    with patch('app.applications.core.application_service.InstanceService') as mock_instance_service_class:
        mock_instance_service = MagicMock()
        mock_instance_service_class.return_value = mock_instance_service

        result = application_service.delete_application(app_uuid, MagicMock())

        assert result == {"detail": "Application deleted successfully"}
        # Validator calls find_by_uuid, then service calls it again
        assert mock_repository.find_by_uuid.call_count >= 1
        mock_repository.delete_by_id.assert_called_once_with(mock_application.id)

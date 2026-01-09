"""Tests for InstanceService."""
import pytest
from uuid import uuid4, UUID
from unittest.mock import MagicMock, patch
from app.instances.core.instance_service import InstanceService
from app.instances.infra.instance_repository import InstanceRepository
from app.instances.api.instance_dto import InstanceCreate, InstanceUpdate
from app.instances.core.instance_validators import (
    InstanceNotFoundError,
    InstanceAlreadyExistsError,
    ApplicationNotFoundError,
    EnvironmentNotFoundError
)


@pytest.fixture
def mock_repository():
    """Create a mock InstanceRepository."""
    return MagicMock(spec=InstanceRepository)


@pytest.fixture
def mock_db():
    """Create a mock database session."""
    return MagicMock()


@pytest.fixture
def instance_service(mock_repository, mock_db):
    """Create InstanceService instance."""
    return InstanceService(mock_repository, mock_db)


def test_create_instance_success(instance_service, mock_repository):
    """Test successful instance creation."""
    app_uuid = uuid4()
    env_uuid = uuid4()
    dto = InstanceCreate(
        application_uuid=app_uuid,
        environment_uuid=env_uuid,
        image="nginx",
        version="1.0.0"
    )

    mock_application = MagicMock()
    mock_application.id = 1
    mock_application.uuid = app_uuid

    mock_environment = MagicMock()
    mock_environment.id = 1
    mock_environment.uuid = env_uuid

    mock_instance = MagicMock()
    mock_instance.uuid = uuid4()

    mock_repository.find_application_by_uuid.return_value = mock_application
    mock_repository.find_environment_by_uuid.return_value = mock_environment
    mock_repository.find_by_application_and_environment.return_value = None  # Unique
    mock_repository.create.return_value = mock_instance

    # Mock _build_instance_entity to avoid SQLAlchemy initialization issues
    with patch.object(instance_service, '_build_instance_entity') as mock_build:
        mock_build.return_value = mock_instance
        result = instance_service.create_instance(dto)

    assert result == mock_instance
    # Validator calls find_application_by_uuid, then service calls it again
    assert mock_repository.find_application_by_uuid.call_count >= 1
    # Check that it was called with the correct UUID at least once
    assert any(call[0][0] == app_uuid for call in mock_repository.find_application_by_uuid.call_args_list)
    # Validator calls find_environment_by_uuid, then service calls it again
    assert mock_repository.find_environment_by_uuid.call_count >= 1
    # Check that it was called with the correct UUID at least once
    assert any(call[0][0] == env_uuid for call in mock_repository.find_environment_by_uuid.call_args_list)
    mock_repository.create.assert_called_once()


def test_create_instance_application_not_found(instance_service, mock_repository):
    """Test instance creation with non-existent application."""
    app_uuid = uuid4()
    env_uuid = uuid4()
    dto = InstanceCreate(
        application_uuid=app_uuid,
        environment_uuid=env_uuid,
        image="nginx",
        version="1.0.0"
    )

    mock_repository.find_application_by_uuid.return_value = None

    with pytest.raises(ApplicationNotFoundError):
        instance_service.create_instance(dto)

    mock_repository.find_application_by_uuid.assert_called_once_with(app_uuid)
    mock_repository.create.assert_not_called()


def test_create_instance_environment_not_found(instance_service, mock_repository):
    """Test instance creation with non-existent environment."""
    app_uuid = uuid4()
    env_uuid = uuid4()
    dto = InstanceCreate(
        application_uuid=app_uuid,
        environment_uuid=env_uuid,
        image="nginx",
        version="1.0.0"
    )

    mock_application = MagicMock()
    mock_application.id = 1
    mock_repository.find_application_by_uuid.return_value = mock_application
    mock_repository.find_environment_by_uuid.return_value = None

    with pytest.raises(EnvironmentNotFoundError):
        instance_service.create_instance(dto)

    mock_repository.find_environment_by_uuid.assert_called_once_with(env_uuid)
    mock_repository.create.assert_not_called()


def test_update_instance_success(instance_service, mock_repository):
    """Test successful instance update."""
    instance_uuid = uuid4()
    dto = InstanceUpdate(image="nginx:latest", version="2.0.0")

    mock_instance = MagicMock()
    mock_instance.uuid = instance_uuid
    mock_instance.image = "nginx"
    mock_instance.version = "1.0.0"
    mock_instance.enabled = True

    updated_instance = MagicMock()
    updated_instance.uuid = instance_uuid
    updated_instance.image = dto.image
    updated_instance.version = dto.version

    mock_repository.find_by_uuid.return_value = mock_instance
    mock_repository.update.return_value = updated_instance

    result = instance_service.update_instance(instance_uuid, dto)

    assert result == updated_instance
    assert mock_instance.image == dto.image
    assert mock_instance.version == dto.version
    mock_repository.update.assert_called_once()


def test_get_instance_success(instance_service, mock_repository):
    """Test getting instance by UUID."""
    instance_uuid = uuid4()
    mock_instance = MagicMock()
    mock_instance.uuid = instance_uuid
    mock_repository.find_by_uuid.return_value = mock_instance

    result = instance_service.get_instance(instance_uuid)

    assert result == mock_instance
    # Validator calls find_by_uuid without load_components, service calls with load_components=True
    assert mock_repository.find_by_uuid.call_count >= 1
    # Check that it was called with load_components=True at least once
    assert any(
        call.kwargs.get('load_components') == True
        for call in mock_repository.find_by_uuid.call_args_list
        if call.kwargs
    )


def test_get_instance_not_found(instance_service, mock_repository):
    """Test getting non-existent instance."""
    instance_uuid = uuid4()
    mock_repository.find_by_uuid.return_value = None

    with pytest.raises(InstanceNotFoundError):
        instance_service.get_instance(instance_uuid)

    # Validator calls find_by_uuid without load_components first, which returns None
    # So the exception is raised before service calls it with load_components
    assert mock_repository.find_by_uuid.call_count >= 1

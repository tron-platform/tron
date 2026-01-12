"""Tests for SettingsService."""
import pytest
from uuid import uuid4, UUID
from unittest.mock import MagicMock, patch
from app.settings.core.settings_service import SettingsService
from app.settings.infra.settings_repository import SettingsRepository
from app.settings.api.settings_dto import SettingsCreate, SettingsUpdate
from app.settings.core.settings_validators import (
    SettingsNotFoundError,
    EnvironmentNotFoundError,
    SettingsKeyAlreadyExistsError
)


@pytest.fixture
def mock_repository():
    """Create a mock SettingsRepository."""
    return MagicMock(spec=SettingsRepository)


@pytest.fixture
def settings_service(mock_repository):
    """Create SettingsService instance."""
    return SettingsService(mock_repository)


@pytest.fixture
def mock_environment():
    """Create a mock environment."""
    environment = MagicMock()
    environment.id = 1
    environment.uuid = uuid4()
    environment.name = "test-env"
    return environment


@pytest.fixture
def mock_settings():
    """Create a mock settings."""
    settings = MagicMock()
    settings.uuid = uuid4()
    settings.id = 1
    settings.key = "test-key"
    settings.value = "test-value"
    settings.description = "Test description"
    settings.environment_id = 1
    settings.environment = MagicMock()
    settings.environment.name = "test-env"
    settings.environment.uuid = uuid4()
    return settings


def test_create_settings_success(settings_service, mock_repository, mock_environment):
    """Test successful settings creation."""
    dto = SettingsCreate(
        key="test-key",
        value="test-value",
        description="Test description",
        environment_uuid=mock_environment.uuid
    )

    mock_settings = MagicMock()
    mock_settings.uuid = uuid4()
    mock_settings.key = dto.key

    mock_repository.find_environment_by_uuid.return_value = mock_environment
    mock_repository.find_by_key_and_environment_id.return_value = None  # Key is unique
    mock_repository.create.return_value = mock_settings

    with patch.object(settings_service, '_build_settings_entity', return_value=mock_settings):
        result = settings_service.create_settings(dto)

        assert result == mock_settings
        # Validator also calls find_environment_by_uuid
        assert mock_repository.find_environment_by_uuid.call_count >= 1
        mock_repository.create.assert_called_once()


def test_create_settings_environment_not_found(settings_service, mock_repository):
    """Test settings creation with non-existent environment."""
    dto = SettingsCreate(
        key="test-key",
        value="test-value",
        environment_uuid=uuid4()
    )

    mock_repository.find_environment_by_uuid.return_value = None

    with pytest.raises(EnvironmentNotFoundError):
        settings_service.create_settings(dto)


def test_create_settings_duplicate_key(settings_service, mock_repository, mock_environment):
    """Test settings creation with duplicate key."""
    dto = SettingsCreate(
        key="existing-key",
        value="test-value",
        environment_uuid=mock_environment.uuid
    )

    existing_settings = MagicMock()
    existing_settings.key = dto.key

    mock_repository.find_environment_by_uuid.return_value = mock_environment
    mock_repository.find_by_key_and_environment_id.return_value = existing_settings

    with pytest.raises(SettingsKeyAlreadyExistsError):
        settings_service.create_settings(dto)


def test_update_settings_success(settings_service, mock_repository, mock_settings):
    """Test successful settings update."""
    settings_uuid = mock_settings.uuid
    dto = SettingsUpdate(key="updated-key", value="updated-value")

    updated_settings = MagicMock()
    updated_settings.uuid = settings_uuid
    updated_settings.key = dto.key

    mock_settings.environment_id = 1
    mock_repository.find_by_uuid.return_value = mock_settings
    # When exclude_uuid is provided, validator checks if existing_settings.uuid == exclude_uuid
    # Since we're updating the same settings, we need to mock it to return the same settings
    # OR return None (no existing settings with that key)
    mock_repository.find_by_key_and_environment_id.return_value = None  # No conflict
    mock_repository.update.return_value = updated_settings

    result = settings_service.update_settings(settings_uuid, dto)

    assert result == updated_settings
    assert mock_settings.key == dto.key
    assert mock_settings.value == dto.value
    mock_repository.update.assert_called_once()


def test_update_settings_partial(settings_service, mock_repository, mock_settings):
    """Test partial settings update."""
    settings_uuid = mock_settings.uuid
    dto = SettingsUpdate(value="updated-value")  # Only update value

    updated_settings = MagicMock()
    updated_settings.uuid = settings_uuid

    mock_repository.find_by_uuid.return_value = mock_settings
    mock_repository.update.return_value = updated_settings

    result = settings_service.update_settings(settings_uuid, dto)

    assert result == updated_settings
    assert mock_settings.value == dto.value
    # Key should not be updated
    mock_repository.update.assert_called_once()


def test_update_settings_not_found(settings_service, mock_repository):
    """Test updating non-existent settings."""
    settings_uuid = uuid4()
    dto = SettingsUpdate(key="updated-key")

    mock_repository.find_by_uuid.return_value = None

    with pytest.raises(SettingsNotFoundError):
        settings_service.update_settings(settings_uuid, dto)


def test_get_settings_success(settings_service, mock_repository, mock_settings):
    """Test getting settings by UUID."""
    settings_uuid = mock_settings.uuid
    mock_repository.find_by_uuid.return_value = mock_settings

    with patch.object(settings_service, '_serialize_settings_with_environment') as mock_serialize:
        mock_response = MagicMock()
        mock_serialize.return_value = mock_response

        result = settings_service.get_settings(settings_uuid)

        assert result == mock_response
        # Validator also calls find_by_uuid
        assert mock_repository.find_by_uuid.call_count >= 1
        mock_serialize.assert_called_once_with(mock_settings)


def test_get_settings_not_found(settings_service, mock_repository):
    """Test getting non-existent settings."""
    settings_uuid = uuid4()
    mock_repository.find_by_uuid.return_value = None

    with pytest.raises(SettingsNotFoundError):
        settings_service.get_settings(settings_uuid)


def test_get_settings_list(settings_service, mock_repository, mock_settings):
    """Test getting all settings."""
    mock_settings2 = MagicMock()
    mock_settings2.uuid = uuid4()
    mock_settings2.key = "test-key-2"
    mock_settings2.environment = MagicMock()
    mock_settings2.environment.name = "test-env"
    mock_settings2.environment.uuid = uuid4()

    mock_repository.find_all.return_value = [mock_settings, mock_settings2]

    with patch.object(settings_service, '_serialize_settings_with_environment') as mock_serialize:
        mock_serialize.side_effect = lambda s: MagicMock(uuid=s.uuid, key=s.key)

        result = settings_service.get_settings_list(skip=0, limit=10)

        assert len(result) == 2
        mock_repository.find_all.assert_called_once_with(skip=0, limit=10)


def test_delete_settings_success(settings_service, mock_repository, mock_settings):
    """Test successful settings deletion."""
    settings_uuid = mock_settings.uuid
    mock_repository.find_by_uuid.return_value = mock_settings

    result = settings_service.delete_settings(settings_uuid)

    assert result == {"detail": "Settings deleted successfully"}
    # Validator also calls find_by_uuid
    assert mock_repository.find_by_uuid.call_count >= 1
    mock_repository.delete.assert_called_once_with(mock_settings)


def test_delete_settings_not_found(settings_service, mock_repository):
    """Test deleting non-existent settings."""
    settings_uuid = uuid4()
    mock_repository.find_by_uuid.return_value = None

    with pytest.raises(SettingsNotFoundError):
        settings_service.delete_settings(settings_uuid)

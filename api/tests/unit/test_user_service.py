"""Tests for UserService."""
import pytest
from uuid import uuid4, UUID
from unittest.mock import MagicMock, patch
from app.users.core.user_service import UserService
from app.users.infra.user_repository import UserRepository
from app.users.api.user_dto import UserCreate, UserUpdate
from app.users.core.user_validators import (
    UserNotFoundError,
    UserEmailAlreadyExistsError,
    CannotDeleteSelfError
)
from app.users.infra.user_model import UserRole


@pytest.fixture
def mock_repository():
    """Create a mock UserRepository."""
    return MagicMock(spec=UserRepository)


@pytest.fixture
def mock_auth_service():
    """Create a mock AuthService."""
    mock_service = MagicMock()
    mock_service.get_password_hash.return_value = "hashed_password"
    return mock_service


@pytest.fixture
def user_service(mock_repository, mock_auth_service):
    """Create UserService instance."""
    return UserService(mock_repository, mock_auth_service)


def test_create_user_success(user_service, mock_repository, mock_auth_service):
    """Test successful user creation."""
    dto = UserCreate(
        email="test@example.com",
        password="password123",
        full_name="Test User"
    )

    mock_repository.find_by_email.return_value = None  # Email is unique
    mock_user = MagicMock()
    mock_user.uuid = uuid4()
    mock_user.email = dto.email
    mock_user.full_name = dto.full_name
    mock_user.role = UserRole.USER.value
    mock_repository.create.return_value = mock_user

    # Mock _build_user_entity to avoid SQLAlchemy initialization issues
    with patch.object(user_service, '_build_user_entity') as mock_build:
        mock_build.return_value = mock_user
        result = user_service.create_user(dto)

    assert result == mock_user
    mock_repository.find_by_email.assert_called_once_with(dto.email)
    mock_auth_service.get_password_hash.assert_called_once_with(dto.password)
    mock_repository.create.assert_called_once()


def test_create_user_duplicate_email(user_service, mock_repository):
    """Test user creation with duplicate email."""
    dto = UserCreate(
        email="existing@example.com",
        password="password123",
        full_name="Test User"
    )

    existing_user = MagicMock()
    existing_user.email = dto.email
    mock_repository.find_by_email.return_value = existing_user

    with pytest.raises(UserEmailAlreadyExistsError):
        user_service.create_user(dto)

    mock_repository.find_by_email.assert_called_once_with(dto.email)
    mock_repository.create.assert_not_called()


def test_update_user_success(user_service, mock_repository):
    """Test successful user update."""
    user_uuid = uuid4()
    dto = UserUpdate(full_name="Updated Name")

    existing_user = MagicMock()
    existing_user.uuid = user_uuid
    existing_user.email = "test@example.com"
    existing_user.full_name = "Old Name"

    updated_user = MagicMock()
    updated_user.uuid = user_uuid
    updated_user.full_name = dto.full_name

    mock_repository.find_by_uuid.return_value = existing_user
    mock_repository.find_by_email.return_value = None  # Email check uses find_by_email
    mock_repository.update.return_value = updated_user

    result = user_service.update_user(user_uuid, dto)

    assert result == updated_user
    # Validator calls find_by_uuid, then service calls it again
    assert mock_repository.find_by_uuid.call_count >= 1
    mock_repository.update.assert_called_once()


def test_get_user_success(user_service, mock_repository):
    """Test getting user by UUID."""
    user_uuid = uuid4()
    mock_user = MagicMock()
    mock_user.uuid = user_uuid
    mock_repository.find_by_uuid.return_value = mock_user

    result = user_service.get_user(user_uuid)

    assert result == mock_user
    # Validator calls find_by_uuid, then service calls it again
    assert mock_repository.find_by_uuid.call_count >= 1
    # Check that it was called with the correct UUID at least once
    assert any(call[0][0] == user_uuid for call in mock_repository.find_by_uuid.call_args_list)


def test_get_user_not_found(user_service, mock_repository):
    """Test getting non-existent user."""
    user_uuid = uuid4()
    mock_repository.find_by_uuid.return_value = None

    with pytest.raises(UserNotFoundError):
        user_service.get_user(user_uuid)

    mock_repository.find_by_uuid.assert_called_once_with(user_uuid)


def test_delete_user_success(user_service, mock_repository):
    """Test successful user deletion."""
    user_uuid = uuid4()
    current_user_uuid = uuid4()  # Different user

    mock_user = MagicMock()
    mock_user.uuid = user_uuid
    mock_repository.find_by_uuid.return_value = mock_user

    result = user_service.delete_user(user_uuid, current_user_uuid)

    assert result is None
    mock_repository.find_by_uuid.assert_called()
    mock_repository.delete.assert_called_once_with(mock_user)


def test_delete_user_cannot_delete_self(user_service, mock_repository):
    """Test that user cannot delete themselves."""
    user_uuid = uuid4()

    mock_user = MagicMock()
    mock_user.uuid = user_uuid
    mock_repository.find_by_uuid.return_value = mock_user

    with pytest.raises(CannotDeleteSelfError):
        user_service.delete_user(user_uuid, user_uuid)  # Same UUID

    mock_repository.find_by_uuid.assert_called_once_with(user_uuid)
    mock_repository.delete.assert_not_called()

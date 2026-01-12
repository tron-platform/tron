"""Tests for AuthService."""
import pytest
from uuid import uuid4
from unittest.mock import MagicMock, patch
from datetime import timedelta
from jose import JWTError
from fastapi import HTTPException

from app.auth.core.auth_service import AuthService
from app.users.infra.user_repository import UserRepository
from app.auth.infra.token_repository import TokenRepository
from app.users.infra.user_model import User, UserRole


@pytest.fixture
def mock_user_repository():
    """Create a mock UserRepository."""
    return MagicMock(spec=UserRepository)


@pytest.fixture
def mock_token_repository():
    """Create a mock TokenRepository."""
    return MagicMock(spec=TokenRepository)


@pytest.fixture
def auth_service(mock_user_repository, mock_token_repository):
    """Create AuthService instance."""
    return AuthService(mock_user_repository, mock_token_repository)


@pytest.fixture
def mock_user():
    """Create a mock user."""
    user = MagicMock(spec=User)
    user.uuid = uuid4()
    user.email = "test@example.com"
    user.hashed_password = AuthService.get_password_hash("password123")
    user.is_active = True
    user.full_name = "Test User"
    user.role = UserRole.USER
    return user


def test_verify_password_success(auth_service):
    """Test password verification with correct password."""
    password = "password123"
    hashed = AuthService.get_password_hash(password)

    result = AuthService.verify_password(password, hashed)

    assert result is True


def test_verify_password_failure(auth_service):
    """Test password verification with incorrect password."""
    password = "password123"
    wrong_password = "wrongpassword"
    hashed = AuthService.get_password_hash(password)

    result = AuthService.verify_password(wrong_password, hashed)

    assert result is False


def test_get_password_hash(auth_service):
    """Test password hashing."""
    password = "password123"

    hashed = AuthService.get_password_hash(password)

    assert hashed != password
    assert isinstance(hashed, str)
    assert len(hashed) > 0


def test_create_access_token(auth_service):
    """Test access token creation."""
    data = {"sub": "test@example.com", "uuid": str(uuid4())}

    token = AuthService.create_access_token(data)

    assert isinstance(token, str)
    assert len(token) > 0


def test_create_access_token_with_expires_delta(auth_service):
    """Test access token creation with custom expiration."""
    data = {"sub": "test@example.com", "uuid": str(uuid4())}
    expires_delta = timedelta(minutes=60)

    token = AuthService.create_access_token(data, expires_delta=expires_delta)

    assert isinstance(token, str)
    # Verify token can be decoded
    payload = AuthService.verify_token(token)
    assert payload["sub"] == "test@example.com"


def test_create_refresh_token(auth_service):
    """Test refresh token creation."""
    data = {"sub": "test@example.com", "uuid": str(uuid4())}

    token = AuthService.create_refresh_token(data)

    assert isinstance(token, str)
    assert len(token) > 0
    # Verify token can be decoded
    payload = AuthService.verify_token(token)
    assert payload["type"] == "refresh"


def test_verify_token_success(auth_service):
    """Test token verification with valid token."""
    data = {"sub": "test@example.com", "uuid": str(uuid4())}
    token = AuthService.create_access_token(data)

    payload = AuthService.verify_token(token)

    assert payload["sub"] == "test@example.com"
    assert payload["type"] == "access"


def test_verify_token_invalid(auth_service):
    """Test token verification with invalid token."""
    invalid_token = "invalid.token.here"

    with pytest.raises(HTTPException) as exc_info:
        AuthService.verify_token(invalid_token)

    assert exc_info.value.status_code == 401


def test_authenticate_user_success(auth_service, mock_user_repository, mock_user):
    """Test successful user authentication."""
    mock_user_repository.find_by_email.return_value = mock_user

    result = auth_service.authenticate_user("test@example.com", "password123")

    assert result == mock_user
    mock_user_repository.find_by_email.assert_called_once_with("test@example.com")


def test_authenticate_user_wrong_password(auth_service, mock_user_repository, mock_user):
    """Test authentication with wrong password."""
    mock_user_repository.find_by_email.return_value = mock_user

    result = auth_service.authenticate_user("test@example.com", "wrongpassword")

    assert result is None


def test_authenticate_user_not_found(auth_service, mock_user_repository):
    """Test authentication with non-existent user."""
    mock_user_repository.find_by_email.return_value = None

    result = auth_service.authenticate_user("nonexistent@example.com", "password123")

    assert result is None


def test_authenticate_user_inactive(auth_service, mock_user_repository, mock_user):
    """Test authentication with inactive user."""
    mock_user.is_active = False
    mock_user_repository.find_by_email.return_value = mock_user

    result = auth_service.authenticate_user("test@example.com", "password123")

    assert result is None


def test_authenticate_user_no_repository(auth_service):
    """Test authentication without repository raises error."""
    auth_service.user_repository = None

    with pytest.raises(ValueError, match="UserRepository is required"):
        auth_service.authenticate_user("test@example.com", "password123")


def test_get_user_by_email_success(auth_service, mock_user_repository, mock_user):
    """Test getting user by email."""
    mock_user_repository.find_by_email.return_value = mock_user

    result = auth_service.get_user_by_email("test@example.com")

    assert result == mock_user
    mock_user_repository.find_by_email.assert_called_once_with("test@example.com")


def test_get_user_by_email_no_repository(auth_service):
    """Test getting user by email without repository raises error."""
    auth_service.user_repository = None

    with pytest.raises(ValueError, match="UserRepository is required"):
        auth_service.get_user_by_email("test@example.com")


def test_get_user_by_uuid_success(auth_service, mock_user_repository, mock_user):
    """Test getting user by UUID."""
    user_uuid = mock_user.uuid
    mock_user_repository.find_by_uuid.return_value = mock_user

    result = auth_service.get_user_by_uuid(str(user_uuid))

    assert result == mock_user
    mock_user_repository.find_by_uuid.assert_called_once()


def test_get_user_by_google_id_success(auth_service, mock_user_repository, mock_user):
    """Test getting user by Google ID."""
    mock_user.google_id = "google123"
    mock_user_repository.find_by_google_id.return_value = mock_user

    result = auth_service.get_user_by_google_id("google123")

    assert result == mock_user
    mock_user_repository.find_by_google_id.assert_called_once_with("google123")


def test_generate_token(auth_service):
    """Test secure token generation."""
    token = AuthService.generate_token()

    assert isinstance(token, str)
    assert len(token) > 0
    # Generate another token and verify they're different
    token2 = AuthService.generate_token()
    assert token != token2


def test_hash_token(auth_service):
    """Test token hashing."""
    token = "test-token-123"

    hashed = AuthService.hash_token(token)

    assert hashed != token
    assert isinstance(hashed, str)
    assert len(hashed) > 0


def test_verify_token_hash_success(auth_service):
    """Test token hash verification with correct token."""
    token = "test-token-123"
    hashed = AuthService.hash_token(token)

    result = AuthService.verify_token_hash(token, hashed)

    assert result is True


def test_verify_token_hash_failure(auth_service):
    """Test token hash verification with incorrect token."""
    token = "test-token-123"
    wrong_token = "wrong-token"
    hashed = AuthService.hash_token(token)

    result = AuthService.verify_token_hash(wrong_token, hashed)

    assert result is False


def test_get_token_by_hash_success(auth_service, mock_token_repository):
    """Test getting token by hash."""
    from app.auth.infra.token_model import Token

    plain_token = "test-token-123"
    token_hash = AuthService.hash_token(plain_token)

    mock_token = MagicMock(spec=Token)
    mock_token.token_hash = token_hash
    mock_token_repository.find_active_tokens.return_value = [mock_token]

    result = auth_service.get_token_by_hash(plain_token)

    assert result == mock_token
    mock_token_repository.update_last_used.assert_called_once_with(mock_token)


def test_get_token_by_hash_not_found(auth_service, mock_token_repository):
    """Test getting token by hash when token doesn't exist."""
    plain_token = "test-token-123"
    mock_token_repository.find_active_tokens.return_value = []

    result = auth_service.get_token_by_hash(plain_token)

    assert result is None


def test_get_token_by_hash_no_repository(auth_service):
    """Test getting token by hash without repository raises error."""
    auth_service.token_repository = None

    with pytest.raises(ValueError, match="TokenRepository is required"):
        auth_service.get_token_by_hash("test-token-123")

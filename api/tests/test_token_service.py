"""Tests for TokenService."""
import pytest
from uuid import uuid4
from unittest.mock import MagicMock, patch
from datetime import datetime, timezone, timedelta
from app.auth.core.token_service import TokenService
from app.auth.infra.token_repository import TokenRepository
from app.auth.api.token_dto import TokenCreate, TokenUpdate
from app.auth.core.token_validators import TokenNotFoundError
from app.auth.infra.token_model import TokenRole


@pytest.fixture
def mock_repository():
    """Create a mock TokenRepository."""
    return MagicMock(spec=TokenRepository)


@pytest.fixture
def mock_db():
    """Create a mock database session."""
    return MagicMock()


@pytest.fixture
def token_service(mock_repository, mock_db):
    """Create TokenService instance."""
    return TokenService(mock_repository, mock_db)


@pytest.fixture
def mock_token():
    """Create a mock token."""
    from datetime import datetime, timezone

    token = MagicMock()
    token.uuid = uuid4()
    token.id = 1
    token.name = "test-token"
    token.token_hash = "hashed_token"
    token.role = TokenRole.ADMIN.value
    token.is_active = True
    token.expires_at = datetime.now(timezone.utc) + timedelta(days=30)
    token.last_used_at = None
    token.created_at = datetime.now(timezone.utc)
    token.updated_at = datetime.now(timezone.utc)
    token.user_id = None
    return token


def test_list_tokens_success(token_service, mock_repository, mock_token):
    """Test successful token listing."""
    mock_token2 = MagicMock()
    mock_token2.uuid = uuid4()
    mock_token2.name = "test-token-2"
    mock_token2.token_hash = "hashed_token_2"
    mock_token2.role = TokenRole.USER.value
    mock_token2.is_active = True
    mock_token2.expires_at = None
    mock_token2.last_used_at = None
    mock_token2.created_at = datetime.now(timezone.utc)
    mock_token2.updated_at = datetime.now(timezone.utc)
    mock_token2.user_id = None

    mock_repository.find_all.return_value = [mock_token, mock_token2]

    result = token_service.list_tokens(skip=0, limit=10)

    assert len(result) == 2
    mock_repository.find_all.assert_called_once_with(skip=0, limit=10, search=None)


def test_list_tokens_with_search(token_service, mock_repository, mock_token):
    """Test token listing with search."""
    mock_repository.find_all.return_value = [mock_token]

    result = token_service.list_tokens(skip=0, limit=10, search="test")

    assert len(result) == 1
    mock_repository.find_all.assert_called_once_with(skip=0, limit=10, search="test")


def test_get_token_success(token_service, mock_repository, mock_token):
    """Test getting token by UUID."""
    token_uuid = str(mock_token.uuid)
    mock_repository.find_by_uuid.return_value = mock_token

    with patch.object(token_service, '_serialize_token') as mock_serialize:
        mock_response = MagicMock()
        mock_serialize.return_value = mock_response

        result = token_service.get_token(token_uuid)

        assert result == mock_response
        # Validator also calls find_by_uuid
        assert mock_repository.find_by_uuid.call_count >= 1
        mock_serialize.assert_called_once_with(mock_token)


def test_get_token_not_found(token_service, mock_repository):
    """Test getting non-existent token."""
    token_uuid = str(uuid4())
    mock_repository.find_by_uuid.return_value = None

    with pytest.raises(TokenNotFoundError):
        token_service.get_token(token_uuid)


def test_create_token_success(token_service, mock_repository, mock_db, mock_token):
    """Test successful token creation."""
    dto = TokenCreate(
        name="new-token",
        role=TokenRole.ADMIN.value,
        expires_at=None
    )

    mock_repository.create.return_value = mock_token

    with patch.object(token_service, '_build_token_entity', return_value=mock_token), \
         patch('app.auth.core.token_service.AuthService.generate_token', return_value="plain-token-123"), \
         patch('app.auth.core.token_service.AuthService.hash_token', return_value="hashed-token-123"):

        result = token_service.create_token(dto)

        assert result.uuid == str(mock_token.uuid)
        assert result.name == mock_token.name
        assert result.token == "plain-token-123"
        assert result.role == mock_token.role
        mock_repository.create.assert_called_once()


def test_create_token_with_user_id(token_service, mock_repository, mock_db, mock_token):
    """Test token creation with user_id."""
    dto = TokenCreate(
        name="user-token",
        role=TokenRole.USER.value,
        expires_at=None
    )
    user_id = 1

    mock_repository.create.return_value = mock_token

    with patch.object(token_service, '_build_token_entity', return_value=mock_token), \
         patch('app.auth.core.token_service.AuthService.generate_token', return_value="plain-token-123"), \
         patch('app.auth.core.token_service.AuthService.hash_token', return_value="hashed-token-123"):

        result = token_service.create_token(dto, user_id=user_id)

        assert result.token == "plain-token-123"
        mock_repository.create.assert_called_once()


def test_update_token_success(token_service, mock_repository, mock_db, mock_token):
    """Test successful token update."""
    token_uuid = str(mock_token.uuid)
    dto = TokenUpdate(
        name="updated-token",
        role=TokenRole.USER.value,
        is_active=False
    )

    mock_repository.find_by_uuid.return_value = mock_token

    with patch.object(token_service, '_serialize_token') as mock_serialize:
        mock_response = MagicMock()
        mock_serialize.return_value = mock_response

        result = token_service.update_token(token_uuid, dto)

        assert result == mock_response
        assert mock_token.name == dto.name
        assert mock_token.role == dto.role
        assert mock_token.is_active == dto.is_active
        mock_repository.update.assert_called_once_with(mock_token)


def test_update_token_partial(token_service, mock_repository, mock_db, mock_token):
    """Test partial token update."""
    token_uuid = str(mock_token.uuid)
    dto = TokenUpdate(name="updated-name")  # Only update name

    mock_repository.find_by_uuid.return_value = mock_token

    with patch.object(token_service, '_serialize_token') as mock_serialize:
        mock_response = MagicMock()
        mock_serialize.return_value = mock_response

        result = token_service.update_token(token_uuid, dto)

        assert result == mock_response
        assert mock_token.name == dto.name
        mock_repository.update.assert_called_once()


def test_update_token_not_found(token_service, mock_repository, mock_db):
    """Test updating non-existent token."""
    token_uuid = str(uuid4())
    dto = TokenUpdate(name="updated-token")

    mock_repository.find_by_uuid.return_value = None

    with pytest.raises(TokenNotFoundError):
        token_service.update_token(token_uuid, dto)


def test_delete_token_success(token_service, mock_repository, mock_db, mock_token):
    """Test successful token deletion."""
    token_uuid = str(mock_token.uuid)
    mock_repository.find_by_uuid.return_value = mock_token

    result = token_service.delete_token(token_uuid)

    assert result == {"detail": "Token deleted successfully"}
    # Validator also calls find_by_uuid
    assert mock_repository.find_by_uuid.call_count >= 1
    mock_repository.delete.assert_called_once_with(mock_token)


def test_delete_token_not_found(token_service, mock_repository, mock_db):
    """Test deleting non-existent token."""
    token_uuid = str(uuid4())
    mock_repository.find_by_uuid.return_value = None

    with pytest.raises(TokenNotFoundError):
        token_service.delete_token(token_uuid)

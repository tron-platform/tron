"""Validation logic for tokens."""
from uuid import UUID
from app.auth.infra.token_repository import TokenRepository
from app.auth.infra.token_model import Token as TokenModel


class TokenNotFoundError(Exception):
    """Token not found."""
    pass


def validate_token_exists(repository: TokenRepository, token_uuid: str) -> None:
    """Validate that token exists."""
    token = repository.find_by_uuid(token_uuid)
    if not token:
        raise TokenNotFoundError(f"Token with UUID {token_uuid} not found")

"""Business logic for tokens. Broken into small, focused functions."""
from uuid import UUID
from typing import List, Optional
from sqlalchemy.orm import Session
from datetime import datetime

from app.auth.infra.token_repository import TokenRepository
from app.auth.infra.token_model import Token as TokenModel
from app.auth.api.token_dto import TokenCreate, TokenUpdate, TokenResponse, TokenCreateResponse
from app.auth.core.token_validators import validate_token_exists, TokenNotFoundError
from app.auth.core.auth_service import AuthService


class TokenService:
    """Business logic for tokens. No direct database access."""

    def __init__(self, repository: TokenRepository, database_session: Session):
        self.repository = repository
        self.db = database_session

    def list_tokens(self, skip: int = 0, limit: int = 100, search: Optional[str] = None) -> List[TokenResponse]:
        """List all tokens with optional search."""
        tokens = self.repository.find_all(skip=skip, limit=limit, search=search)
        return [self._serialize_token(t) for t in tokens]

    def get_token(self, token_uuid: str) -> TokenResponse:
        """Get token by UUID."""
        validate_token_exists(self.repository, token_uuid)
        token = self.repository.find_by_uuid(token_uuid)
        return self._serialize_token(token)

    def create_token(self, dto: TokenCreate, user_id: Optional[int] = None) -> TokenCreateResponse:
        """Create a new token."""
        # Gerar token aleatório
        plain_token = AuthService.generate_token()
        token_hash = AuthService.hash_token(plain_token)

        # Criar token no banco
        token = self._build_token_entity(dto, token_hash, user_id)
        token = self.repository.create(token)

        # Retornar resposta com o token em texto plano (só aparece na criação)
        return TokenCreateResponse(
            uuid=str(token.uuid),
            name=token.name,
            token=plain_token,  # Token em texto plano - só aparece aqui
            role=token.role,
            expires_at=token.expires_at.isoformat() if token.expires_at else None,
            created_at=token.created_at.isoformat()
        )

    def update_token(self, token_uuid: str, dto: TokenUpdate) -> TokenResponse:
        """Update an existing token."""
        validate_token_exists(self.repository, token_uuid)
        token = self.repository.find_by_uuid(token_uuid)

        self._update_token_fields(token, dto)
        self.repository.update(token)

        return self._serialize_token(token)

    def delete_token(self, token_uuid: str) -> dict:
        """Delete a token."""
        validate_token_exists(self.repository, token_uuid)
        token = self.repository.find_by_uuid(token_uuid)
        self.repository.delete(token)
        return {"detail": "Token deleted successfully"}

    def _build_token_entity(
        self,
        dto: TokenCreate,
        token_hash: str,
        user_id: Optional[int]
    ) -> TokenModel:
        """Build token entity from DTO."""
        return TokenModel(
            name=dto.name,
            token_hash=token_hash,
            role=dto.role,
            expires_at=dto.expires_at,
            user_id=user_id
        )

    def _update_token_fields(self, token: TokenModel, dto: TokenUpdate) -> None:
        """Update token fields from DTO."""
        if dto.name is not None:
            token.name = dto.name
        if dto.role is not None:
            token.role = dto.role
        if dto.is_active is not None:
            token.is_active = dto.is_active
        if dto.expires_at is not None:
            token.expires_at = dto.expires_at

    def _serialize_token(self, token: TokenModel) -> TokenResponse:
        """Serialize token to DTO."""
        return TokenResponse.model_validate(token)

from sqlalchemy.orm import Session
from typing import Optional, List
from uuid import UUID
from app.auth.infra.token_model import Token as TokenModel
from datetime import datetime, timezone


class TokenRepository:
    """Repository for Token database operations. No business logic here."""

    def __init__(self, database_session: Session):
        self.db = database_session

    def find_all(self, skip: int = 0, limit: int = 100, search: Optional[str] = None) -> List[TokenModel]:
        """Find all tokens with optional search."""
        query = self.db.query(TokenModel)

        if search:
            search_term = f"%{search}%"
            query = query.filter(TokenModel.name.ilike(search_term))

        return query.order_by(TokenModel.created_at.desc()).offset(skip).limit(limit).all()

    def find_by_uuid(self, token_uuid: str) -> Optional[TokenModel]:
        """Find token by UUID."""
        return self.db.query(TokenModel).filter(TokenModel.uuid == UUID(token_uuid)).first()

    def find_active_tokens(self) -> List[TokenModel]:
        """Find all active tokens."""
        return self.db.query(TokenModel).filter(TokenModel.is_active == True).all()

    def create(self, token: TokenModel) -> TokenModel:
        """Create a new token."""
        self.db.add(token)
        self.db.commit()
        self.db.refresh(token)
        return token

    def update(self, token: TokenModel) -> TokenModel:
        """Update a token."""
        self.db.commit()
        self.db.refresh(token)
        return token

    def delete(self, token: TokenModel) -> None:
        """Delete a token."""
        self.db.delete(token)
        self.db.commit()

    def update_last_used(self, token: TokenModel) -> None:
        """Update token last_used_at timestamp."""
        token.last_used_at = datetime.now(timezone.utc)
        self.db.commit()

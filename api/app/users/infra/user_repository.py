from sqlalchemy.orm import Session
from uuid import UUID
from typing import Optional, List
from app.users.infra.user_model import User as UserModel


class UserRepository:
    """Repository for User database operations. No business logic here."""

    def __init__(self, database_session: Session):
        self.db = database_session

    def find_by_uuid(self, uuid: UUID) -> Optional[UserModel]:
        """Find user by UUID."""
        return self.db.query(UserModel).filter(UserModel.uuid == uuid).first()

    def find_by_email(self, email: str) -> Optional[UserModel]:
        """Find user by email."""
        return self.db.query(UserModel).filter(UserModel.email == email).first()

    def find_by_google_id(self, google_id: str) -> Optional[UserModel]:
        """Find user by Google ID."""
        return self.db.query(UserModel).filter(UserModel.google_id == google_id).first()

    def find_all(
        self,
        skip: int = 0,
        limit: int = 100,
        search: Optional[str] = None
    ) -> List[UserModel]:
        """Find all users, optionally filtered by search term."""
        query = self.db.query(UserModel)

        if search:
            search_term = f"%{search}%"
            query = query.filter(
                (UserModel.email.ilike(search_term)) |
                (UserModel.full_name.ilike(search_term))
            )

        return query.order_by(UserModel.created_at.desc()).offset(skip).limit(limit).all()

    def create(self, user: UserModel) -> UserModel:
        """Create a new user."""
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user

    def update(self, user: UserModel) -> UserModel:
        """Update an existing user."""
        self.db.commit()
        self.db.refresh(user)
        return user

    def delete(self, user: UserModel) -> None:
        """Delete a user."""
        self.db.delete(user)
        self.db.commit()

    def rollback(self) -> None:
        """Rollback current transaction."""
        self.db.rollback()

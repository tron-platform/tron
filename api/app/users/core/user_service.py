from uuid import uuid4, UUID
from typing import List, Optional
from app.users.infra.user_repository import UserRepository
from app.users.infra.user_model import User as UserModel, UserRole
from app.users.api.user_dto import UserCreate, UserUpdate, UserResponse
from app.users.core.user_validators import (
    validate_user_create_dto,
    validate_user_update_dto,
    validate_user_exists,
    validate_user_email_uniqueness,
    validate_can_delete_user,
    UserNotFoundError,
    UserEmailAlreadyExistsError,
    CannotDeleteSelfError
)
from app.auth.core.auth_service import AuthService


class UserService:
    """Business logic for users. No direct database access."""

    def __init__(self, repository: UserRepository, auth_service: AuthService):
        self.repository = repository
        self.auth_service = auth_service

    def create_user(self, dto: UserCreate) -> UserResponse:
        """Create a new user."""
        validate_user_create_dto(dto)
        validate_user_email_uniqueness(self.repository, dto.email)

        hashed_password = self.auth_service.get_password_hash(dto.password)
        user = self._build_user_entity(dto, hashed_password)

        return self.repository.create(user)

    def update_user(self, uuid: UUID, dto: UserUpdate) -> UserResponse:
        """Update an existing user."""
        validate_user_update_dto(dto)
        validate_user_exists(self.repository, uuid)

        user = self.repository.find_by_uuid(uuid)

        if dto.email is not None:
            validate_user_email_uniqueness(self.repository, dto.email, exclude_uuid=uuid)
            user.email = dto.email

        if dto.full_name is not None:
            user.full_name = dto.full_name

        if dto.is_active is not None:
            user.is_active = dto.is_active

        if dto.role is not None:
            user.role = dto.role

        if dto.password is not None:
            user.hashed_password = self.auth_service.get_password_hash(dto.password)

        return self.repository.update(user)

    def get_user(self, uuid: UUID) -> UserResponse:
        """Get user by UUID."""
        validate_user_exists(self.repository, uuid)
        return self.repository.find_by_uuid(uuid)

    def get_users(
        self,
        skip: int = 0,
        limit: int = 100,
        search: Optional[str] = None
    ) -> List[UserResponse]:
        """Get all users, optionally filtered by search term."""
        return self.repository.find_all(skip=skip, limit=limit, search=search)

    def delete_user(self, uuid: UUID, current_user_uuid: UUID) -> None:
        """Delete a user."""
        validate_user_exists(self.repository, uuid)
        validate_can_delete_user(self.repository, uuid, current_user_uuid)

        user = self.repository.find_by_uuid(uuid)
        self.repository.delete(user)

    def _build_user_entity(self, dto: UserCreate, hashed_password: str) -> UserModel:
        """Build User entity from DTO."""
        return UserModel(
            email=dto.email,
            hashed_password=hashed_password,
            full_name=dto.full_name,
            role=UserRole.USER.value
        )

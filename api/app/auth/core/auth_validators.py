from app.users.infra.user_repository import UserRepository
from app.auth.api.auth_dto import LoginRequest, UpdateProfileRequest


class InvalidCredentialsError(Exception):
    """Raised when credentials are invalid."""
    pass


class UserInactiveError(Exception):
    """Raised when user is inactive."""
    pass


class EmailAlreadyExistsError(Exception):
    """Raised when email already exists."""
    pass


class InvalidCurrentPasswordError(Exception):
    """Raised when current password is incorrect."""
    pass


def validate_login_request(dto: LoginRequest) -> None:
    """Validate login request. Raises ValueError if validation fails."""
    if not dto.email or not dto.email.strip():
        raise ValueError("Email is required")

    if not dto.password:
        raise ValueError("Password is required")


def validate_update_profile_request(
    dto: UpdateProfileRequest,
    repository: UserRepository,
    current_user_email: str
) -> None:
    """Validate update profile request."""
    if dto.email and dto.email != current_user_email:
        existing_user = repository.find_by_email(dto.email)
        if existing_user:
            raise EmailAlreadyExistsError("Email already registered")

    if dto.password and not dto.current_password:
        raise ValueError("Current password is required to change password")


def validate_current_password(
    repository: UserRepository,
    user_uuid: str,
    current_password: str
) -> None:
    """Validate current password."""
    from uuid import UUID as UUIDType
    from app.auth.core.auth_service import AuthService

    user = repository.find_by_uuid(UUIDType(user_uuid))
    if not user or not user.hashed_password:
        raise InvalidCurrentPasswordError("Invalid current password")

    if not AuthService.verify_password(current_password, user.hashed_password):
        raise InvalidCurrentPasswordError("Current password is incorrect")

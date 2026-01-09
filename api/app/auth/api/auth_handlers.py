from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.shared.database.database import get_db
from app.users.infra.user_repository import UserRepository
from app.auth.infra.token_repository import TokenRepository
from app.auth.core.auth_service import AuthService
from app.auth.api.auth_dto import (
    Token,
    LoginRequest,
    RefreshTokenRequest,
    UpdateProfileRequest
)
from app.users.api.user_dto import UserResponse, UserCreate
from app.users.core.user_validators import UserEmailAlreadyExistsError
from app.users.infra.user_model import User, UserRole
from app.shared.dependencies.auth import get_current_user
from app.auth.core.auth_validators import (
    validate_login_request,
    validate_update_profile_request,
    validate_current_password,
    InvalidCredentialsError,
    InvalidCurrentPasswordError,
    EmailAlreadyExistsError
)


router = APIRouter(prefix="/auth", tags=["auth"])


def get_auth_service(database_session: Session = Depends(get_db)) -> AuthService:
    """Dependency to get AuthService instance."""
    user_repository = UserRepository(database_session)
    token_repository = TokenRepository(database_session)
    return AuthService(user_repository, token_repository)


@router.post("/login", response_model=Token)
async def login(
    login_data: LoginRequest,
    service: AuthService = Depends(get_auth_service)
):
    """Login with email and password."""
    try:
        validate_login_request(login_data)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    user = service.authenticate_user(login_data.email, login_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email ou senha incorretos"
        )

    access_token = service.create_access_token(data={"sub": str(user.uuid)})
    refresh_token = service.create_refresh_token(data={"sub": str(user.uuid)})

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }


@router.post("/login/form", response_model=Token)
async def login_form(
    form_data: OAuth2PasswordRequestForm = Depends(),
    service: AuthService = Depends(get_auth_service)
):
    """Alternative login endpoint for OAuth2PasswordRequestForm compatibility."""
    user = service.authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email ou senha incorretos"
        )

    access_token = service.create_access_token(data={"sub": str(user.uuid)})
    refresh_token = service.create_refresh_token(data={"sub": str(user.uuid)})

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserCreate,
    database_session: Session = Depends(get_db),
    service: AuthService = Depends(get_auth_service)
):
    """Register a new user."""
    from app.users.core.user_service import UserService

    try:
        user_service = UserService(UserRepository(database_session), service)
        return user_service.create_user(user_data)
    except UserEmailAlreadyExistsError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/refresh", response_model=Token)
async def refresh_token(
    token_data: RefreshTokenRequest,
    service: AuthService = Depends(get_auth_service)
):
    """Refresh access token."""
    payload = service.verify_token(token_data.refresh_token)
    if payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido"
        )

    user_uuid = payload.get("sub")
    user = service.get_user_by_uuid(user_uuid)
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuário não encontrado ou inativo"
        )

    access_token = service.create_access_token(data={"sub": str(user.uuid)})
    refresh_token = service.create_refresh_token(data={"sub": str(user.uuid)})

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_user)
):
    """Get current user information."""
    return current_user


@router.put("/me", response_model=UserResponse)
async def update_profile(
    profile_data: UpdateProfileRequest,
    current_user: User = Depends(get_current_user),
    database_session: Session = Depends(get_db),
    service: AuthService = Depends(get_auth_service)
):
    """Update current user profile."""
    user_repository = UserRepository(database_session)

    try:
        validate_update_profile_request(profile_data, user_repository, current_user.email)
    except (EmailAlreadyExistsError, ValueError) as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    # Update email if provided
    if profile_data.email and profile_data.email != current_user.email:
        current_user.email = profile_data.email

    # Update password if provided
    if profile_data.password:
        try:
            validate_current_password(user_repository, str(current_user.uuid), profile_data.current_password)
        except InvalidCurrentPasswordError as e:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))

        current_user.hashed_password = service.get_password_hash(profile_data.password)

    # Update full name if provided
    if profile_data.full_name is not None:
        current_user.full_name = profile_data.full_name

    user_repository.update(current_user)
    return current_user


@router.get("/google/login")
async def google_login():
    """Endpoint to initiate Google login."""
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Login com Google será implementado em breve"
    )

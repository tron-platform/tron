from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID

from app.shared.database.database import get_db
from app.users.infra.user_repository import UserRepository
from app.users.core.user_service import UserService
from app.users.api.user_dto import UserCreate, UserUpdate, UserResponse
from app.users.core.user_validators import (
    UserNotFoundError,
    UserEmailAlreadyExistsError,
    CannotDeleteSelfError
)
from app.users.infra.user_model import UserRole
from app.users.infra.user_model import User
from app.shared.dependencies.auth import require_role, get_current_user
from app.auth.core.auth_service import AuthService


router = APIRouter(prefix="/users", tags=["users"])


def get_user_service(database_session: Session = Depends(get_db)) -> UserService:
    """Dependency to get UserService instance."""
    user_repository = UserRepository(database_session)
    auth_service = AuthService()
    return UserService(user_repository, auth_service)


@router.get("", response_model=List[UserResponse])
async def list_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    search: Optional[str] = Query(None),
    service: UserService = Depends(get_user_service),
    current_user: User = Depends(require_role([UserRole.ADMIN]))
):
    """List all users (admin only)."""
    return service.get_users(skip=skip, limit=limit, search=search)


@router.get("/{user_uuid}", response_model=UserResponse)
async def get_user(
    user_uuid: UUID,
    service: UserService = Depends(get_user_service),
    current_user: User = Depends(require_role([UserRole.ADMIN]))
):
    """Get user by UUID (admin only)."""
    try:
        return service.get_user(user_uuid)
    except UserNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    user_data: UserCreate,
    service: UserService = Depends(get_user_service),
    current_user: User = Depends(require_role([UserRole.ADMIN]))
):
    """Create a new user (admin only)."""
    try:
        return service.create_user(user_data)
    except UserEmailAlreadyExistsError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.put("/{user_uuid}", response_model=UserResponse)
async def update_user(
    user_uuid: UUID,
    user_data: UserUpdate,
    service: UserService = Depends(get_user_service),
    current_user: User = Depends(require_role([UserRole.ADMIN]))
):
    """Update a user (admin only)."""
    try:
        return service.update_user(user_uuid, user_data)
    except UserNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except UserEmailAlreadyExistsError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.delete("/{user_uuid}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_uuid: UUID,
    service: UserService = Depends(get_user_service),
    current_user: User = Depends(require_role([UserRole.ADMIN]))
):
    """Delete a user (admin only)."""
    try:
        service.delete_user(user_uuid, current_user.uuid)
    except UserNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except CannotDeleteSelfError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

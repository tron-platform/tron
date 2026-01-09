from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from uuid import UUID

from app.shared.database.database import get_db
from app.environments.infra.environment_repository import EnvironmentRepository
from app.environments.core.environment_service import EnvironmentService
from app.environments.api.environment_dto import (
    EnvironmentCreate,
    Environment,
    EnvironmentWithClusters
)
from app.environments.core.environment_validators import (
    EnvironmentNotFoundError,
    EnvironmentHasComponentsError
)
from app.users.infra.user_model import User, UserRole
from app.shared.dependencies.auth import require_role, get_current_user


router = APIRouter()


def get_environment_service(database_session: Session = Depends(get_db)) -> EnvironmentService:
    """Dependency to get EnvironmentService instance."""
    environment_repository = EnvironmentRepository(database_session)
    return EnvironmentService(environment_repository)


@router.post("/environments/", response_model=Environment)
def create_environment(
    environment: EnvironmentCreate,
    service: EnvironmentService = Depends(get_environment_service),
    current_user: User = Depends(require_role([UserRole.ADMIN]))
):
    """Create a new environment."""
    try:
        return service.create_environment(environment)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/environments/{uuid}", response_model=Environment)
def update_environment(
    uuid: UUID,
    environment: EnvironmentCreate,
    service: EnvironmentService = Depends(get_environment_service),
    current_user: User = Depends(require_role([UserRole.ADMIN]))
):
    """Update an existing environment."""
    try:
        return service.update_environment(uuid, environment)
    except EnvironmentNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/environments/", response_model=list[EnvironmentWithClusters])
def list_environments(
    skip: int = 0,
    limit: int = 100,
    service: EnvironmentService = Depends(get_environment_service),
    current_user: User = Depends(get_current_user)
):
    """List all environments."""
    return service.get_environments(skip=skip, limit=limit)


@router.get("/environments/{uuid}", response_model=EnvironmentWithClusters)
def get_environment(
    uuid: UUID,
    service: EnvironmentService = Depends(get_environment_service),
    current_user: User = Depends(get_current_user)
):
    """Get environment by UUID."""
    try:
        return service.get_environment(uuid)
    except EnvironmentNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/environments/{uuid}", response_model=dict)
def delete_environment(
    uuid: UUID,
    service: EnvironmentService = Depends(get_environment_service),
    current_user: User = Depends(require_role([UserRole.ADMIN]))
):
    """Delete an environment."""
    try:
        return service.delete_environment(uuid)
    except EnvironmentNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except EnvironmentHasComponentsError as e:
        raise HTTPException(status_code=400, detail=str(e))

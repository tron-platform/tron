from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from uuid import UUID

from app.shared.database.database import get_db
from app.applications.infra.application_repository import ApplicationRepository
from app.applications.core.application_service import ApplicationService
from app.applications.api.application_dto import ApplicationCreate, ApplicationUpdate, Application
from app.applications.core.application_validators import (
    ApplicationNotFoundError,
    ApplicationNameAlreadyExistsError
)
from app.users.infra.user_model import User, UserRole
from app.shared.dependencies.auth import require_role, get_current_user


router = APIRouter()


def get_application_service(database_session: Session = Depends(get_db)) -> ApplicationService:
    """Dependency to get ApplicationService instance."""
    from app.instances.infra.instance_repository import InstanceRepository
    from app.instances.core.instance_service import InstanceService

    application_repository = ApplicationRepository(database_session)
    instance_repository = InstanceRepository(database_session)
    instance_service = InstanceService(instance_repository)
    return ApplicationService(application_repository, instance_service)


@router.post("/applications/", response_model=Application)
def create_application(
    application: ApplicationCreate,
    service: ApplicationService = Depends(get_application_service),
    current_user: User = Depends(require_role([UserRole.ADMIN]))
):
    """Create a new application."""
    try:
        return service.create_application(application)
    except ApplicationNameAlreadyExistsError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/applications/{uuid}", response_model=Application)
def update_application(
    uuid: UUID,
    application: ApplicationUpdate,
    service: ApplicationService = Depends(get_application_service),
    current_user: User = Depends(require_role([UserRole.ADMIN]))
):
    """Update an existing application."""
    try:
        return service.update_application(uuid, application)
    except ApplicationNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ApplicationNameAlreadyExistsError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/applications/", response_model=list[Application])
def list_applications(
    skip: int = 0,
    limit: int = 100,
    service: ApplicationService = Depends(get_application_service),
    current_user: User = Depends(get_current_user)
):
    """List all applications."""
    return service.get_applications(skip=skip, limit=limit)


@router.get("/applications/{uuid}", response_model=Application)
def get_application(
    uuid: UUID,
    service: ApplicationService = Depends(get_application_service),
    current_user: User = Depends(get_current_user)
):
    """Get application by UUID."""
    try:
        return service.get_application(uuid)
    except ApplicationNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/applications/{uuid}", response_model=dict)
def delete_application(
    uuid: UUID,
    service: ApplicationService = Depends(get_application_service),
    database_session: Session = Depends(get_db),
    current_user: User = Depends(require_role([UserRole.ADMIN]))
):
    """Delete an application."""
    try:
        return service.delete_application(uuid, database_session)
    except ApplicationNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

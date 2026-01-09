from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from uuid import UUID
from typing import List

from app.shared.database.database import get_db
from app.instances.infra.instance_repository import InstanceRepository
from app.instances.core.instance_service import InstanceService
from app.instances.api.instance_dto import (
    InstanceCreate,
    InstanceUpdate,
    Instance,
    KubernetesEvent
)
from app.instances.core.instance_validators import (
    InstanceNotFoundError,
    InstanceAlreadyExistsError,
    ApplicationNotFoundError,
    EnvironmentNotFoundError
)
from app.users.infra.user_model import User, UserRole
from app.shared.dependencies.auth import require_role, get_current_user


router = APIRouter()


def get_instance_service(database_session: Session = Depends(get_db)) -> InstanceService:
    """Dependency to get InstanceService instance."""
    instance_repository = InstanceRepository(database_session)
    return InstanceService(instance_repository, database_session)


@router.post("/instances/", response_model=Instance)
def create_instance(
    instance: InstanceCreate,
    service: InstanceService = Depends(get_instance_service),
    current_user: User = Depends(require_role([UserRole.ADMIN]))
):
    """Create a new instance."""
    try:
        return service.create_instance(instance)
    except (ApplicationNotFoundError, EnvironmentNotFoundError) as e:
        raise HTTPException(status_code=404, detail=str(e))
    except InstanceAlreadyExistsError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/instances/{uuid}", response_model=Instance)
def update_instance(
    uuid: UUID,
    instance: InstanceUpdate,
    service: InstanceService = Depends(get_instance_service),
    current_user: User = Depends(require_role([UserRole.ADMIN]))
):
    """Update an existing instance."""
    try:
        return service.update_instance(uuid, instance)
    except InstanceNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/instances/", response_model=List[Instance])
def list_instances(
    skip: int = 0,
    limit: int = 100,
    service: InstanceService = Depends(get_instance_service),
    current_user: User = Depends(get_current_user)
):
    """List all instances."""
    return service.get_instances(skip=skip, limit=limit)


@router.get("/instances/{uuid}", response_model=Instance)
def get_instance(
    uuid: UUID,
    service: InstanceService = Depends(get_instance_service),
    current_user: User = Depends(get_current_user)
):
    """Get instance by UUID."""
    try:
        return service.get_instance(uuid)
    except InstanceNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/instances/{uuid}", response_model=dict)
def delete_instance(
    uuid: UUID,
    service: InstanceService = Depends(get_instance_service),
    database_session: Session = Depends(get_db),
    current_user: User = Depends(require_role([UserRole.ADMIN]))
):
    """Delete an instance."""
    try:
        return service.delete_instance(uuid, database_session)
    except InstanceNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/instances/{uuid}/events", response_model=List[KubernetesEvent])
def get_instance_events(
    uuid: UUID,
    service: InstanceService = Depends(get_instance_service),
    current_user: User = Depends(get_current_user)
):
    """Get Kubernetes events for an instance."""
    try:
        return service.get_instance_events(uuid)
    except InstanceNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except NotImplementedError:
        # TODO: Remove when Kubernetes features are migrated
        raise HTTPException(
            status_code=501,
            detail="Instance events not yet available in new structure. Use old endpoint temporarily."
        )


@router.post("/instances/{uuid}/sync", response_model=dict)
def sync_instance(
    uuid: UUID,
    service: InstanceService = Depends(get_instance_service),
    current_user: User = Depends(require_role([UserRole.ADMIN]))
):
    """Sync instance components with Kubernetes."""
    try:
        return service.sync_instance(uuid)
    except InstanceNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error syncing instance: {str(e)}")

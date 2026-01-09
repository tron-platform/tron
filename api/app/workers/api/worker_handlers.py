from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from uuid import UUID

from app.shared.database.database import get_db
from app.workers.infra.worker_repository import WorkerRepository
from app.workers.core.worker_service import WorkerService
from app.workers.api.worker_dto import WorkerCreate, WorkerUpdate, Worker
from app.workers.core.worker_validators import (
    WorkerNotFoundError,
    WorkerNotWorkerTypeError,
    InstanceNotFoundError
)
from app.users.infra.user_model import UserRole, User
from app.shared.dependencies.auth import require_role, get_current_user


router = APIRouter(prefix="/application_components/worker", tags=["worker"])


def get_worker_service(database_session: Session = Depends(get_db)) -> WorkerService:
    """Dependency to get WorkerService instance."""
    worker_repository = WorkerRepository(database_session)
    return WorkerService(worker_repository, database_session)


@router.post("/", response_model=Worker)
def create_worker(
    worker: WorkerCreate,
    service: WorkerService = Depends(get_worker_service),
    current_user: User = Depends(require_role([UserRole.ADMIN]))
):
    """Create a new worker."""
    try:
        return service.create_worker(worker)
    except (InstanceNotFoundError, ValueError) as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/", response_model=list[Worker])
def list_workers(
    skip: int = 0,
    limit: int = 100,
    service: WorkerService = Depends(get_worker_service),
    current_user: User = Depends(get_current_user)
):
    """List all workers."""
    return service.get_workers(skip=skip, limit=limit)


@router.get("/{uuid}", response_model=Worker)
def get_worker(
    uuid: UUID,
    service: WorkerService = Depends(get_worker_service),
    current_user: User = Depends(get_current_user)
):
    """Get worker by UUID."""
    try:
        return service.get_worker(uuid)
    except (WorkerNotFoundError, WorkerNotWorkerTypeError) as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.put("/{uuid}", response_model=Worker)
def update_worker(
    uuid: UUID,
    worker: WorkerUpdate,
    service: WorkerService = Depends(get_worker_service),
    current_user: User = Depends(require_role([UserRole.ADMIN]))
):
    """Update an existing worker."""
    try:
        return service.update_worker(uuid, worker)
    except (WorkerNotFoundError, WorkerNotWorkerTypeError) as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{uuid}")
def delete_worker(
    uuid: UUID,
    service: WorkerService = Depends(get_worker_service),
    current_user: User = Depends(require_role([UserRole.ADMIN]))
):
    """Delete a worker."""
    try:
        return service.delete_worker(uuid)
    except (WorkerNotFoundError, WorkerNotWorkerTypeError) as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

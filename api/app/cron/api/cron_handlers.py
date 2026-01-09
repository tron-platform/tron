from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from uuid import UUID

from app.shared.database.database import get_db
from app.cron.infra.cron_repository import CronRepository
from app.cron.core.cron_service import CronService
from app.cron.api.cron_dto import CronCreate, CronUpdate, Cron, CronJob, CronJobLogs
from app.cron.core.cron_validators import (
    CronNotFoundError,
    CronNotCronTypeError,
    InstanceNotFoundError
)
from app.cron.core.cron_jobs_service import (
    get_cron_jobs_from_cluster,
    get_cron_job_logs_from_cluster,
    delete_cron_job_from_cluster
)
from app.users.infra.user_model import UserRole, User
from app.shared.dependencies.auth import require_role, get_current_user


router = APIRouter(prefix="/application_components/cron", tags=["cron"])


def get_cron_service(database_session: Session = Depends(get_db)) -> CronService:
    """Dependency to get CronService instance."""
    cron_repository = CronRepository(database_session)
    return CronService(cron_repository, database_session)


@router.post("/", response_model=Cron)
def create_cron(
    cron: CronCreate,
    service: CronService = Depends(get_cron_service),
    current_user: User = Depends(require_role([UserRole.ADMIN]))
):
    """Create a new cron."""
    try:
        return service.create_cron(cron)
    except (InstanceNotFoundError, ValueError) as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/", response_model=list[Cron])
def list_crons(
    skip: int = 0,
    limit: int = 100,
    service: CronService = Depends(get_cron_service),
    current_user: User = Depends(get_current_user)
):
    """List all crons."""
    return service.get_crons(skip=skip, limit=limit)


@router.get("/{uuid}", response_model=Cron)
def get_cron(
    uuid: UUID,
    service: CronService = Depends(get_cron_service),
    current_user: User = Depends(get_current_user)
):
    """Get cron by UUID."""
    try:
        return service.get_cron(uuid)
    except (CronNotFoundError, CronNotCronTypeError) as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.put("/{uuid}", response_model=Cron)
def update_cron(
    uuid: UUID,
    cron: CronUpdate,
    service: CronService = Depends(get_cron_service),
    current_user: User = Depends(require_role([UserRole.ADMIN]))
):
    """Update an existing cron."""
    try:
        return service.update_cron(uuid, cron)
    except (CronNotFoundError, CronNotCronTypeError) as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{uuid}")
def delete_cron(
    uuid: UUID,
    service: CronService = Depends(get_cron_service),
    current_user: User = Depends(require_role([UserRole.ADMIN]))
):
    """Delete a cron."""
    try:
        return service.delete_cron(uuid)
    except (CronNotFoundError, CronNotCronTypeError) as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{uuid}/jobs", response_model=list[CronJob])
def get_cron_jobs(
    uuid: UUID,
    database_session: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get jobs for a cron."""
    repository = CronRepository(database_session)
    cron = repository.find_by_uuid(uuid, load_relations=True)

    if not cron:
        raise HTTPException(status_code=404, detail="Cron not found")

    if cron.type.value != "cron":
        raise HTTPException(status_code=400, detail="Component is not a cron")

    cluster_instance = repository.find_cluster_instance_by_component_id(cron.id)
    if not cluster_instance:
        raise HTTPException(status_code=404, detail="Cron is not deployed to any cluster")

    cluster = cluster_instance.cluster
    application_name = cron.instance.application.name
    component_name = cron.name

    try:
        jobs = get_cron_jobs_from_cluster(cluster, application_name, component_name)
        return jobs
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get jobs: {str(e)}")


@router.get("/{uuid}/jobs/{job_name}/logs", response_model=CronJobLogs)
def get_cron_job_logs(
    uuid: UUID,
    job_name: str,
    container_name: str = None,
    tail_lines: int = 100,
    database_session: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get logs for a cron job."""
    repository = CronRepository(database_session)
    cron = repository.find_by_uuid(uuid, load_relations=True)

    if not cron:
        raise HTTPException(status_code=404, detail="Cron not found")

    if cron.type.value != "cron":
        raise HTTPException(status_code=400, detail="Component is not a cron")

    cluster_instance = repository.find_cluster_instance_by_component_id(cron.id)
    if not cluster_instance:
        raise HTTPException(status_code=404, detail="Cron is not deployed to any cluster")

    cluster = cluster_instance.cluster
    application_name = cron.instance.application.name

    try:
        result = get_cron_job_logs_from_cluster(cluster, application_name, job_name, container_name, tail_lines)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get logs for job {job_name}: {str(e)}")


@router.delete("/{uuid}/jobs/{job_name}")
def delete_cron_job(
    uuid: UUID,
    job_name: str,
    database_session: Session = Depends(get_db),
    current_user: User = Depends(require_role([UserRole.ADMIN]))
):
    """Delete a cron job."""
    repository = CronRepository(database_session)
    cron = repository.find_by_uuid(uuid, load_relations=True)

    if not cron:
        raise HTTPException(status_code=404, detail="Cron not found")

    if cron.type.value != "cron":
        raise HTTPException(status_code=400, detail="Component is not a cron")

    cluster_instance = repository.find_cluster_instance_by_component_id(cron.id)
    if not cluster_instance:
        raise HTTPException(status_code=404, detail="Cron is not deployed to any cluster")

    cluster = cluster_instance.cluster
    application_name = cron.instance.application.name

    try:
        delete_cron_job_from_cluster(cluster, application_name, job_name)
        return {"detail": f"Job '{job_name}' deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete job {job_name}: {str(e)}")

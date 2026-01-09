from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from uuid import UUID

from app.shared.database.database import get_db
from app.webapps.infra.webapp_repository import WebappRepository
from app.webapps.core.webapp_service import WebappService
from app.webapps.api.webapp_dto import (
    WebappCreate,
    WebappUpdate,
    Webapp,
    Pod,
    PodLogs,
    PodCommandRequest,
    PodCommandResponse
)
from app.webapps.core.webapp_validators import (
    WebappNotFoundError,
    WebappNotWebappTypeError,
    InstanceNotFoundError,
    InvalidExposureTypeError,
    InvalidVisibilityError,
    InvalidURLError
)
from app.webapps.core.webapp_pods_service import (
    get_webapp_pods_from_cluster,
    delete_webapp_pod_from_cluster,
    get_webapp_pod_logs_from_cluster,
    exec_webapp_pod_command_from_cluster
)
from app.users.infra.user_model import UserRole, User
from app.shared.dependencies.auth import require_role, get_current_user


router = APIRouter(prefix="/application_components/webapp", tags=["webapp"])


def get_webapp_service(database_session: Session = Depends(get_db)) -> WebappService:
    """Dependency to get WebappService instance."""
    webapp_repository = WebappRepository(database_session)
    return WebappService(webapp_repository, database_session)


@router.post("/", response_model=Webapp)
def create_webapp(
    webapp: WebappCreate,
    service: WebappService = Depends(get_webapp_service),
    current_user: User = Depends(require_role([UserRole.ADMIN]))
):
    """Create a new webapp."""
    try:
        return service.create_webapp(webapp)
    except (InstanceNotFoundError, InvalidExposureTypeError, InvalidVisibilityError, InvalidURLError) as e:
        raise HTTPException(status_code=400, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/", response_model=list[Webapp])
def list_webapps(
    skip: int = 0,
    limit: int = 100,
    service: WebappService = Depends(get_webapp_service),
    current_user: User = Depends(get_current_user)
):
    """List all webapps."""
    return service.get_webapps(skip=skip, limit=limit)


@router.get("/{uuid}", response_model=Webapp)
def get_webapp(
    uuid: UUID,
    service: WebappService = Depends(get_webapp_service),
    current_user: User = Depends(get_current_user)
):
    """Get webapp by UUID."""
    try:
        return service.get_webapp(uuid)
    except (WebappNotFoundError, WebappNotWebappTypeError) as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.put("/{uuid}", response_model=Webapp)
def update_webapp(
    uuid: UUID,
    webapp: WebappUpdate,
    service: WebappService = Depends(get_webapp_service),
    current_user: User = Depends(require_role([UserRole.ADMIN]))
):
    """Update an existing webapp."""
    try:
        return service.update_webapp(uuid, webapp)
    except (WebappNotFoundError, WebappNotWebappTypeError) as e:
        raise HTTPException(status_code=404, detail=str(e))
    except (InvalidURLError, InvalidExposureTypeError, InvalidVisibilityError) as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{uuid}")
def delete_webapp(
    uuid: UUID,
    service: WebappService = Depends(get_webapp_service),
    current_user: User = Depends(require_role([UserRole.ADMIN]))
):
    """Delete a webapp."""
    try:
        return service.delete_webapp(uuid)
    except (WebappNotFoundError, WebappNotWebappTypeError) as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{uuid}/pods", response_model=list[Pod])
def get_webapp_pods(
    uuid: UUID,
    database_session: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get pods for a webapp."""
    repository = WebappRepository(database_session)
    webapp = repository.find_by_uuid(uuid, load_relations=True)

    if not webapp:
        raise HTTPException(status_code=404, detail="Webapp not found")

    if webapp.type.value != "webapp":
        raise HTTPException(status_code=400, detail="Component is not a webapp")

    cluster_instance = repository.find_cluster_instance_by_component_id(webapp.id)
    if not cluster_instance:
        raise HTTPException(status_code=404, detail="Webapp is not deployed to any cluster")

    cluster = cluster_instance.cluster
    application_name = webapp.instance.application.name
    component_name = webapp.name

    try:
        pods = get_webapp_pods_from_cluster(cluster, application_name, component_name)
        return pods
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get pods: {str(e)}")


@router.delete("/{uuid}/pods/{pod_name}")
def delete_webapp_pod(
    uuid: UUID,
    pod_name: str,
    database_session: Session = Depends(get_db),
    current_user: User = Depends(require_role([UserRole.ADMIN]))
):
    """Delete a pod for a webapp."""
    repository = WebappRepository(database_session)
    webapp = repository.find_by_uuid(uuid, load_relations=True)

    if not webapp:
        raise HTTPException(status_code=404, detail="Webapp not found")

    if webapp.type.value != "webapp":
        raise HTTPException(status_code=400, detail="Component is not a webapp")

    cluster_instance = repository.find_cluster_instance_by_component_id(webapp.id)
    if not cluster_instance:
        raise HTTPException(status_code=404, detail="Webapp is not deployed to any cluster")

    cluster = cluster_instance.cluster
    application_name = webapp.instance.application.name

    try:
        delete_webapp_pod_from_cluster(cluster, application_name, pod_name)
        return {"detail": f"Pod {pod_name} deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete pod {pod_name}: {str(e)}")


@router.get("/{uuid}/pods/{pod_name}/logs", response_model=PodLogs)
def get_webapp_pod_logs(
    uuid: UUID,
    pod_name: str,
    container_name: str = None,
    tail_lines: int = 100,
    database_session: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get logs for a pod."""
    repository = WebappRepository(database_session)
    webapp = repository.find_by_uuid(uuid, load_relations=True)

    if not webapp:
        raise HTTPException(status_code=404, detail="Webapp not found")

    if webapp.type.value != "webapp":
        raise HTTPException(status_code=400, detail="Component is not a webapp")

    cluster_instance = repository.find_cluster_instance_by_component_id(webapp.id)
    if not cluster_instance:
        raise HTTPException(status_code=404, detail="Webapp is not deployed to any cluster")

    cluster = cluster_instance.cluster
    application_name = webapp.instance.application.name

    try:
        logs = get_webapp_pod_logs_from_cluster(cluster, application_name, pod_name, container_name, tail_lines)
        return {"logs": logs, "pod_name": pod_name, "container_name": container_name}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get logs for pod {pod_name}: {str(e)}")


@router.post("/{uuid}/pods/{pod_name}/exec", response_model=PodCommandResponse)
def exec_webapp_pod_command(
    uuid: UUID,
    pod_name: str,
    request: PodCommandRequest,
    database_session: Session = Depends(get_db),
    current_user: User = Depends(require_role([UserRole.ADMIN]))
):
    """Execute a command in a pod."""
    repository = WebappRepository(database_session)
    webapp = repository.find_by_uuid(uuid, load_relations=True)

    if not webapp:
        raise HTTPException(status_code=404, detail="Webapp not found")

    if webapp.type.value != "webapp":
        raise HTTPException(status_code=400, detail="Component is not a webapp")

    cluster_instance = repository.find_cluster_instance_by_component_id(webapp.id)
    if not cluster_instance:
        raise HTTPException(status_code=404, detail="Webapp is not deployed to any cluster")

    cluster = cluster_instance.cluster
    application_name = webapp.instance.application.name

    try:
        result = exec_webapp_pod_command_from_cluster(
            cluster,
            application_name,
            pod_name,
            request.command,
            request.container_name
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to execute command in pod {pod_name}: {str(e)}")

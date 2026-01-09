from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from uuid import UUID

from app.shared.database.database import get_db
from app.clusters.infra.cluster_repository import ClusterRepository
from app.clusters.core.cluster_service import ClusterService
from app.clusters.api.cluster_dto import (
    ClusterCreate,
    ClusterResponse,
    ClusterResponseWithValidation,
    ClusterCompletedResponse
)
from app.clusters.core.cluster_validators import (
    ClusterNotFoundError,
    ClusterConnectionError,
    EnvironmentNotFoundError
)
from app.users.infra.user_model import User, UserRole
from app.shared.dependencies.auth import require_role, get_current_user


router = APIRouter()


def get_cluster_service(database_session: Session = Depends(get_db)) -> ClusterService:
    """Dependency to get ClusterService instance."""
    cluster_repository = ClusterRepository(database_session)
    return ClusterService(cluster_repository)


@router.post("/clusters/", response_model=ClusterResponse)
def create_cluster(
    cluster: ClusterCreate,
    service: ClusterService = Depends(get_cluster_service),
    current_user: User = Depends(require_role([UserRole.ADMIN]))
):
    """Create a new cluster."""
    try:
        return service.create_cluster(cluster)
    except (EnvironmentNotFoundError, ClusterConnectionError) as e:
        raise HTTPException(status_code=400, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/clusters/{uuid}", response_model=ClusterResponse)
def update_cluster(
    uuid: UUID,
    cluster: ClusterCreate,
    service: ClusterService = Depends(get_cluster_service),
    current_user: User = Depends(require_role([UserRole.ADMIN]))
):
    """Update an existing cluster."""
    try:
        return service.update_cluster(uuid, cluster)
    except ClusterNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except (EnvironmentNotFoundError, ClusterConnectionError) as e:
        raise HTTPException(status_code=400, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/clusters/", response_model=list[ClusterResponseWithValidation])
def list_clusters(
    skip: int = 0,
    limit: int = 100,
    service: ClusterService = Depends(get_cluster_service),
    current_user: User = Depends(get_current_user)
):
    """List all clusters."""
    return service.get_clusters(skip=skip, limit=limit)


@router.get("/clusters/{uuid}", response_model=ClusterCompletedResponse)
def get_cluster(
    uuid: UUID,
    service: ClusterService = Depends(get_cluster_service),
    current_user: User = Depends(get_current_user)
):
    """Get cluster by UUID."""
    try:
        return service.get_cluster(uuid)
    except ClusterNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/clusters/{uuid}", response_model=dict)
def delete_cluster(
    uuid: UUID,
    service: ClusterService = Depends(get_cluster_service),
    current_user: User = Depends(require_role([UserRole.ADMIN]))
):
    """Delete a cluster."""
    try:
        return service.delete_cluster(uuid)
    except ClusterNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))

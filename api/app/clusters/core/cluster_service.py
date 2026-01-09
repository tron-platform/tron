import json
from uuid import uuid4, UUID
from typing import List
from fastapi import HTTPException

from app.clusters.infra.cluster_repository import ClusterRepository
from app.clusters.infra.cluster_model import Cluster as ClusterModel
from app.clusters.api.cluster_dto import (
    ClusterCreate,
    ClusterResponse,
    ClusterResponseWithValidation,
    ClusterCompletedResponse
)
from app.clusters.core.cluster_validators import (
    validate_cluster_create_dto,
    validate_cluster_exists,
    validate_environment_exists,
    ClusterNotFoundError,
    ClusterConnectionError,
    EnvironmentNotFoundError
)
# TODO: Migrate to shared/k8s
from app.k8s.client import K8sClient


def get_gateway_reference_from_cluster(cluster: ClusterModel) -> dict:
    """
    Get gateway reference information from a cluster.
    Dynamically searches for Gateway in Kubernetes cluster.

    Args:
        cluster: Cluster database object

    Returns:
        Dict with namespace and name of gateway, or empty values if not found
    """
    try:
        k8s_client = K8sClient(url=cluster.api_address, token=cluster.token)
        gateway_ref = k8s_client.get_gateway_reference()

        if gateway_ref:
            return gateway_ref
    except Exception as e:
        print(f"Warning: Error getting Gateway reference from cluster: {e}")

    return {
        "namespace": "",
        "name": ""
    }


class ClusterService:
    """Business logic for clusters. No direct database access."""

    def __init__(self, repository: ClusterRepository):
        self.repository = repository

    def create_cluster(self, dto: ClusterCreate) -> ClusterResponse:
        """Create a new cluster."""
        validate_cluster_create_dto(dto)
        validate_environment_exists(self.repository, dto.environment_uuid)

        # Validate Kubernetes connection
        self._validate_cluster_connection(dto.api_address, dto.token)

        environment = self.repository.find_environment_by_uuid(dto.environment_uuid)
        cluster = self._build_cluster_entity(dto, environment.id)

        return self.repository.create(cluster)

    def update_cluster(self, uuid: UUID, dto: ClusterCreate) -> ClusterResponse:
        """Update an existing cluster."""
        validate_cluster_create_dto(dto)
        validate_cluster_exists(self.repository, uuid)
        validate_environment_exists(self.repository, dto.environment_uuid)

        # Validate Kubernetes connection
        self._validate_cluster_connection(dto.api_address, dto.token)

        cluster = self.repository.find_by_uuid(uuid)
        environment = self.repository.find_environment_by_uuid(dto.environment_uuid)

        cluster.name = dto.name
        cluster.api_address = dto.api_address
        cluster.token = dto.token
        cluster.environment_id = environment.id

        return self.repository.update(cluster)

    def get_cluster(self, uuid: UUID) -> ClusterCompletedResponse:
        """Get cluster by UUID with full details."""
        validate_cluster_exists(self.repository, uuid)

        cluster = self.repository.find_by_uuid(uuid)
        return self._build_cluster_completed_response(cluster)

    def get_clusters(self, skip: int = 0, limit: int = 100) -> List[ClusterResponseWithValidation]:
        """Get all clusters with validation details."""
        clusters = self.repository.find_all(skip=skip, limit=limit)
        return [self._build_cluster_response_with_validation(cluster) for cluster in clusters]

    def delete_cluster(self, uuid: UUID) -> dict:
        """Delete a cluster."""
        validate_cluster_exists(self.repository, uuid)

        cluster = self.repository.find_by_uuid(uuid)
        self.repository.delete(cluster)

        return {"detail": "Cluster deleted successfully"}

    def _validate_cluster_connection(self, api_address: str, token: str) -> None:
        """Validate Kubernetes cluster connection. Raises ClusterConnectionError if fails."""
        k8s_client = K8sClient(url=api_address, token=token)

        try:
            success, connection_message = k8s_client.validate_connection()
            if not success:
                error_message = connection_message.get("message", {})
                if isinstance(error_message, dict):
                    error_text = error_message.get("message", json.dumps(error_message))
                else:
                    error_text = str(error_message)
                raise ClusterConnectionError(error_text)
        except HTTPException:
            raise
        except Exception as e:
            raise ClusterConnectionError(f"Connection validation failed: {str(e)}")

    def _build_cluster_entity(self, dto: ClusterCreate, environment_id: int) -> ClusterModel:
        """Build Cluster entity from DTO."""
        return ClusterModel(
            uuid=uuid4(),
            name=dto.name,
            api_address=dto.api_address,
            token=dto.token,
            environment_id=environment_id,
        )

    def _build_cluster_response_with_validation(self, cluster: ClusterModel) -> ClusterResponseWithValidation:
        """Build cluster response with validation details."""
        # TODO: Migrate Kubernetes client to shared/k8s
        k8s_client = K8sClient(url=cluster.api_address, token=cluster.token)
        success, connection_message = k8s_client.validate_connection()

        gateway_api_available = False
        gateway_resources = []
        gateway_ref = {"namespace": "", "name": ""}

        if success:
            gateway_api_available = k8s_client.check_api_available("gateway.networking.k8s.io")
            if gateway_api_available:
                gateway_resources = k8s_client.get_gateway_api_resources()
                gateway_ref = get_gateway_reference_from_cluster(cluster)

        return ClusterResponseWithValidation(
            uuid=cluster.uuid,
            name=cluster.name,
            api_address=cluster.api_address,
            environment=cluster.environment,
            detail=connection_message,
            gateway={
                "api": {
                    "enabled": gateway_api_available,
                    "resources": gateway_resources
                },
                "reference": gateway_ref
            }
        )

    def _build_cluster_completed_response(self, cluster: ClusterModel) -> ClusterCompletedResponse:
        """Build complete cluster response with all details."""
        # TODO: Migrate Kubernetes client to shared/k8s
        k8s_client = K8sClient(url=cluster.api_address, token=cluster.token)
        gateway_api_available = k8s_client.check_api_available("gateway.networking.k8s.io")
        gateway_resources = k8s_client.get_gateway_api_resources() if gateway_api_available else []
        gateway_ref = get_gateway_reference_from_cluster(cluster)

        # Get available CPU and memory from cluster
        try:
            available_cpu = k8s_client.get_available_cpu() or 0
            available_memory = k8s_client.get_available_memory() or 0
        except Exception:
            available_cpu = None
            available_memory = None

        return ClusterCompletedResponse(
            uuid=cluster.uuid,
            name=cluster.name,
            api_address=cluster.api_address,
            available_cpu=available_cpu,
            available_memory=available_memory,
            environment=cluster.environment,
            gateway={
                "api": {
                    "enabled": gateway_api_available,
                    "resources": gateway_resources
                },
                "reference": gateway_ref
            }
        )

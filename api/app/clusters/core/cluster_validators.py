from uuid import UUID
from app.clusters.infra.cluster_repository import ClusterRepository


class ClusterNotFoundError(Exception):
    """Raised when cluster is not found."""
    pass


class ClusterConnectionError(Exception):
    """Raised when cluster connection validation fails."""
    pass


class EnvironmentNotFoundError(Exception):
    """Raised when environment is not found."""
    pass


def validate_cluster_create_dto(dto) -> None:
    """Validate cluster create DTO. Raises ValueError if validation fails."""
    if not dto.name or not dto.name.strip():
        raise ValueError("Cluster name is required and cannot be empty")

    if not dto.api_address or not dto.api_address.strip():
        raise ValueError("Cluster API address is required and cannot be empty")

    if not dto.token or not dto.token.strip():
        raise ValueError("Cluster token is required and cannot be empty")

    if not dto.environment_uuid:
        raise ValueError("Environment UUID is required")


def validate_cluster_exists(repository: ClusterRepository, uuid: UUID) -> None:
    """Validate that cluster exists. Raises ClusterNotFoundError if not found."""
    cluster = repository.find_by_uuid(uuid)
    if not cluster:
        raise ClusterNotFoundError(f"Cluster with UUID '{uuid}' not found")


def validate_environment_exists(repository: ClusterRepository, uuid: UUID) -> None:
    """Validate that environment exists."""
    environment = repository.find_environment_by_uuid(uuid)
    if not environment:
        raise EnvironmentNotFoundError(f"Environment with UUID '{uuid}' not found")

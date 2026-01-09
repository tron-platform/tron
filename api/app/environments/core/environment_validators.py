from uuid import UUID
from app.environments.infra.environment_repository import EnvironmentRepository


class EnvironmentNotFoundError(Exception):
    """Raised when environment is not found."""
    pass


class EnvironmentHasComponentsError(Exception):
    """Raised when trying to delete environment with associated components."""
    pass


def validate_environment_create_dto(dto) -> None:
    """Validate environment create DTO. Raises ValueError if validation fails."""
    if not dto.name or not dto.name.strip():
        raise ValueError("Environment name is required and cannot be empty")

    if len(dto.name.strip()) < 1:
        raise ValueError("Environment name must be at least 1 character long")


def validate_environment_exists(repository: EnvironmentRepository, uuid: UUID) -> None:
    """Validate that environment exists. Raises EnvironmentNotFoundError if not found."""
    environment = repository.find_by_uuid(uuid)
    if not environment:
        raise EnvironmentNotFoundError(f"Environment with UUID '{uuid}' not found")


def validate_environment_can_be_deleted(repository: EnvironmentRepository, uuid: UUID) -> None:
    """Validate that environment can be deleted (no associated components)."""
    environment = repository.find_by_uuid(uuid)
    if not environment:
        raise EnvironmentNotFoundError(f"Environment with UUID '{uuid}' not found")

    components = repository.find_components_by_environment_id(environment.id)
    if components:
        raise EnvironmentHasComponentsError(
            "Cannot delete environment with associated components"
        )

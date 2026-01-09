from uuid import UUID
from app.instances.infra.instance_repository import InstanceRepository
from app.instances.api.instance_dto import InstanceCreate, InstanceUpdate


class InstanceNotFoundError(Exception):
    """Raised when instance is not found."""
    pass


class InstanceAlreadyExistsError(Exception):
    """Raised when instance already exists for application and environment."""
    pass


class ApplicationNotFoundError(Exception):
    """Raised when application is not found."""
    pass


class EnvironmentNotFoundError(Exception):
    """Raised when environment is not found."""
    pass


def validate_instance_create_dto(dto: InstanceCreate) -> None:
    """Validate instance create DTO. Raises ValueError if validation fails."""
    if not dto.image or not dto.image.strip():
        raise ValueError("Instance image is required and cannot be empty")

    if not dto.version or not dto.version.strip():
        raise ValueError("Instance version is required and cannot be empty")

    if not dto.application_uuid:
        raise ValueError("Application UUID is required")

    if not dto.environment_uuid:
        raise ValueError("Environment UUID is required")


def validate_instance_update_dto(dto: InstanceUpdate) -> None:
    """Validate instance update DTO. Raises ValueError if validation fails."""
    if dto.image is not None and not dto.image.strip():
        raise ValueError("Instance image cannot be empty")

    if dto.version is not None and not dto.version.strip():
        raise ValueError("Instance version cannot be empty")


def validate_instance_exists(repository: InstanceRepository, uuid: UUID) -> None:
    """Validate that instance exists. Raises InstanceNotFoundError if not found."""
    instance = repository.find_by_uuid(uuid)
    if not instance:
        raise InstanceNotFoundError(f"Instance with UUID '{uuid}' not found")


def validate_instance_uniqueness(
    repository: InstanceRepository,
    application_id: int,
    environment_id: int,
    exclude_uuid: UUID = None
) -> None:
    """Validate that instance is unique for application and environment."""
    existing_instance = repository.find_by_application_and_environment(application_id, environment_id)
    if existing_instance:
        if exclude_uuid and existing_instance.uuid == exclude_uuid:
            return  # Same instance, OK
        raise InstanceAlreadyExistsError(
            "Instance already exists for this application and environment"
        )


def validate_application_exists(repository: InstanceRepository, uuid: UUID) -> None:
    """Validate that application exists."""
    application = repository.find_application_by_uuid(uuid)
    if not application:
        raise ApplicationNotFoundError(f"Application with UUID '{uuid}' not found")


def validate_environment_exists(repository: InstanceRepository, uuid: UUID) -> None:
    """Validate that environment exists."""
    environment = repository.find_environment_by_uuid(uuid)
    if not environment:
        raise EnvironmentNotFoundError(f"Environment with UUID '{uuid}' not found")

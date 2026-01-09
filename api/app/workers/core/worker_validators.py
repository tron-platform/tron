from uuid import UUID
from app.workers.infra.worker_repository import WorkerRepository
from app.workers.api.worker_dto import WorkerCreate, WorkerUpdate


class WorkerNotFoundError(Exception):
    """Raised when worker is not found."""
    pass


class WorkerNotWorkerTypeError(Exception):
    """Raised when component is not a worker type."""
    pass


class InstanceNotFoundError(Exception):
    """Raised when instance is not found."""
    pass


def validate_worker_create_dto(dto: WorkerCreate) -> None:
    """Validate worker create DTO. Raises ValueError if validation fails."""
    if not dto.name or not dto.name.strip():
        raise ValueError("Worker name is required and cannot be empty")

    if ' ' in dto.name:
        raise ValueError("Component name cannot contain spaces")

    if not dto.instance_uuid:
        raise ValueError("Instance UUID is required")

    if not dto.settings:
        raise ValueError("Worker settings are required")


def validate_worker_update_dto(dto: WorkerUpdate) -> None:
    """Validate worker update DTO. Raises ValueError if validation fails."""
    pass


def validate_worker_exists(repository: WorkerRepository, uuid: UUID) -> None:
    """Validate that worker exists. Raises WorkerNotFoundError if not found."""
    worker = repository.find_by_uuid(uuid)
    if not worker:
        raise WorkerNotFoundError(f"Worker with UUID '{uuid}' not found")


def validate_worker_type(worker) -> None:
    """Validate that component is a worker type."""
    from app.workers.infra.application_component_model import WebappType
    if worker.type != WebappType.worker:
        raise WorkerNotWorkerTypeError("Component is not a worker")


def validate_instance_exists(repository: WorkerRepository, uuid: UUID) -> None:
    """Validate that instance exists."""
    instance = repository.find_instance_by_uuid(uuid)
    if not instance:
        raise InstanceNotFoundError(f"Instance with UUID '{uuid}' not found")

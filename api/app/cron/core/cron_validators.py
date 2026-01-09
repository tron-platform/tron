from uuid import UUID
from app.cron.infra.cron_repository import CronRepository
from app.cron.api.cron_dto import CronCreate, CronUpdate


class CronNotFoundError(Exception):
    """Raised when cron is not found."""
    pass


class CronNotCronTypeError(Exception):
    """Raised when component is not a cron type."""
    pass


class InstanceNotFoundError(Exception):
    """Raised when instance is not found."""
    pass


def validate_cron_create_dto(dto: CronCreate) -> None:
    """Validate cron create DTO. Raises ValueError if validation fails."""
    if not dto.name or not dto.name.strip():
        raise ValueError("Cron name is required and cannot be empty")

    if ' ' in dto.name:
        raise ValueError("Component name cannot contain spaces")

    if not dto.instance_uuid:
        raise ValueError("Instance UUID is required")

    if not dto.settings:
        raise ValueError("Cron settings are required")

    if not dto.settings.schedule or not dto.settings.schedule.strip():
        raise ValueError("Cron schedule is required")


def validate_cron_update_dto(dto: CronUpdate) -> None:
    """Validate cron update DTO. Raises ValueError if validation fails."""
    if dto.settings and dto.settings.schedule:
        if not dto.settings.schedule.strip():
            raise ValueError("Cron schedule cannot be empty")


def validate_cron_exists(repository: CronRepository, uuid: UUID) -> None:
    """Validate that cron exists. Raises CronNotFoundError if not found."""
    cron = repository.find_by_uuid(uuid)
    if not cron:
        raise CronNotFoundError(f"Cron with UUID '{uuid}' not found")


def validate_cron_type(cron) -> None:
    """Validate that component is a cron type."""
    from app.cron.infra.application_component_model import WebappType
    if cron.type != WebappType.cron:
        raise CronNotCronTypeError("Component is not a cron")


def validate_instance_exists(repository: CronRepository, uuid: UUID) -> None:
    """Validate that instance exists."""
    instance = repository.find_instance_by_uuid(uuid)
    if not instance:
        raise InstanceNotFoundError(f"Instance with UUID '{uuid}' not found")

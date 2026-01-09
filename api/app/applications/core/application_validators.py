from fastapi import HTTPException
from uuid import UUID
from app.applications.infra.application_repository import ApplicationRepository
from app.applications.api.application_dto import ApplicationCreate, ApplicationUpdate


class ApplicationNotFoundError(Exception):
    """Raised when application is not found."""
    pass


class ApplicationNameAlreadyExistsError(Exception):
    """Raised when application name already exists."""
    pass


def validate_application_name_uniqueness(
    repository: ApplicationRepository,
    name: str,
    exclude_uuid: UUID = None
) -> None:
    """
    Validate that application name is unique.
    Raises ApplicationNameAlreadyExistsError if name already exists.
    """
    existing_application = None
    if exclude_uuid:
        existing_application = repository.find_by_name_excluding_uuid(name, exclude_uuid)
    else:
        existing_application = repository.find_by_name(name)

    if existing_application:
        raise ApplicationNameAlreadyExistsError(f"Application with name '{name}' already exists")


def validate_application_exists(
    repository: ApplicationRepository,
    uuid: UUID
) -> None:
    """
    Validate that application exists.
    Raises ApplicationNotFoundError if application not found.
    """
    application = repository.find_by_uuid(uuid)
    if not application:
        raise ApplicationNotFoundError(f"Application with UUID '{uuid}' not found")


def validate_application_create_dto(dto: ApplicationCreate) -> None:
    """
    Validate application create DTO.
    Raises ValueError if validation fails.
    """
    if not dto.name or not dto.name.strip():
        raise ValueError("Application name is required and cannot be empty")

    if len(dto.name.strip()) < 1:
        raise ValueError("Application name must be at least 1 character long")


def validate_application_update_dto(dto: ApplicationUpdate) -> None:
    """
    Validate application update DTO.
    Raises ValueError if validation fails.
    """
    if dto.name is not None:
        if not dto.name.strip():
            raise ValueError("Application name cannot be empty")
        if len(dto.name.strip()) < 1:
            raise ValueError("Application name must be at least 1 character long")

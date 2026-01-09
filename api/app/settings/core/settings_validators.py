from uuid import UUID
from app.settings.infra.settings_repository import SettingsRepository


class SettingsNotFoundError(Exception):
    """Raised when settings is not found."""
    pass


class EnvironmentNotFoundError(Exception):
    """Raised when environment is not found."""
    pass


class SettingsKeyAlreadyExistsError(Exception):
    """Raised when settings key already exists for environment."""
    pass


def validate_settings_create_dto(dto) -> None:
    """Validate settings create DTO. Raises ValueError if validation fails."""
    if not dto.key or not dto.key.strip():
        raise ValueError("Settings key is required and cannot be empty")

    if dto.value is None:
        raise ValueError("Settings value is required")

    if not dto.environment_uuid:
        raise ValueError("Environment UUID is required")


def validate_settings_update_dto(dto) -> None:
    """Validate settings update DTO. Raises ValueError if validation fails."""
    if dto.key is not None and not dto.key.strip():
        raise ValueError("Settings key cannot be empty")


def validate_settings_exists(repository: SettingsRepository, uuid: UUID) -> None:
    """Validate that settings exists. Raises SettingsNotFoundError if not found."""
    settings = repository.find_by_uuid(uuid)
    if not settings:
        raise SettingsNotFoundError(f"Settings with UUID '{uuid}' not found")


def validate_environment_exists(repository: SettingsRepository, uuid: UUID) -> None:
    """Validate that environment exists."""
    environment = repository.find_environment_by_uuid(uuid)
    if not environment:
        raise EnvironmentNotFoundError(f"Environment with UUID '{uuid}' not found")


def validate_settings_key_uniqueness(
    repository: SettingsRepository,
    key: str,
    environment_id: int,
    exclude_uuid: UUID = None
) -> None:
    """Validate that settings key is unique for environment."""
    existing_settings = repository.find_by_key_and_environment_id(key, environment_id)
    if existing_settings:
        if exclude_uuid and existing_settings.uuid == exclude_uuid:
            return  # Same settings, OK
        raise SettingsKeyAlreadyExistsError(
            f"Settings with key '{key}' already exists for this environment"
        )

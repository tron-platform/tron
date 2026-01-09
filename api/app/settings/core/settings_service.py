from uuid import uuid4, UUID
from typing import List
from app.settings.infra.settings_repository import SettingsRepository
from app.settings.infra.settings_model import Settings as SettingsModel
from app.settings.api.settings_dto import (
    SettingsCreate,
    SettingsUpdate,
    Settings,
    SettingsWithEnvironment
)
from app.settings.core.settings_validators import (
    validate_settings_create_dto,
    validate_settings_update_dto,
    validate_settings_exists,
    validate_environment_exists,
    validate_settings_key_uniqueness,
    SettingsNotFoundError,
    EnvironmentNotFoundError,
    SettingsKeyAlreadyExistsError
)


class SettingsService:
    """Business logic for settings. No direct database access."""

    def __init__(self, repository: SettingsRepository):
        self.repository = repository

    def create_settings(self, dto: SettingsCreate) -> Settings:
        """Create a new settings."""
        validate_settings_create_dto(dto)
        validate_environment_exists(self.repository, dto.environment_uuid)

        environment = self.repository.find_environment_by_uuid(dto.environment_uuid)
        validate_settings_key_uniqueness(self.repository, dto.key, environment.id)

        settings = self._build_settings_entity(dto, environment.id)
        return self.repository.create(settings)

    def update_settings(self, uuid: UUID, dto: SettingsUpdate) -> Settings:
        """Update an existing settings."""
        validate_settings_update_dto(dto)
        validate_settings_exists(self.repository, uuid)

        settings = self.repository.find_by_uuid(uuid)

        if dto.key is not None:
            validate_settings_key_uniqueness(self.repository, dto.key, settings.environment_id, exclude_uuid=uuid)
            settings.key = dto.key

        if dto.value is not None:
            settings.value = dto.value

        if dto.description is not None:
            settings.description = dto.description

        return self.repository.update(settings)

    def get_settings(self, uuid: UUID) -> SettingsWithEnvironment:
        """Get settings by UUID with environment."""
        validate_settings_exists(self.repository, uuid)

        settings = self.repository.find_by_uuid(uuid)
        return self._serialize_settings_with_environment(settings)

    def get_settings_list(self, skip: int = 0, limit: int = 100) -> List[SettingsWithEnvironment]:
        """Get all settings with environment."""
        settings_list = self.repository.find_all(skip=skip, limit=limit)
        return [self._serialize_settings_with_environment(s) for s in settings_list]

    def delete_settings(self, uuid: UUID) -> dict:
        """Delete a settings."""
        validate_settings_exists(self.repository, uuid)

        settings = self.repository.find_by_uuid(uuid)
        self.repository.delete(settings)

        return {"detail": "Settings deleted successfully"}

    def _build_settings_entity(self, dto: SettingsCreate, environment_id: int) -> SettingsModel:
        """Build Settings entity from DTO."""
        return SettingsModel(
            uuid=uuid4(),
            key=dto.key,
            value=dto.value,
            description=dto.description,
            environment_id=environment_id
        )

    def _serialize_settings_with_environment(self, settings: SettingsModel) -> SettingsWithEnvironment:
        """Serialize settings with environment."""
        return SettingsWithEnvironment(
            uuid=settings.uuid,
            key=settings.key,
            value=settings.value,
            description=settings.description,
            environment={
                "name": settings.environment.name,
                "uuid": settings.environment.uuid
            }
        )

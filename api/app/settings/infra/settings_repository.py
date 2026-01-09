from sqlalchemy.orm import Session
from uuid import UUID
from typing import Optional, List
from app.settings.infra.settings_model import Settings as SettingsModel
from app.environments.infra.environment_model import Environment as EnvironmentModel


class SettingsRepository:
    """Repository for Settings database operations. No business logic here."""

    def __init__(self, database_session: Session):
        self.db = database_session

    def find_by_uuid(self, uuid: UUID) -> Optional[SettingsModel]:
        """Find settings by UUID."""
        return self.db.query(SettingsModel).filter(SettingsModel.uuid == uuid).first()

    def find_by_key_and_environment_id(self, key: str, environment_id: int) -> Optional[SettingsModel]:
        """Find settings by key and environment ID."""
        return (
            self.db.query(SettingsModel)
            .filter(
                SettingsModel.key == key,
                SettingsModel.environment_id == environment_id
            )
            .first()
        )

    def find_all(self, skip: int = 0, limit: int = 100) -> List[SettingsModel]:
        """Find all settings."""
        return self.db.query(SettingsModel).offset(skip).limit(limit).all()

    def find_environment_by_uuid(self, uuid: UUID) -> Optional[EnvironmentModel]:
        """Find environment by UUID."""
        return self.db.query(EnvironmentModel).filter(EnvironmentModel.uuid == uuid).first()

    def create(self, settings: SettingsModel) -> SettingsModel:
        """Create a new settings."""
        self.db.add(settings)
        try:
            self.db.commit()
            self.db.refresh(settings)
        except Exception as e:
            self.db.rollback()
            raise Exception(f"Failed to create settings: {str(e)}")
        return settings

    def update(self, settings: SettingsModel) -> SettingsModel:
        """Update an existing settings."""
        try:
            self.db.commit()
            self.db.refresh(settings)
        except Exception as e:
            self.db.rollback()
            raise Exception(f"Failed to update settings: {str(e)}")
        return settings

    def delete(self, settings: SettingsModel) -> None:
        """Delete a settings."""
        self.db.delete(settings)
        try:
            self.db.commit()
        except Exception as e:
            self.db.rollback()
            raise Exception(f"Failed to delete settings: {str(e)}")

    def rollback(self) -> None:
        """Rollback current transaction."""
        self.db.rollback()

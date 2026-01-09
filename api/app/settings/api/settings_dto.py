from pydantic import BaseModel, ConfigDict
from typing import Optional, Union
from uuid import UUID
from app.environments.api.environment_dto import Environment


class SettingsBase(BaseModel):
    key: str
    value: Union[str, int, bool, dict]
    description: Optional[str] = None


class SettingsCreate(SettingsBase):
    environment_uuid: UUID


class Settings(SettingsBase):
    uuid: UUID

    model_config = ConfigDict(
        from_attributes=True,
    )


class SettingsUpdate(SettingsBase):
    key: Optional[str] = None
    value: Optional[Union[str, int, bool, dict]] = None


class SettingsWithEnvironment(Settings):
    environment: Environment

    model_config = ConfigDict(
        from_attributes=True,
    )

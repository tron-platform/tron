from pydantic import BaseModel, ConfigDict, model_validator
from uuid import UUID
from datetime import datetime
from typing import Any


class ApplicationBase(BaseModel):
    name: str
    repository: str | None = None
    enabled: bool = True


class ApplicationCreate(ApplicationBase):
    pass


class ApplicationUpdate(BaseModel):
    name: str | None = None
    repository: str | None = None
    enabled: bool | None = None


class Application(ApplicationBase):
    uuid: UUID
    created_at: str
    updated_at: str

    @model_validator(mode='before')
    @classmethod
    def convert_datetime_to_string(cls, data: Any) -> Any:
        if isinstance(data, dict):
            if 'created_at' in data and isinstance(data['created_at'], datetime):
                data['created_at'] = data['created_at'].isoformat()
            if 'updated_at' in data and isinstance(data['updated_at'], datetime):
                data['updated_at'] = data['updated_at'].isoformat()
        elif hasattr(data, '__dict__'):
            if hasattr(data, 'created_at') and isinstance(data.created_at, datetime):
                data.created_at = data.created_at.isoformat()
            if hasattr(data, 'updated_at') and isinstance(data.updated_at, datetime):
                data.updated_at = data.updated_at.isoformat()
        return data

    model_config = ConfigDict(
        from_attributes=True,
    )

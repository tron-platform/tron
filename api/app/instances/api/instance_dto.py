from pydantic import BaseModel, ConfigDict, model_validator
from uuid import UUID
from datetime import datetime
from typing import Any, List
from app.applications.api.application_dto import Application
from app.environments.api.environment_dto import Environment


class InstanceBase(BaseModel):
    image: str
    version: str
    enabled: bool = True


class InstanceCreate(InstanceBase):
    application_uuid: UUID
    environment_uuid: UUID


class InstanceUpdate(BaseModel):
    image: str | None = None
    version: str | None = None
    enabled: bool | None = None


class InstanceComponent(BaseModel):
    uuid: UUID
    name: str
    type: str
    url: str | None
    enabled: bool
    settings: dict[str, Any] | None = None
    created_at: str
    updated_at: str

    @model_validator(mode='before')
    @classmethod
    def convert_datetime_to_string_and_remove_visibility(cls, data: Any) -> Any:
        if isinstance(data, dict):
            if 'created_at' in data and isinstance(data['created_at'], datetime):
                data['created_at'] = data['created_at'].isoformat()
            if 'updated_at' in data and isinstance(data['updated_at'], datetime):
                data['updated_at'] = data['updated_at'].isoformat()
            if 'visibility' in data:
                del data['visibility']
        elif hasattr(data, '__dict__'):
            if hasattr(data, 'created_at') and isinstance(data.created_at, datetime):
                data.created_at = data.created_at.isoformat()
            if hasattr(data, 'updated_at') and isinstance(data.updated_at, datetime):
                data.updated_at = data.updated_at.isoformat()
            if hasattr(data, 'visibility'):
                delattr(data, 'visibility')
        return data

    model_config = ConfigDict(
        from_attributes=True,
    )


class Instance(InstanceBase):
    uuid: UUID
    application: Application
    environment: Environment
    components: List[InstanceComponent] = []
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
            if 'components' in data and data['components']:
                for component in data['components']:
                    if isinstance(component, dict):
                        if 'created_at' in component and isinstance(component['created_at'], datetime):
                            component['created_at'] = component['created_at'].isoformat()
                        if 'updated_at' in component and isinstance(component['updated_at'], datetime):
                            component['updated_at'] = component['updated_at'].isoformat()
        elif hasattr(data, '__dict__'):
            if hasattr(data, 'created_at') and isinstance(data.created_at, datetime):
                data.created_at = data.created_at.isoformat()
            if hasattr(data, 'updated_at') and isinstance(data.updated_at, datetime):
                data.updated_at = data.updated_at.isoformat()
            if hasattr(data, 'components') and data.components:
                for component in data.components:
                    if hasattr(component, 'created_at') and isinstance(component.created_at, datetime):
                        component.created_at = component.created_at.isoformat()
                    if hasattr(component, 'updated_at') and isinstance(component.updated_at, datetime):
                        component.updated_at = component.updated_at.isoformat()
        return data

    model_config = ConfigDict(
        from_attributes=True,
    )


class KubernetesEventInvolvedObject(BaseModel):
    kind: str | None = None
    name: str | None = None
    namespace: str | None = None


class KubernetesEventSource(BaseModel):
    component: str | None = None
    host: str | None = None


class KubernetesEvent(BaseModel):
    name: str
    namespace: str
    type: str
    reason: str
    message: str
    involved_object: KubernetesEventInvolvedObject
    source: KubernetesEventSource
    first_timestamp: str | None = None
    last_timestamp: str | None = None
    count: int
    age_seconds: int

from pydantic import BaseModel, ConfigDict, field_validator, model_validator
from typing import List, Any, Dict, Union
from uuid import UUID
from datetime import datetime
import shlex


class WorkerEnvs(BaseModel):
    key: str
    value: str


class WorkerCustomMetrics(BaseModel):
    enabled: bool = False
    path: str = "/metrics"
    port: int


class WorkerAutoscaling(BaseModel):
    min: int = 2
    max: int = 10


class WorkerSettings(BaseModel):
    custom_metrics: WorkerCustomMetrics
    envs: List[WorkerEnvs] = []
    command: Union[str, List[str], None] = None
    cpu: float
    memory: int
    cpu_scaling_threshold: int = 80
    memory_scaling_threshold: int = 80
    autoscaling: WorkerAutoscaling

    @model_validator(mode='after')
    def parse_command(self):
        """Parse command string into array if it's a string"""
        if isinstance(self.command, str):
            command_str = self.command.strip()
            if command_str:
                self.command = shlex.split(command_str)
            else:
                self.command = None
        return self


class WorkerBase(BaseModel):
    name: str

    @field_validator('name')
    @classmethod
    def validate_name_no_spaces(cls, v: str) -> str:
        if ' ' in v:
            raise ValueError("Component name cannot contain spaces")
        return v

    model_config = ConfigDict(
        from_attributes=True,
    )


class WorkerCreate(WorkerBase):
    instance_uuid: UUID
    name: str
    enabled: bool = True
    settings: WorkerSettings


class WorkerUpdate(BaseModel):
    enabled: bool | None = None
    settings: WorkerSettings | None = None


class Worker(WorkerBase):
    uuid: UUID
    name: str
    enabled: bool
    settings: Dict[str, Any] | None
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

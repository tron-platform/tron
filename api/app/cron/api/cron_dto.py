from pydantic import BaseModel, ConfigDict, field_validator, model_validator
from typing import List, Any, Dict, Union
from uuid import UUID
from datetime import datetime
import shlex


class CronEnvs(BaseModel):
    key: str
    value: str


class CronSettings(BaseModel):
    envs: List[CronEnvs] = []
    command: Union[str, List[str], None] = None
    cpu: float
    memory: int
    schedule: str  # Cron schedule expression (e.g., "0 0 * * *")

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


class CronBase(BaseModel):
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


class CronCreate(CronBase):
    instance_uuid: UUID
    name: str
    enabled: bool = True
    settings: CronSettings


class CronUpdate(BaseModel):
    enabled: bool | None = None
    settings: CronSettings | None = None


class Cron(CronBase):
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


class CronJob(BaseModel):
    """Schema for representing a Job executed by a CronJob"""
    name: str
    status: str  # Succeeded, Failed, Active, Unknown
    succeeded: int
    failed: int
    active: int
    start_time: str | None
    completion_time: str | None
    age_seconds: int
    duration_seconds: int | None

    model_config = ConfigDict(
        from_attributes=True,
    )


class CronJobLogs(BaseModel):
    """Schema for logs of a Job"""
    logs: str
    pod_name: str
    job_name: str
    container_name: str | None = None

    model_config = ConfigDict(
        from_attributes=True,
    )

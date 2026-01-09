from pydantic import BaseModel, ConfigDict, model_validator
from typing import Optional, Any
from datetime import datetime
from uuid import UUID
from app.auth.infra.token_model import TokenRole


class TokenBase(BaseModel):
    name: str
    role: str
    expires_at: Optional[datetime] = None


class TokenCreate(TokenBase):
    pass


class TokenUpdate(BaseModel):
    name: Optional[str] = None
    role: Optional[str] = None
    is_active: Optional[bool] = None
    expires_at: Optional[datetime] = None


class TokenResponse(TokenBase):
    uuid: str
    is_active: bool
    last_used_at: Optional[str] = None
    created_at: str
    updated_at: str
    user_id: Optional[int] = None

    @model_validator(mode='before')
    @classmethod
    def convert_datetime_to_string(cls, data: Any) -> Any:
        if isinstance(data, dict):
            if 'uuid' in data and isinstance(data['uuid'], UUID):
                data['uuid'] = str(data['uuid'])
            if 'created_at' in data and isinstance(data['created_at'], datetime):
                data['created_at'] = data['created_at'].isoformat()
            if 'updated_at' in data and isinstance(data['updated_at'], datetime):
                data['updated_at'] = data['updated_at'].isoformat()
            if 'last_used_at' in data and isinstance(data['last_used_at'], datetime):
                data['last_used_at'] = data['last_used_at'].isoformat()
            if 'expires_at' in data and isinstance(data['expires_at'], datetime):
                data['expires_at'] = data['expires_at'].isoformat()
        elif hasattr(data, '__dict__'):
            if hasattr(data, 'uuid') and isinstance(data.uuid, UUID):
                data.uuid = str(data.uuid)
            if hasattr(data, 'created_at') and isinstance(data.created_at, datetime):
                data.created_at = data.created_at.isoformat()
            if hasattr(data, 'updated_at') and isinstance(data.updated_at, datetime):
                data.updated_at = data.updated_at.isoformat()
            if hasattr(data, 'last_used_at') and isinstance(data.last_used_at, datetime):
                data.last_used_at = data.last_used_at.isoformat()
            if hasattr(data, 'expires_at') and isinstance(data.expires_at, datetime):
                data.expires_at = data.expires_at.isoformat()
        return data

    model_config = ConfigDict(
        from_attributes=True,
    )


class TokenCreateResponse(BaseModel):
    uuid: str
    name: str
    token: str  # Token gerado (só aparece na criação)
    role: str
    expires_at: Optional[str] = None
    created_at: str

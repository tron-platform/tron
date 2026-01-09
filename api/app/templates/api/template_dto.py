from pydantic import BaseModel, ConfigDict
from uuid import UUID
from typing import Optional


class TemplateBase(BaseModel):
    name: str
    description: Optional[str] = None
    category: str
    content: str
    variables_schema: Optional[str] = None


class TemplateCreate(TemplateBase):
    pass


class TemplateUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    content: Optional[str] = None
    variables_schema: Optional[str] = None


class Template(TemplateBase):
    uuid: UUID

    model_config = ConfigDict(
        from_attributes=True,
    )

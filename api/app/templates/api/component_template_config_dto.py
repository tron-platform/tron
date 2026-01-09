from pydantic import BaseModel, ConfigDict
from uuid import UUID
from typing import Optional


class ComponentTemplateConfigBase(BaseModel):
    component_type: str  # webapp, cron, worker
    template_uuid: UUID
    render_order: int = 0
    enabled: bool = True


class ComponentTemplateConfigCreate(ComponentTemplateConfigBase):
    pass


class ComponentTemplateConfigUpdate(BaseModel):
    render_order: Optional[int] = None
    enabled: Optional[bool] = None


class ComponentTemplateConfig(ComponentTemplateConfigBase):
    uuid: UUID
    template_name: Optional[str] = None

    model_config = ConfigDict(
        from_attributes=True,
    )


class ComponentTemplateConfigWithTemplate(ComponentTemplateConfig):
    template_name: Optional[str] = None

    model_config = ConfigDict(
        from_attributes=True,
    )

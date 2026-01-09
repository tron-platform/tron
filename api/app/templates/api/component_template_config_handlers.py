from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from uuid import UUID
from typing import List

from app.shared.database.database import get_db
from app.templates.infra.component_template_config_repository import ComponentTemplateConfigRepository
from app.templates.infra.template_repository import TemplateRepository
from app.templates.core.component_template_config_service import ComponentTemplateConfigService
from app.templates.api.component_template_config_dto import (
    ComponentTemplateConfigCreate,
    ComponentTemplateConfigUpdate,
    ComponentTemplateConfig
)
from app.templates.core.component_template_config_validators import (
    ComponentTemplateConfigNotFoundError,
    ComponentTemplateConfigAlreadyExistsError,
    TemplateNotFoundError
)
from app.users.infra.user_model import User, UserRole
from app.shared.dependencies.auth import require_role, get_current_user


router = APIRouter()


def get_component_template_config_service(
    database_session: Session = Depends(get_db)
) -> ComponentTemplateConfigService:
    """Dependency to get ComponentTemplateConfigService instance."""
    config_repository = ComponentTemplateConfigRepository(database_session)
    template_repository = TemplateRepository(database_session)
    return ComponentTemplateConfigService(config_repository, template_repository)


@router.post("/component-template-configs/", response_model=ComponentTemplateConfig)
def create_component_template_config(
    config: ComponentTemplateConfigCreate,
    service: ComponentTemplateConfigService = Depends(get_component_template_config_service),
    current_user: User = Depends(require_role([UserRole.ADMIN]))
):
    """Create a new component template config."""
    try:
        db_config = service.create_component_template_config(config)
        # Serialize manually to include template_uuid
        return {
            "uuid": db_config.uuid,
            "component_type": db_config.component_type,
            "template_uuid": db_config.template.uuid,
            "render_order": db_config.render_order,
            "enabled": db_config.enabled == "true",
        }
    except TemplateNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ComponentTemplateConfigAlreadyExistsError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/component-template-configs/{uuid}", response_model=ComponentTemplateConfig)
def update_component_template_config(
    uuid: UUID,
    config: ComponentTemplateConfigUpdate,
    service: ComponentTemplateConfigService = Depends(get_component_template_config_service),
    current_user: User = Depends(require_role([UserRole.ADMIN]))
):
    """Update an existing component template config."""
    try:
        db_config = service.update_component_template_config(uuid, config)
        # Serialize manually to include template_uuid
        return {
            "uuid": db_config.uuid,
            "component_type": db_config.component_type,
            "template_uuid": db_config.template.uuid,
            "render_order": db_config.render_order,
            "enabled": db_config.enabled == "true",
        }
    except ComponentTemplateConfigNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/component-template-configs/", response_model=List[ComponentTemplateConfig])
def list_component_template_configs(
    skip: int = 0,
    limit: int = 100,
    component_type: str = Query(None, description="Filter by component type"),
    service: ComponentTemplateConfigService = Depends(get_component_template_config_service),
    current_user: User = Depends(get_current_user)
):
    """List all component template configs."""
    configs = service.get_component_template_configs(
        component_type=component_type, skip=skip, limit=limit
    )
    # Serialize manually to include template information
    result = []
    for config in configs:
        config_dict = {
            "uuid": str(config.uuid),
            "component_type": config.component_type,
            "template_uuid": str(config.template.uuid),
            "render_order": config.render_order,
            "enabled": config.enabled == "true",
            "template_name": config.template.name if config.template else None,
        }
        result.append(config_dict)
    return result


@router.get("/component-template-configs/{uuid}", response_model=ComponentTemplateConfig)
def get_component_template_config(
    uuid: UUID,
    service: ComponentTemplateConfigService = Depends(get_component_template_config_service),
    current_user: User = Depends(get_current_user)
):
    """Get component template config by UUID."""
    try:
        db_config = service.get_component_template_config(uuid)
        # Serialize manually to include template_uuid
        return {
            "uuid": db_config.uuid,
            "component_type": db_config.component_type,
            "template_uuid": db_config.template.uuid,
            "render_order": db_config.render_order,
            "enabled": db_config.enabled == "true",
        }
    except ComponentTemplateConfigNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/component-template-configs/{uuid}", response_model=dict)
def delete_component_template_config(
    uuid: UUID,
    service: ComponentTemplateConfigService = Depends(get_component_template_config_service),
    current_user: User = Depends(require_role([UserRole.ADMIN]))
):
    """Delete a component template config."""
    try:
        return service.delete_component_template_config(uuid)
    except ComponentTemplateConfigNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/component-template-configs/component/{component_type}/templates", response_model=List[dict])
def get_templates_for_component(
    component_type: str,
    service: ComponentTemplateConfigService = Depends(get_component_template_config_service),
    current_user: User = Depends(get_current_user)
):
    """Get templates ordered by render_order for a specific component type."""
    templates = service.get_templates_for_component_type(component_type)
    return [
        {
            "uuid": str(template.uuid),
            "name": template.name,
            "content": template.content,
        }
        for template in templates
    ]

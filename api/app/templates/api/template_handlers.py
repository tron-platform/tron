from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from uuid import UUID
from typing import Optional

from app.shared.database.database import get_db
from app.templates.infra.template_repository import TemplateRepository
from app.templates.core.template_service import TemplateService
from app.templates.api.template_dto import TemplateCreate, TemplateUpdate, Template
from app.templates.core.template_validators import TemplateNotFoundError
from app.users.infra.user_model import User, UserRole
from app.shared.dependencies.auth import require_role, get_current_user


router = APIRouter()


def get_template_service(database_session: Session = Depends(get_db)) -> TemplateService:
    """Dependency to get TemplateService instance."""
    template_repository = TemplateRepository(database_session)
    return TemplateService(template_repository)


@router.post("/templates/", response_model=Template)
def create_template(
    template: TemplateCreate,
    service: TemplateService = Depends(get_template_service),
    current_user: User = Depends(require_role([UserRole.ADMIN]))
):
    """Create a new template."""
    try:
        return service.create_template(template)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/templates/{uuid}", response_model=Template)
def update_template(
    uuid: UUID,
    template: TemplateUpdate,
    service: TemplateService = Depends(get_template_service),
    current_user: User = Depends(require_role([UserRole.ADMIN]))
):
    """Update an existing template."""
    try:
        return service.update_template(uuid, template)
    except TemplateNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/templates/", response_model=list[Template])
def list_templates(
    skip: int = 0,
    limit: int = 100,
    category: Optional[str] = Query(None, description="Filter by category"),
    service: TemplateService = Depends(get_template_service),
    current_user: User = Depends(get_current_user)
):
    """List all templates."""
    return service.get_templates(skip=skip, limit=limit, category=category)


@router.get("/templates/{uuid}", response_model=Template)
def get_template(
    uuid: UUID,
    service: TemplateService = Depends(get_template_service),
    current_user: User = Depends(get_current_user)
):
    """Get template by UUID."""
    try:
        return service.get_template(uuid)
    except TemplateNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/templates/{uuid}", response_model=dict)
def delete_template(
    uuid: UUID,
    service: TemplateService = Depends(get_template_service),
    current_user: User = Depends(require_role([UserRole.ADMIN]))
):
    """Delete a template."""
    try:
        return service.delete_template(uuid)
    except TemplateNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

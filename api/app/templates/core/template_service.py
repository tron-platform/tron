from uuid import uuid4, UUID
from typing import List, Optional
from app.templates.infra.template_repository import TemplateRepository
from app.templates.infra.template_model import Template as TemplateModel
from app.templates.api.template_dto import TemplateCreate, TemplateUpdate, Template
from app.templates.core.template_validators import (
    validate_template_create_dto,
    validate_template_update_dto,
    validate_template_exists,
    validate_template_can_be_deleted,
    TemplateNotFoundError
)


class TemplateService:
    """Business logic for templates. No direct database access."""

    def __init__(self, repository: TemplateRepository):
        self.repository = repository

    def create_template(self, dto: TemplateCreate) -> Template:
        """Create a new template."""
        validate_template_create_dto(dto)

        template = self._build_template_entity(dto)
        return self.repository.create(template)

    def update_template(self, uuid: UUID, dto: TemplateUpdate) -> Template:
        """Update an existing template."""
        validate_template_update_dto(dto)
        validate_template_exists(self.repository, uuid)

        template = self.repository.find_by_uuid(uuid)

        if dto.name is not None:
            template.name = dto.name

        if dto.description is not None:
            template.description = dto.description

        if dto.content is not None:
            template.content = dto.content

        if dto.variables_schema is not None:
            template.variables_schema = dto.variables_schema

        return self.repository.update(template)

    def get_template(self, uuid: UUID) -> Template:
        """Get template by UUID."""
        validate_template_exists(self.repository, uuid)
        return self.repository.find_by_uuid(uuid)

    def get_templates(
        self,
        skip: int = 0,
        limit: int = 100,
        category: Optional[str] = None
    ) -> List[Template]:
        """Get all templates, optionally filtered by category."""
        return self.repository.find_all(skip=skip, limit=limit, category=category)

    def delete_template(self, uuid: UUID) -> dict:
        """Delete a template and its associated component configs."""
        validate_template_exists(self.repository, uuid)
        validate_template_can_be_deleted(self.repository, uuid)

        template = self.repository.find_by_uuid(uuid)
        configs = self.repository.find_component_configs_by_template_id(template.id)

        # Delete associated configs first
        if configs:
            self.repository.delete_component_configs(configs)

        # Delete template
        self.repository.delete(template)

        return {"status": "success", "message": "Template deleted successfully"}

    def _build_template_entity(self, dto: TemplateCreate) -> TemplateModel:
        """Build Template entity from DTO."""
        return TemplateModel(
            uuid=uuid4(),
            name=dto.name,
            description=dto.description,
            category=dto.category,
            content=dto.content,
            variables_schema=dto.variables_schema,
        )

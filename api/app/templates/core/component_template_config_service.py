from sqlalchemy.orm import Session
from uuid import UUID
from typing import Optional, List
from app.templates.infra.component_template_config_repository import ComponentTemplateConfigRepository
from app.templates.infra.template_repository import TemplateRepository
from app.templates.infra.component_template_config_model import ComponentTemplateConfig as ComponentTemplateConfigModel
from app.templates.infra.template_model import Template as TemplateModel
from app.templates.core.component_template_config_validators import (
    ComponentTemplateConfigNotFoundError,
    ComponentTemplateConfigAlreadyExistsError,
    TemplateNotFoundError
)
from app.templates.api.component_template_config_dto import (
    ComponentTemplateConfigCreate,
    ComponentTemplateConfigUpdate
)
from uuid import uuid4


class ComponentTemplateConfigService:
    """Service for component template config business logic."""

    def __init__(
        self,
        config_repository: ComponentTemplateConfigRepository,
        template_repository: TemplateRepository
    ):
        self.config_repository = config_repository
        self.template_repository = template_repository

    def create_component_template_config(
        self, config_data: ComponentTemplateConfigCreate
    ) -> ComponentTemplateConfigModel:
        """Create a new component template config."""
        # Validate template exists
        template = self.template_repository.find_by_uuid(config_data.template_uuid)
        if not template:
            raise TemplateNotFoundError(f"Template with UUID {config_data.template_uuid} not found")

        # Check if config already exists
        existing_config = self.config_repository.find_by_component_type_and_template_id(
            config_data.component_type, template.id
        )
        if existing_config:
            raise ComponentTemplateConfigAlreadyExistsError(
                f"Configuration for component_type '{config_data.component_type}' "
                f"and template '{config_data.template_uuid}' already exists"
            )

        # Create new config
        new_config = ComponentTemplateConfigModel(
            uuid=uuid4(),
            component_type=config_data.component_type,
            template_id=template.id,
            render_order=config_data.render_order,
            enabled=str(config_data.enabled).lower(),
        )

        return self.config_repository.create(new_config)

    def update_component_template_config(
        self, config_uuid: UUID, config_data: ComponentTemplateConfigUpdate
    ) -> ComponentTemplateConfigModel:
        """Update an existing component template config."""
        config = self.config_repository.find_by_uuid(config_uuid)
        if not config:
            raise ComponentTemplateConfigNotFoundError(
                f"Component template config with UUID {config_uuid} not found"
            )

        # Update fields
        if config_data.render_order is not None:
            config.render_order = config_data.render_order
        if config_data.enabled is not None:
            config.enabled = str(config_data.enabled).lower()

        return self.config_repository.update(config)

    def get_component_template_config(self, config_uuid: UUID) -> ComponentTemplateConfigModel:
        """Get component template config by UUID."""
        config = self.config_repository.find_by_uuid(config_uuid)
        if not config:
            raise ComponentTemplateConfigNotFoundError(
                f"Component template config with UUID {config_uuid} not found"
            )
        return config

    def get_component_template_configs(
        self, component_type: Optional[str] = None, skip: int = 0, limit: int = 100
    ) -> List[ComponentTemplateConfigModel]:
        """Get all component template configs, optionally filtered by component type."""
        return self.config_repository.find_all(component_type=component_type, skip=skip, limit=limit)

    def get_templates_for_component_type(self, component_type: str) -> List[TemplateModel]:
        """Get templates ordered by render_order for a component type."""
        return self.config_repository.find_templates_for_component_type(component_type)

    def delete_component_template_config(self, config_uuid: UUID) -> dict:
        """Delete a component template config."""
        config = self.config_repository.find_by_uuid(config_uuid)
        if not config:
            raise ComponentTemplateConfigNotFoundError(
                f"Component template config with UUID {config_uuid} not found"
            )

        self.config_repository.delete(config)
        return {"status": "success", "message": "Component template config deleted successfully"}

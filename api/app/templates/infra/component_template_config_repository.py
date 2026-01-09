from sqlalchemy.orm import Session, joinedload
from uuid import UUID
from typing import Optional, List
from app.templates.infra.component_template_config_model import ComponentTemplateConfig as ComponentTemplateConfigModel
from app.templates.infra.template_model import Template as TemplateModel


class ComponentTemplateConfigRepository:
    """Repository for ComponentTemplateConfig database operations. No business logic here."""

    def __init__(self, database_session: Session):
        self.db = database_session

    def find_by_uuid(self, uuid: UUID) -> Optional[ComponentTemplateConfigModel]:
        """Find component template config by UUID."""
        return (
            self.db.query(ComponentTemplateConfigModel)
            .options(joinedload(ComponentTemplateConfigModel.template))
            .filter(ComponentTemplateConfigModel.uuid == uuid)
            .first()
        )

    def find_by_component_type_and_template_id(
        self, component_type: str, template_id: int
    ) -> Optional[ComponentTemplateConfigModel]:
        """Find config by component type and template ID."""
        return (
            self.db.query(ComponentTemplateConfigModel)
            .filter(
                ComponentTemplateConfigModel.component_type == component_type,
                ComponentTemplateConfigModel.template_id == template_id,
            )
            .first()
        )

    def find_all(
        self, component_type: Optional[str] = None, skip: int = 0, limit: int = 100
    ) -> List[ComponentTemplateConfigModel]:
        """Find all component template configs, optionally filtered by component type."""
        query = (
            self.db.query(ComponentTemplateConfigModel)
            .options(joinedload(ComponentTemplateConfigModel.template))
            .order_by(ComponentTemplateConfigModel.render_order)
        )
        if component_type:
            query = query.filter(ComponentTemplateConfigModel.component_type == component_type)
        return query.offset(skip).limit(limit).all()

    def find_templates_for_component_type(self, component_type: str) -> List[TemplateModel]:
        """Find templates ordered by render_order for a component type."""
        configs = (
            self.db.query(ComponentTemplateConfigModel)
            .join(TemplateModel)
            .filter(
                ComponentTemplateConfigModel.component_type == component_type,
                ComponentTemplateConfigModel.enabled == "true",
            )
            .order_by(ComponentTemplateConfigModel.render_order)
            .all()
        )
        return [config.template for config in configs]

    def create(self, config: ComponentTemplateConfigModel) -> ComponentTemplateConfigModel:
        """Create a new component template config."""
        self.db.add(config)
        try:
            self.db.commit()
            self.db.refresh(config)
            # Load template relationship
            self.db.refresh(config, ["template"])
        except Exception as e:
            self.db.rollback()
            raise Exception(f"Failed to create component template config: {str(e)}")
        return config

    def update(self, config: ComponentTemplateConfigModel) -> ComponentTemplateConfigModel:
        """Update an existing component template config."""
        try:
            self.db.commit()
            self.db.refresh(config)
            # Load template relationship
            self.db.refresh(config, ["template"])
        except Exception as e:
            self.db.rollback()
            raise Exception(f"Failed to update component template config: {str(e)}")
        return config

    def delete(self, config: ComponentTemplateConfigModel) -> None:
        """Delete a component template config."""
        self.db.delete(config)
        try:
            self.db.commit()
        except Exception as e:
            self.db.rollback()
            raise Exception(f"Failed to delete component template config: {str(e)}")

    def rollback(self) -> None:
        """Rollback current transaction."""
        self.db.rollback()

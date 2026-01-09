from sqlalchemy.orm import Session
from uuid import UUID
from typing import Optional, List
from app.environments.infra.environment_model import Environment as EnvironmentModel
from app.webapps.infra.application_component_model import ApplicationComponent as ApplicationComponentModel
from app.instances.infra.instance_model import Instance as InstanceModel


class EnvironmentRepository:
    """Repository for Environment database operations. No business logic here."""

    def __init__(self, database_session: Session):
        self.db = database_session

    def find_by_uuid(self, uuid: UUID) -> Optional[EnvironmentModel]:
        """Find environment by UUID."""
        return self.db.query(EnvironmentModel).filter(EnvironmentModel.uuid == uuid).first()

    def find_by_name(self, name: str) -> Optional[EnvironmentModel]:
        """Find environment by name."""
        return self.db.query(EnvironmentModel).filter(EnvironmentModel.name == name).first()

    def find_all(self, skip: int = 0, limit: int = 100) -> List[EnvironmentModel]:
        """Find all environments."""
        return self.db.query(EnvironmentModel).offset(skip).limit(limit).all()

    def find_components_by_environment_id(self, environment_id: int) -> List[ApplicationComponentModel]:
        """Find all components associated with an environment."""
        return (
            self.db.query(ApplicationComponentModel)
            .join(InstanceModel)
            .filter(InstanceModel.environment_id == environment_id)
            .all()
        )

    def create(self, environment: EnvironmentModel) -> EnvironmentModel:
        """Create a new environment."""
        self.db.add(environment)
        self.db.commit()
        self.db.refresh(environment)
        return environment

    def update(self, environment: EnvironmentModel) -> EnvironmentModel:
        """Update an existing environment."""
        self.db.commit()
        self.db.refresh(environment)
        return environment

    def delete(self, environment: EnvironmentModel) -> None:
        """Delete an environment."""
        self.db.delete(environment)
        self.db.commit()

    def rollback(self) -> None:
        """Rollback current transaction."""
        self.db.rollback()

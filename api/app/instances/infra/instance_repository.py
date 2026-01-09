from sqlalchemy.orm import Session, joinedload
from uuid import UUID
from typing import Optional, List
from app.instances.infra.instance_model import Instance as InstanceModel
from app.applications.infra.application_model import Application as ApplicationModel
from app.environments.infra.environment_model import Environment as EnvironmentModel


class InstanceRepository:
    """Repository for Instance database operations. No business logic here."""

    def __init__(self, database_session: Session):
        self.db = database_session

    def find_by_uuid(self, uuid: UUID, load_components: bool = False) -> Optional[InstanceModel]:
        """Find instance by UUID."""
        query = self.db.query(InstanceModel).filter(InstanceModel.uuid == uuid)
        if load_components:
            query = query.options(joinedload(InstanceModel.components))
        return query.first()

    def find_by_uuid_with_relations(self, uuid: UUID) -> Optional[InstanceModel]:
        """Find instance by UUID with all relations loaded."""
        return (
            self.db.query(InstanceModel)
            .options(
                joinedload(InstanceModel.application),
                joinedload(InstanceModel.environment),
                joinedload(InstanceModel.components)
            )
            .filter(InstanceModel.uuid == uuid)
            .first()
        )

    def find_by_application_and_environment(
        self,
        application_id: int,
        environment_id: int
    ) -> Optional[InstanceModel]:
        """Find instance by application and environment."""
        return (
            self.db.query(InstanceModel)
            .filter(
                InstanceModel.application_id == application_id,
                InstanceModel.environment_id == environment_id
            )
            .first()
        )

    def find_all(self, skip: int = 0, limit: int = 100, load_components: bool = False) -> List[InstanceModel]:
        """Find all instances."""
        query = self.db.query(InstanceModel).offset(skip).limit(limit)
        if load_components:
            query = query.options(joinedload(InstanceModel.components))
        return query.all()

    def find_application_by_uuid(self, uuid: UUID) -> Optional[ApplicationModel]:
        """Find application by UUID."""
        return self.db.query(ApplicationModel).filter(ApplicationModel.uuid == uuid).first()

    def find_environment_by_uuid(self, uuid: UUID) -> Optional[EnvironmentModel]:
        """Find environment by UUID."""
        return self.db.query(EnvironmentModel).filter(EnvironmentModel.uuid == uuid).first()

    def create(self, instance: InstanceModel) -> InstanceModel:
        """Create a new instance."""
        self.db.add(instance)
        self.db.commit()
        self.db.refresh(instance)
        return instance

    def update(self, instance: InstanceModel) -> InstanceModel:
        """Update an existing instance."""
        self.db.commit()
        self.db.refresh(instance)
        return instance

    def delete_by_id(self, instance_id: int) -> None:
        """Delete instance by ID."""
        from sqlalchemy import delete
        stmt = delete(InstanceModel).where(InstanceModel.id == instance_id)
        self.db.execute(stmt)
        self.db.commit()

    def rollback(self) -> None:
        """Rollback current transaction."""
        self.db.rollback()

from sqlalchemy.orm import Session, joinedload
from uuid import UUID
from typing import Optional, List
from app.cron.infra.application_component_model import ApplicationComponent as ApplicationComponentModel, WebappType
from app.instances.infra.instance_model import Instance as InstanceModel
from app.shared.infra.cluster_instance_model import ClusterInstance as ClusterInstanceModel
from app.settings.infra.settings_model import Settings as SettingsModel


class CronRepository:
    """Repository for Cron database operations. No business logic here."""

    def __init__(self, database_session: Session):
        self.db = database_session

    def find_by_uuid(self, uuid: UUID, load_relations: bool = False) -> Optional[ApplicationComponentModel]:
        """Find cron by UUID."""
        query = self.db.query(ApplicationComponentModel).filter(
            ApplicationComponentModel.uuid == uuid,
            ApplicationComponentModel.type == WebappType.cron
        )
        if load_relations:
            query = query.options(
                joinedload(ApplicationComponentModel.instance)
                .joinedload(InstanceModel.application),
                joinedload(ApplicationComponentModel.instance)
                .joinedload(InstanceModel.environment),
                joinedload(ApplicationComponentModel.instances)
                .joinedload(ClusterInstanceModel.cluster)
            )
        return query.first()

    def find_all(self, skip: int = 0, limit: int = 100) -> List[ApplicationComponentModel]:
        """Find all crons."""
        return (
            self.db.query(ApplicationComponentModel)
            .filter(ApplicationComponentModel.type == WebappType.cron)
            .offset(skip)
            .limit(limit)
            .all()
        )

    def find_instance_by_uuid(self, uuid: UUID) -> Optional[InstanceModel]:
        """Find instance by UUID."""
        return self.db.query(InstanceModel).filter(InstanceModel.uuid == uuid).first()

    def find_cluster_instance_by_component_id(self, component_id: int) -> Optional[ClusterInstanceModel]:
        """Find cluster instance by component ID."""
        return (
            self.db.query(ClusterInstanceModel)
            .filter(ClusterInstanceModel.application_component_id == component_id)
            .first()
        )

    def find_settings_by_environment_id(self, environment_id: int) -> List[SettingsModel]:
        """Find settings by environment ID."""
        return (
            self.db.query(SettingsModel)
            .filter(SettingsModel.environment_id == environment_id)
            .all()
        )

    def create(self, cron: ApplicationComponentModel) -> ApplicationComponentModel:
        """Create a new cron."""
        self.db.add(cron)
        try:
            self.db.commit()
            self.db.refresh(cron)
        except Exception as e:
            self.db.rollback()
            raise Exception(f"Failed to create cron: {str(e)}")
        return cron

    def update(self, cron: ApplicationComponentModel) -> ApplicationComponentModel:
        """Update an existing cron."""
        try:
            self.db.commit()
            self.db.refresh(cron)
        except Exception as e:
            self.db.rollback()
            raise Exception(f"Failed to update cron: {str(e)}")
        return cron

    def delete(self, cron: ApplicationComponentModel) -> None:
        """Delete a cron."""
        self.db.delete(cron)
        try:
            self.db.commit()
        except Exception as e:
            self.db.rollback()
            raise Exception(f"Failed to delete cron: {str(e)}")

    def create_cluster_instance(self, cluster_instance: ClusterInstanceModel) -> ClusterInstanceModel:
        """Create a cluster instance."""
        self.db.add(cluster_instance)
        return cluster_instance

    def delete_cluster_instance(self, cluster_instance: ClusterInstanceModel) -> None:
        """Delete a cluster instance."""
        self.db.delete(cluster_instance)

    def rollback(self) -> None:
        """Rollback current transaction."""
        self.db.rollback()

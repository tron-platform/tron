from sqlalchemy.orm import Session
from sqlalchemy import func
from app.applications.infra.application_model import Application as ApplicationModel
from app.instances.infra.instance_model import Instance as InstanceModel
from app.webapps.infra.application_component_model import ApplicationComponent as ApplicationComponentModel
from app.clusters.infra.cluster_model import Cluster as ClusterModel
from app.environments.infra.environment_model import Environment as EnvironmentModel
from app.shared.infra.cluster_instance_model import ClusterInstance as ClusterInstanceModel


class DashboardRepository:
    """Repository for Dashboard database operations. No business logic here."""

    def __init__(self, database_session: Session):
        self.db = database_session

    def count_applications(self) -> int:
        """Count total applications."""
        return self.db.query(func.count(ApplicationModel.id)).scalar() or 0

    def count_instances(self) -> int:
        """Count total instances."""
        return self.db.query(func.count(InstanceModel.id)).scalar() or 0

    def count_total_components(self) -> int:
        """Count total components."""
        return self.db.query(func.count(ApplicationComponentModel.id)).scalar() or 0

    def count_components_by_type(self, component_type: str) -> int:
        """Count components by type."""
        return (
            self.db.query(func.count(ApplicationComponentModel.id))
            .filter(ApplicationComponentModel.type == component_type)
            .scalar() or 0
        )

    def count_enabled_components(self) -> int:
        """Count enabled components."""
        return (
            self.db.query(func.count(ApplicationComponentModel.id))
            .filter(ApplicationComponentModel.enabled == True)
            .scalar() or 0
        )

    def count_disabled_components(self) -> int:
        """Count disabled components."""
        return (
            self.db.query(func.count(ApplicationComponentModel.id))
            .filter(ApplicationComponentModel.enabled == False)
            .scalar() or 0
        )

    def count_clusters(self) -> int:
        """Count total clusters."""
        return self.db.query(func.count(ClusterModel.id)).scalar() or 0

    def count_environments(self) -> int:
        """Count total environments."""
        return self.db.query(func.count(EnvironmentModel.id)).scalar() or 0

    def get_components_by_environment(self) -> list:
        """Get components count grouped by environment."""
        return (
            self.db.query(
                EnvironmentModel.name,
                func.count(ApplicationComponentModel.id)
            )
            .join(InstanceModel, InstanceModel.environment_id == EnvironmentModel.id)
            .join(ApplicationComponentModel, ApplicationComponentModel.instance_id == InstanceModel.id)
            .group_by(EnvironmentModel.name)
            .all()
        )

    def get_components_by_cluster(self) -> list:
        """Get components count grouped by cluster."""
        return (
            self.db.query(
                ClusterModel.name,
                func.count(ApplicationComponentModel.id)
            )
            .join(ClusterInstanceModel, ClusterInstanceModel.cluster_id == ClusterModel.id)
            .join(ApplicationComponentModel, ApplicationComponentModel.id == ClusterInstanceModel.application_component_id)
            .group_by(ClusterModel.name)
            .all()
        )

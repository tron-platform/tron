from sqlalchemy.orm import Session
from uuid import UUID
from typing import Optional, List
from app.clusters.infra.cluster_model import Cluster as ClusterModel
from app.environments.infra.environment_model import Environment as EnvironmentModel


class ClusterRepository:
    """Repository for Cluster database operations. No business logic here."""

    def __init__(self, database_session: Session):
        self.db = database_session

    def find_by_uuid(self, uuid: UUID) -> Optional[ClusterModel]:
        """Find cluster by UUID."""
        return self.db.query(ClusterModel).filter(ClusterModel.uuid == uuid).first()

    def find_by_name(self, name: str) -> Optional[ClusterModel]:
        """Find cluster by name."""
        return self.db.query(ClusterModel).filter(ClusterModel.name == name).first()

    def find_by_api_address(self, api_address: str) -> Optional[ClusterModel]:
        """Find cluster by API address."""
        return self.db.query(ClusterModel).filter(ClusterModel.api_address == api_address).first()

    def find_all(self, skip: int = 0, limit: int = 100) -> List[ClusterModel]:
        """Find all clusters."""
        return self.db.query(ClusterModel).offset(skip).limit(limit).all()

    def find_environment_by_uuid(self, uuid: UUID) -> Optional[EnvironmentModel]:
        """Find environment by UUID."""
        return self.db.query(EnvironmentModel).filter(EnvironmentModel.uuid == uuid).first()

    def create(self, cluster: ClusterModel) -> ClusterModel:
        """Create a new cluster."""
        self.db.add(cluster)
        self.db.commit()
        self.db.refresh(cluster)
        return cluster

    def update(self, cluster: ClusterModel) -> ClusterModel:
        """Update an existing cluster."""
        self.db.commit()
        self.db.refresh(cluster)
        return cluster

    def delete(self, cluster: ClusterModel) -> None:
        """Delete a cluster."""
        self.db.delete(cluster)
        self.db.commit()

    def rollback(self) -> None:
        """Rollback current transaction."""
        self.db.rollback()

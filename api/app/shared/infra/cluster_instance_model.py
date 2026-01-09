from sqlalchemy import Column, Integer, String, DateTime, UniqueConstraint, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.shared.database.database import Base
from sqlalchemy.dialects.postgresql import UUID
from uuid import uuid4
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.clusters.infra.cluster_model import Cluster
    from app.webapps.infra.application_component_model import ApplicationComponent


class ClusterInstance(Base):
    __tablename__ = "cluster_instances"

    id = Column(Integer, primary_key=True, index=True)
    uuid = Column(UUID(as_uuid=True), default=uuid4, unique=True, nullable=False)

    application_component_id = Column(Integer, ForeignKey("application_components.id"), nullable=False)
    application_component = relationship(
        "ApplicationComponent",
        back_populates="instances",
        foreign_keys=[application_component_id],
        lazy="select"
    )

    cluster_id = Column(Integer, ForeignKey("clusters.id"), nullable=False)
    cluster = relationship(
        "Cluster",
        back_populates="instances",
        foreign_keys=[cluster_id],
        lazy="select"
    )

    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), server_onupdate=func.now(), nullable=False)

    __table_args__ = (
        UniqueConstraint('cluster_id', 'application_component_id', name='cluster_instance_cluster_id'),
    )

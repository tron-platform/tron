import enum
from sqlalchemy import Column, Integer, String, ForeignKey, Boolean, Enum, JSON, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from uuid import uuid4
from app.shared.database.database import Base


class WebappProtocolType(str, enum.Enum):
    http = "http"
    https = "https"
    tcp = "tcp"
    tls = "tls"


class WebappType(str, enum.Enum):
    webapp = "webapp"
    worker = "worker"
    cron = "cron"


class VisibilityType(str, enum.Enum):
    public = "public"
    private = "private"
    cluster = "cluster"


class ApplicationComponent(Base):
    __tablename__ = "application_components"

    id = Column(Integer, primary_key=True, index=True)
    uuid = Column(UUID(as_uuid=True), default=uuid4, unique=True, nullable=False)

    instance_id = Column(Integer, ForeignKey("instances.id"), nullable=False)
    instance = relationship("Instance", back_populates="components")

    name = Column(String, nullable=False)
    type = Column(Enum(WebappType), nullable=False, default=WebappType.webapp)

    settings = Column(JSON, nullable=True)

    url = Column(String, unique=True, nullable=True)
    enabled = Column(Boolean, nullable=False, default=True)

    instances = relationship(
        "ClusterInstance",
        back_populates="application_component",
        foreign_keys="[ClusterInstance.application_component_id]",
        lazy="select"
    )

    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), server_onupdate=func.now(), nullable=False)

    __table_args__ = ()

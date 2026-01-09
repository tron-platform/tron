from sqlalchemy import Column, Integer, String, DateTime, UniqueConstraint
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.shared.database.database import Base
from sqlalchemy.dialects.postgresql import UUID
from uuid import uuid4


class Environment(Base):
    __tablename__ = "environments"

    id = Column(Integer, primary_key=True, index=True)
    uuid = Column(UUID(as_uuid=True), default=uuid4, unique=True, nullable=False)
    name = Column(String, unique=True, index=True)

    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), server_onupdate=func.now(), nullable=False)

    settings = relationship("Settings", back_populates="environment")
    clusters = relationship("Cluster", back_populates="environment")
    instances = relationship("Instance", back_populates="environment")

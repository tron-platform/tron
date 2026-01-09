from sqlalchemy import Column, String, JSON, Integer, ForeignKey, DateTime, UniqueConstraint
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.shared.database.database import Base
from sqlalchemy.dialects.postgresql import UUID
from uuid import uuid4


class Settings(Base):
    __tablename__ = "settings"

    id = Column(Integer, primary_key=True)
    uuid = Column(UUID(as_uuid=True), default=uuid4, unique=True, nullable=False)
    key = Column(String, nullable=False)
    value = Column(JSON, nullable=False)
    description = Column(String)

    environment_id = Column(Integer, ForeignKey('environments.id'), nullable=False)
    environment = relationship("Environment", back_populates="settings")

    __table_args__ = (UniqueConstraint('key', 'environment_id', name='uq_key_environment'),)

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.shared.database.database import Base
from sqlalchemy.dialects.postgresql import UUID
from uuid import uuid4
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.templates.infra.template_model import Template


class ComponentTemplateConfig(Base):
    __tablename__ = "component_template_configs"

    id = Column(Integer, primary_key=True, index=True)
    uuid = Column(UUID(as_uuid=True), default=uuid4, unique=True, nullable=False)

    component_type = Column(String, nullable=False, index=True)  # webapp, cron, worker
    template_id = Column(Integer, ForeignKey("templates.id"), nullable=False)
    template = relationship("Template", back_populates="component_configs")

    render_order = Column(Integer, nullable=False, default=0)  # Ordem de renderização
    enabled = Column(String, nullable=False, default="true")  # "true" ou "false" como string para compatibilidade

    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), server_onupdate=func.now(), nullable=False)

    __table_args__ = (
        UniqueConstraint('component_type', 'template_id', name='uix_component_type_template'),
    )

from sqlalchemy import Column, Integer, String, DateTime, Text, UniqueConstraint
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.shared.database.database import Base
from sqlalchemy.dialects.postgresql import UUID
from uuid import uuid4


class Template(Base):
    __tablename__ = "templates"

    id = Column(Integer, primary_key=True, index=True)
    uuid = Column(UUID(as_uuid=True), default=uuid4, unique=True, nullable=False)
    name = Column(String, nullable=False, index=True)
    description = Column(String, nullable=True)
    category = Column(String, nullable=False, index=True)  # webapp, cron, worker, etc.
    content = Column(Text, nullable=False)  # Conteúdo do template Jinja2
    variables_schema = Column(Text, nullable=True)  # JSON com schema das variáveis disponíveis

    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), server_onupdate=func.now(), nullable=False)

    component_configs = relationship(
        "ComponentTemplateConfig",
        back_populates="template",
        lazy="select"
    )

from sqlalchemy.orm import Session, joinedload
from sqlalchemy import delete
from uuid import UUID
from typing import Optional, List
from app.applications.infra.application_model import Application as ApplicationModel


class ApplicationRepository:
    """Repository for Application database operations. No business logic here."""

    def __init__(self, database_session: Session):
        self.db = database_session

    def find_by_uuid(self, uuid: UUID) -> Optional[ApplicationModel]:
        """Find application by UUID."""
        return self.db.query(ApplicationModel).filter(ApplicationModel.uuid == uuid).first()

    def find_by_name(self, name: str) -> Optional[ApplicationModel]:
        """Find application by name."""
        return self.db.query(ApplicationModel).filter(ApplicationModel.name == name).first()

    def find_by_name_excluding_uuid(self, name: str, exclude_uuid: UUID) -> Optional[ApplicationModel]:
        """Find application by name excluding a specific UUID."""
        return (
            self.db.query(ApplicationModel)
            .filter(
                ApplicationModel.name == name,
                ApplicationModel.uuid != exclude_uuid
            )
            .first()
        )

    def find_all_with_instances(self, skip: int = 0, limit: int = 100) -> List[ApplicationModel]:
        """Find all applications with instances loaded."""
        return (
            self.db.query(ApplicationModel)
            .options(joinedload(ApplicationModel.instances))
            .offset(skip)
            .limit(limit)
            .all()
        )

    def find_all(self, skip: int = 0, limit: int = 100) -> List[ApplicationModel]:
        """Find all applications."""
        return self.db.query(ApplicationModel).offset(skip).limit(limit).all()

    def create(self, application: ApplicationModel) -> ApplicationModel:
        """Create a new application."""
        self.db.add(application)
        self.db.commit()
        self.db.refresh(application)
        return application

    def update(self, application: ApplicationModel) -> ApplicationModel:
        """Update an existing application."""
        # Ensure created_at is not modified during update
        # Store original created_at to prevent SQLAlchemy from trying to update it
        original_created_at = application.created_at
        self.db.commit()
        # Restore created_at in case it was modified
        if hasattr(application, 'created_at') and application.created_at != original_created_at:
            application.created_at = original_created_at
        self.db.refresh(application)
        return application

    def delete_by_id(self, application_id: int) -> None:
        """Delete application by ID."""
        stmt = delete(ApplicationModel).where(ApplicationModel.id == application_id)
        self.db.execute(stmt)
        self.db.commit()

    def rollback(self) -> None:
        """Rollback current transaction."""
        self.db.rollback()

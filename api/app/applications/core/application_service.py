from uuid import uuid4, UUID
from typing import List
from sqlalchemy.orm import Session

from app.applications.infra.application_repository import ApplicationRepository
from app.applications.infra.application_model import Application as ApplicationModel
from app.applications.api.application_dto import ApplicationCreate, ApplicationUpdate, Application
from app.applications.core.application_validators import (
    validate_application_create_dto,
    validate_application_update_dto,
    validate_application_name_uniqueness,
    validate_application_exists,
    ApplicationNotFoundError,
    ApplicationNameAlreadyExistsError
)
from app.instances.core.instance_service import InstanceService
from app.instances.infra.instance_repository import InstanceRepository


class ApplicationService:
    """Business logic for applications. No direct database access."""

    def __init__(self, repository: ApplicationRepository, instance_service: InstanceService = None):
        self.repository = repository
        self.instance_service = instance_service

    def create_application(self, dto: ApplicationCreate) -> Application:
        """Create a new application."""
        validate_application_create_dto(dto)
        validate_application_name_uniqueness(self.repository, dto.name)

        application = self._build_application_entity(dto)
        return self.repository.create(application)

    def update_application(self, uuid: UUID, dto: ApplicationUpdate) -> Application:
        """Update an existing application."""
        validate_application_update_dto(dto)
        validate_application_exists(self.repository, uuid)

        application = self.repository.find_by_uuid(uuid)

        if dto.name is not None:
            validate_application_name_uniqueness(self.repository, dto.name, exclude_uuid=uuid)
            application.name = dto.name

        if dto.repository is not None:
            application.repository = dto.repository

        if dto.enabled is not None:
            application.enabled = dto.enabled

        return self.repository.update(application)

    def get_application(self, uuid: UUID) -> Application:
        """Get application by UUID."""
        validate_application_exists(self.repository, uuid)
        return self.repository.find_by_uuid(uuid)

    def get_applications(self, skip: int = 0, limit: int = 100) -> List[Application]:
        """Get all applications."""
        return self.repository.find_all(skip=skip, limit=limit)

    def delete_application(self, uuid: UUID, database_session: Session) -> dict:
        """Delete an application and all its instances."""
        validate_application_exists(self.repository, uuid)

        application = self.repository.find_by_uuid(uuid)
        instances = application.instances

        # Delete all instances
        if not self.instance_service:
            # Create instance service if not provided
            instance_repository = InstanceRepository(database_session)
            self.instance_service = InstanceService(instance_repository)

        for instance in instances:
            try:
                self.instance_service.delete_instance(instance.uuid, database_session)
            except Exception as e:
                self.repository.rollback()
                raise Exception(f"Failed to delete instance '{instance.uuid}': {str(e)}")

        # Delete application
        try:
            self.repository.delete_by_id(application.id)
        except Exception as e:
            self.repository.rollback()
            raise Exception(f"Failed to delete application: {str(e)}")

        return {"detail": "Application deleted successfully"}

    def _build_application_entity(self, dto: ApplicationCreate) -> ApplicationModel:
        """Build Application entity from DTO."""
        return ApplicationModel(
            uuid=uuid4(),
            name=dto.name,
            repository=dto.repository,
            enabled=dto.enabled,
        )

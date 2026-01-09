from uuid import uuid4, UUID
from typing import List
from sqlalchemy.orm import Session

from app.instances.infra.instance_repository import InstanceRepository
from app.instances.infra.instance_model import Instance as InstanceModel
from app.instances.api.instance_dto import InstanceCreate, InstanceUpdate, Instance
from app.instances.core.instance_validators import (
    validate_instance_create_dto,
    validate_instance_update_dto,
    validate_instance_exists,
    validate_instance_uniqueness,
    validate_application_exists,
    validate_environment_exists,
    InstanceNotFoundError,
    InstanceAlreadyExistsError,
    ApplicationNotFoundError,
    EnvironmentNotFoundError
)
from app.webapps.infra.application_component_model import ApplicationComponent as ApplicationComponentModel, WebappType
from app.shared.infra.cluster_instance_model import ClusterInstance as ClusterInstanceModel
from app.shared.core.application_component_helpers import get_or_create_cluster_instance
from app.shared.serializers.serializers import serialize_settings
from app.webapps.core.webapp_kubernetes_service import upsert_to_kubernetes as upsert_webapp_to_k8s
from app.workers.core.worker_kubernetes_service import upsert_to_kubernetes as upsert_worker_to_k8s
from app.cron.core.cron_kubernetes_service import upsert_to_kubernetes as upsert_cron_to_k8s


class InstanceService:
    """Business logic for instances. No direct database access."""

    def __init__(self, repository: InstanceRepository, database_session: Session = None):
        self.repository = repository
        self.db = database_session

    def create_instance(self, dto: InstanceCreate) -> Instance:
        """Create a new instance."""
        validate_instance_create_dto(dto)

        # Validate application and environment exist
        validate_application_exists(self.repository, dto.application_uuid)
        validate_environment_exists(self.repository, dto.environment_uuid)

        application = self.repository.find_application_by_uuid(dto.application_uuid)
        environment = self.repository.find_environment_by_uuid(dto.environment_uuid)

        # Validate uniqueness
        validate_instance_uniqueness(
            self.repository,
            application.id,
            environment.id
        )

        instance = self._build_instance_entity(dto, application.id, environment.id)
        return self.repository.create(instance)

    def update_instance(self, uuid: UUID, dto: InstanceUpdate) -> Instance:
        """Update an existing instance."""
        validate_instance_update_dto(dto)
        validate_instance_exists(self.repository, uuid)

        instance = self.repository.find_by_uuid(uuid)

        if dto.image is not None:
            instance.image = dto.image

        if dto.version is not None:
            instance.version = dto.version

        if dto.enabled is not None:
            instance.enabled = dto.enabled

        # TODO: Handle Kubernetes sync when image/version/enabled changes
        # This will be implemented when Kubernetes features are migrated

        return self.repository.update(instance)

    def get_instance(self, uuid: UUID) -> Instance:
        """Get instance by UUID."""
        validate_instance_exists(self.repository, uuid)
        return self.repository.find_by_uuid(uuid, load_components=True)

    def get_instances(self, skip: int = 0, limit: int = 100) -> List[Instance]:
        """Get all instances."""
        return self.repository.find_all(skip=skip, limit=limit, load_components=True)

    def delete_instance(self, uuid: UUID, database_session: Session) -> dict:
        """Delete an instance and all its components."""
        validate_instance_exists(self.repository, uuid)

        instance = self.repository.find_by_uuid(uuid, load_components=True)

        # TODO: Delete components from Kubernetes
        # This will be implemented when component features are migrated

        try:
            self.repository.delete_by_id(instance.id)
        except Exception as e:
            self.repository.rollback()
            raise Exception(f"Failed to delete instance: {str(e)}")

        return {"detail": "Instance deleted successfully"}

    def get_instance_events(self, uuid: UUID) -> List:
        """Get Kubernetes events for an instance."""
        validate_instance_exists(self.repository, uuid)

        # TODO: Implement Kubernetes events retrieval
        # This will be implemented when Kubernetes features are migrated
        raise NotImplementedError("Instance events not yet migrated to new structure")

    def sync_instance(self, uuid: UUID) -> dict:
        """Sync instance components with Kubernetes."""
        validate_instance_exists(self.repository, uuid)

        if not self.db:
            raise ValueError("Database session is required for sync")

        instance = self.repository.find_by_uuid_with_relations(uuid)
        if not instance:
            raise InstanceNotFoundError(f"Instance with UUID {uuid} not found")

        # Get settings for the environment
        from app.settings.infra.settings_model import Settings as SettingsModel
        settings = self.db.query(SettingsModel).filter(
            SettingsModel.environment_id == instance.environment_id
        ).first()
        settings_serialized = serialize_settings(settings) if settings else {}

        synced_components = 0
        total_components = len([c for c in instance.components if c.enabled])
        errors = []

        # Sync each enabled component
        for component in instance.components:
            if not component.enabled:
                continue

            try:
                # Get or create cluster instance
                cluster_instance = get_or_create_cluster_instance(
                    self._get_component_repository(component),
                    self.db,
                    component
                )
                cluster = cluster_instance.cluster

                # Determine component type and use appropriate upsert function
                if isinstance(component.type, WebappType):
                    component_type = component.type.value
                else:
                    component_type = str(component.type)

                if component_type == WebappType.webapp.value:
                    upsert_func = upsert_webapp_to_k8s
                elif component_type == WebappType.worker.value:
                    upsert_func = upsert_worker_to_k8s
                elif component_type == WebappType.cron.value:
                    upsert_func = upsert_cron_to_k8s
                else:
                    errors.append({
                        "component": component.name,
                        "error": f"Unknown component type: {component_type}"
                    })
                    continue

                # Deploy to Kubernetes
                upsert_func(cluster, component, settings_serialized, self.db)
                self.db.commit()
                self.db.refresh(component)
                self.db.refresh(cluster_instance)

                synced_components += 1
            except Exception as e:
                self.db.rollback()
                errors.append({
                    "component": component.name,
                    "error": str(e)
                })

        return {
            "detail": f"Sync completed. {synced_components}/{total_components} components synced.",
            "synced_components": synced_components,
            "total_components": total_components,
            "errors": errors
        }

    def _get_component_repository(self, component: ApplicationComponentModel):
        """Get appropriate repository for component type."""
        component_type = component.type.value if hasattr(component.type, 'value') else str(component.type)

        if component_type == 'webapp':
            from app.webapps.infra.webapp_repository import WebappRepository
            return WebappRepository(self.db)
        elif component_type == 'worker':
            from app.workers.infra.worker_repository import WorkerRepository
            return WorkerRepository(self.db)
        elif component_type == 'cron':
            from app.cron.infra.cron_repository import CronRepository
            return CronRepository(self.db)
        else:
            raise ValueError(f"Unknown component type: {component_type}")

    def _build_instance_entity(
        self,
        dto: InstanceCreate,
        application_id: int,
        environment_id: int
    ) -> InstanceModel:
        """Build Instance entity from DTO."""
        return InstanceModel(
            uuid=uuid4(),
            application_id=application_id,
            environment_id=environment_id,
            image=dto.image,
            version=dto.version,
            enabled=dto.enabled,
        )

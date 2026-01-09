"""Business logic for workers. Broken into small, focused functions."""
from uuid import uuid4, UUID
from typing import List
from sqlalchemy.orm import Session

from app.workers.infra.worker_repository import WorkerRepository
from app.workers.infra.application_component_model import ApplicationComponent as ApplicationComponentModel, WebappType
from app.workers.api.worker_dto import WorkerCreate, WorkerUpdate, Worker
from app.workers.core.worker_validators import (
    validate_worker_create_dto,
    validate_worker_update_dto,
    validate_worker_exists,
    validate_worker_type,
    validate_instance_exists,
    WorkerNotFoundError,
    WorkerNotWorkerTypeError,
    InstanceNotFoundError
)
from app.workers.core.worker_kubernetes_service import (
    delete_from_kubernetes,
    upsert_to_kubernetes
)
from app.shared.serializers.serializers import serialize_settings
from app.shared.infra.cluster_instance_model import ClusterInstance as ClusterInstanceModel
from app.shared.core.application_component_helpers import (
    get_cluster_for_instance,
    ensure_cluster_instance,
    get_or_create_cluster_instance,
    handle_enabled_change,
    deploy_to_kubernetes,
    delete_from_kubernetes_safe,
    ensure_private_exposure_settings,
    delete_component,
    update_component_enabled_field,
    build_application_component_entity
)


class WorkerService:
    """Business logic for workers. No direct database access."""

    def __init__(self, repository: WorkerRepository, database_session: Session):
        self.repository = repository
        self.db = database_session

    def create_worker(self, dto: WorkerCreate) -> Worker:
        """Create a new worker."""
        validate_worker_create_dto(dto)
        validate_instance_exists(self.repository, dto.instance_uuid)

        instance = self.repository.find_instance_by_uuid(dto.instance_uuid)
        cluster = get_cluster_for_instance(self.db, instance)

        settings_dict = ensure_private_exposure_settings(dto.settings.model_dump())
        worker = self._build_worker_entity(dto, instance.id, settings_dict)
        worker = self.repository.create(worker)

        cluster_instance = ensure_cluster_instance(self.repository, worker, cluster)
        self._deploy_to_kubernetes(worker, instance.environment_id, cluster, cluster_instance)

        return self._serialize_worker(worker)

    def update_worker(self, uuid: UUID, dto: WorkerUpdate) -> Worker:
        """Update an existing worker."""
        validate_worker_update_dto(dto)
        validate_worker_exists(self.repository, uuid)

        worker = self.repository.find_by_uuid(uuid)
        validate_worker_type(worker)

        # Check if there are any changes that require Kubernetes update
        has_changes = dto.settings is not None or dto.enabled is not None

        enabled_changed = self._update_worker_fields(worker, dto)
        cluster_instance = get_or_create_cluster_instance(self.repository, self.db, worker)
        cluster = cluster_instance.cluster

        if enabled_changed['changed']:
            # Handle enabled status change
            handle_enabled_change(
                worker, enabled_changed, cluster, cluster_instance,
                lambda c, cl: self._delete_from_kubernetes_safe(c, cl),
                lambda c, eid, cl, ci: self._deploy_to_kubernetes(c, eid, cl, ci)
            )
        elif worker.enabled and has_changes:
            # If worker is enabled and there are changes, always redeploy to apply new configs
            self._deploy_to_kubernetes(worker, worker.instance.environment_id, cluster, cluster_instance)

        return self._serialize_worker(worker)

    def get_worker(self, uuid: UUID) -> Worker:
        """Get worker by UUID."""
        validate_worker_exists(self.repository, uuid)
        worker = self.repository.find_by_uuid(uuid)
        validate_worker_type(worker)
        return self._serialize_worker(worker)

    def get_workers(self, skip: int = 0, limit: int = 100) -> List[Worker]:
        """Get all workers."""
        workers = self.repository.find_all(skip=skip, limit=limit)
        return [self._serialize_worker(w) for w in workers]

    def delete_worker(self, uuid: UUID) -> dict:
        """Delete a worker."""
        validate_worker_exists(self.repository, uuid)

        worker = self.repository.find_by_uuid(uuid, load_relations=True)
        validate_worker_type(worker)

        return delete_component(
            worker, self.repository, self.db,
            lambda c, cl: self._delete_from_kubernetes_safe(c, cl),
            'worker'
        )


    def _build_worker_entity(
        self,
        dto: WorkerCreate,
        instance_id: int,
        settings_dict: dict
    ) -> ApplicationComponentModel:
        """Build worker entity from DTO."""
        return build_application_component_entity(
            name=dto.name,
            instance_id=instance_id,
            settings_dict=settings_dict,
            component_type=WebappType.worker,
            url=None,  # Workers don't have URLs
            enabled=dto.enabled
        )


    def _update_worker_fields(
        self,
        worker: ApplicationComponentModel,
        dto: WorkerUpdate
    ) -> dict:
        """Update worker fields from DTO. Returns enabled change info."""
        enabled_changed = update_component_enabled_field(worker, dto.enabled, self.repository)

        if dto.settings is not None:
            worker.settings = dto.settings.model_dump()
            self.repository.update(worker)

        return enabled_changed


    def _deploy_to_kubernetes(
        self,
        worker: ApplicationComponentModel,
        environment_id: int,
        cluster: any,
        cluster_instance: ClusterInstanceModel
    ) -> None:
        """Deploy worker to Kubernetes."""
        deploy_to_kubernetes(
            worker, environment_id, cluster, cluster_instance,
            self.db, self.repository, upsert_to_kubernetes, 'worker'
        )

    def _delete_from_kubernetes_safe(
        self,
        worker: ApplicationComponentModel,
        cluster: any
    ) -> None:
        """Safely delete worker from Kubernetes (logs errors but doesn't fail)."""
        delete_from_kubernetes_safe(
            worker, cluster, self.db, self.repository, delete_from_kubernetes, 'worker'
        )

    def _serialize_worker(self, worker: ApplicationComponentModel) -> Worker:
        """Serialize worker to DTO."""
        return Worker.model_validate(worker)

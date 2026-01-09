"""Business logic for crons. Broken into small, focused functions."""
from uuid import uuid4, UUID
from typing import List
from sqlalchemy.orm import Session

from app.cron.infra.cron_repository import CronRepository
from app.cron.infra.application_component_model import ApplicationComponent as ApplicationComponentModel, WebappType
from app.cron.api.cron_dto import CronCreate, CronUpdate, Cron
from app.cron.core.cron_validators import (
    validate_cron_create_dto,
    validate_cron_update_dto,
    validate_cron_exists,
    validate_cron_type,
    validate_instance_exists,
    CronNotFoundError,
    CronNotCronTypeError,
    InstanceNotFoundError
)
from app.cron.core.cron_kubernetes_service import (
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


class CronService:
    """Business logic for crons. No direct database access."""

    def __init__(self, repository: CronRepository, database_session: Session):
        self.repository = repository
        self.db = database_session

    def create_cron(self, dto: CronCreate) -> Cron:
        """Create a new cron."""
        validate_cron_create_dto(dto)
        validate_instance_exists(self.repository, dto.instance_uuid)

        instance = self.repository.find_instance_by_uuid(dto.instance_uuid)
        cluster = get_cluster_for_instance(self.db, instance)

        settings_dict = ensure_private_exposure_settings(dto.settings.model_dump())
        cron = self._build_cron_entity(dto, instance.id, settings_dict)
        cron = self.repository.create(cron)

        cluster_instance = ensure_cluster_instance(self.repository, cron, cluster)
        self._deploy_to_kubernetes(cron, instance.environment_id, cluster, cluster_instance)

        return self._serialize_cron(cron)

    def update_cron(self, uuid: UUID, dto: CronUpdate) -> Cron:
        """Update an existing cron."""
        validate_cron_update_dto(dto)
        validate_cron_exists(self.repository, uuid)

        cron = self.repository.find_by_uuid(uuid)
        validate_cron_type(cron)

        # Check if there are any changes that require Kubernetes update
        has_changes = dto.settings is not None or dto.enabled is not None

        enabled_changed = self._update_cron_fields(cron, dto)
        cluster_instance = get_or_create_cluster_instance(self.repository, self.db, cron)
        cluster = cluster_instance.cluster

        if enabled_changed['changed']:
            # Handle enabled status change
            handle_enabled_change(
                cron, enabled_changed, cluster, cluster_instance,
                lambda c, cl: self._delete_from_kubernetes_safe(c, cl),
                lambda c, eid, cl, ci: self._deploy_to_kubernetes(c, eid, cl, ci)
            )
        elif cron.enabled and has_changes:
            # If cron is enabled and there are changes, always redeploy to apply new configs
            self._deploy_to_kubernetes(cron, cron.instance.environment_id, cluster, cluster_instance)

        return self._serialize_cron(cron)

    def get_cron(self, uuid: UUID) -> Cron:
        """Get cron by UUID."""
        validate_cron_exists(self.repository, uuid)
        cron = self.repository.find_by_uuid(uuid)
        validate_cron_type(cron)
        return self._serialize_cron(cron)

    def get_crons(self, skip: int = 0, limit: int = 100) -> List[Cron]:
        """Get all crons."""
        crons = self.repository.find_all(skip=skip, limit=limit)
        return [self._serialize_cron(c) for c in crons]

    def delete_cron(self, uuid: UUID) -> dict:
        """Delete a cron."""
        validate_cron_exists(self.repository, uuid)

        cron = self.repository.find_by_uuid(uuid, load_relations=True)
        validate_cron_type(cron)

        return delete_component(
            cron, self.repository, self.db,
            lambda c, cl: self._delete_from_kubernetes_safe(c, cl),
            'cron'
        )


    def _build_cron_entity(
        self,
        dto: CronCreate,
        instance_id: int,
        settings_dict: dict
    ) -> ApplicationComponentModel:
        """Build cron entity from DTO."""
        return build_application_component_entity(
            name=dto.name,
            instance_id=instance_id,
            settings_dict=settings_dict,
            component_type=WebappType.cron,
            url=None,  # Crons don't have URLs
            enabled=dto.enabled
        )


    def _update_cron_fields(
        self,
        cron: ApplicationComponentModel,
        dto: CronUpdate
    ) -> dict:
        """Update cron fields from DTO. Returns enabled change info."""
        enabled_changed = update_component_enabled_field(cron, dto.enabled, self.repository)

        if dto.settings is not None:
            cron.settings = dto.settings.model_dump()
            self.repository.update(cron)

        return enabled_changed


    def _deploy_to_kubernetes(
        self,
        cron: ApplicationComponentModel,
        environment_id: int,
        cluster: any,
        cluster_instance: ClusterInstanceModel
    ) -> None:
        """Deploy cron to Kubernetes."""
        deploy_to_kubernetes(
            cron, environment_id, cluster, cluster_instance,
            self.db, self.repository, upsert_to_kubernetes, 'cron'
        )

    def _delete_from_kubernetes_safe(
        self,
        cron: ApplicationComponentModel,
        cluster: any
    ) -> None:
        """Safely delete cron from Kubernetes (logs errors but doesn't fail)."""
        delete_from_kubernetes_safe(
            cron, cluster, self.db, self.repository, delete_from_kubernetes, 'cron'
        )

    def _serialize_cron(self, cron: ApplicationComponentModel) -> Cron:
        """Serialize cron to DTO."""
        return Cron.model_validate(cron)

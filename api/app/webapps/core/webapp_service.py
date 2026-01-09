"""Business logic for webapps. Broken into small, focused functions."""
from uuid import uuid4, UUID
from typing import List
from sqlalchemy.orm import Session

from app.webapps.infra.webapp_repository import WebappRepository
from app.webapps.infra.application_component_model import ApplicationComponent as ApplicationComponentModel, WebappType
from app.webapps.api.webapp_dto import WebappCreate, WebappUpdate, Webapp
from app.webapps.core.webapp_validators import (
    validate_webapp_create_dto,
    validate_webapp_update_dto,
    validate_webapp_exists,
    validate_webapp_type,
    validate_instance_exists,
    validate_exposure_type_for_cluster,
    validate_visibility_for_cluster,
    validate_url_for_exposure,
    WebappNotFoundError,
    WebappNotWebappTypeError,
    InstanceNotFoundError,
    InvalidExposureTypeError,
    InvalidVisibilityError,
    InvalidURLError
)
from app.webapps.core.webapp_kubernetes_service import (
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
    delete_component
)


class WebappService:
    """Business logic for webapps. No direct database access."""

    def __init__(self, repository: WebappRepository, database_session: Session):
        self.repository = repository
        self.db = database_session

    def create_webapp(self, dto: WebappCreate) -> Webapp:
        """Create a new webapp."""
        validate_webapp_create_dto(dto)
        validate_instance_exists(self.repository, dto.instance_uuid)

        instance = self.repository.find_instance_by_uuid(dto.instance_uuid)
        cluster = get_cluster_for_instance(self.db, instance)

        self._validate_exposure_settings(dto.settings.model_dump(), cluster)
        validate_url_for_exposure(
            dto.url,
            dto.settings.exposure.type,
            dto.settings.exposure.visibility.value
        )

        webapp = self._build_webapp_entity(dto, instance.id)
        webapp = self.repository.create(webapp)

        cluster_instance = ensure_cluster_instance(self.repository, webapp, cluster)
        self._deploy_to_kubernetes(webapp, instance.environment_id, cluster, cluster_instance)

        return self._serialize_webapp(webapp)

    def update_webapp(self, uuid: UUID, dto: WebappUpdate) -> Webapp:
        """Update an existing webapp."""
        validate_webapp_update_dto(dto)
        validate_webapp_exists(self.repository, uuid)

        webapp = self.repository.find_by_uuid(uuid)
        validate_webapp_type(webapp)

        # Check if there are any changes that require Kubernetes update
        has_changes = dto.settings is not None or dto.url is not None or dto.enabled is not None

        enabled_changed = self._update_webapp_fields(webapp, dto)
        cluster_instance = get_or_create_cluster_instance(self.repository, self.db, webapp)
        cluster = cluster_instance.cluster

        if enabled_changed['changed']:
            # Handle enabled status change
            handle_enabled_change(
                webapp, enabled_changed, cluster, cluster_instance,
                lambda c, cl: self._delete_from_kubernetes_safe(c, cl),
                lambda c, eid, cl, ci: self._deploy_to_kubernetes(c, eid, cl, ci)
            )
        elif webapp.enabled and has_changes:
            # If webapp is enabled and there are changes, always redeploy to apply new configs
            self._deploy_to_kubernetes(webapp, webapp.instance.environment_id, cluster, cluster_instance)

        return self._serialize_webapp(webapp)

    def get_webapp(self, uuid: UUID) -> Webapp:
        """Get webapp by UUID."""
        validate_webapp_exists(self.repository, uuid)
        webapp = self.repository.find_by_uuid(uuid)
        validate_webapp_type(webapp)
        return self._serialize_webapp(webapp)

    def get_webapps(self, skip: int = 0, limit: int = 100) -> List[Webapp]:
        """Get all webapps."""
        webapps = self.repository.find_all(skip=skip, limit=limit)
        return [self._serialize_webapp(w) for w in webapps]

    def delete_webapp(self, uuid: UUID) -> dict:
        """Delete a webapp."""
        validate_webapp_exists(self.repository, uuid)

        webapp = self.repository.find_by_uuid(uuid, load_relations=True)
        validate_webapp_type(webapp)

        return delete_component(
            webapp, self.repository, self.db,
            lambda c, cl: self._delete_from_kubernetes_safe(c, cl),
            'webapp'
        )


    def _validate_exposure_settings(self, settings_dict: dict, cluster: any) -> None:
        """Validate exposure settings for cluster."""
        if 'exposure' in settings_dict:
            if 'type' in settings_dict['exposure']:
                validate_exposure_type_for_cluster(cluster, settings_dict['exposure']['type'])
            if 'visibility' in settings_dict['exposure']:
                validate_visibility_for_cluster(cluster, settings_dict['exposure']['visibility'])

    def _build_webapp_entity(self, dto: WebappCreate, instance_id: int) -> ApplicationComponentModel:
        """Build webapp entity from DTO."""
        settings_dict = dto.settings.model_dump()
        exposure_type = settings_dict.get('exposure', {}).get('type', 'http')
        exposure_visibility = settings_dict.get('exposure', {}).get('visibility', 'cluster')

        url = dto.url if exposure_type == 'http' and exposure_visibility != 'cluster' else None

        return ApplicationComponentModel(
            uuid=uuid4(),
            instance_id=instance_id,
            name=dto.name,
            type=WebappType.webapp,
            settings=settings_dict,
            url=url,
            enabled=dto.enabled,
        )


    def _update_webapp_fields(self, webapp: ApplicationComponentModel, dto: WebappUpdate) -> dict:
        """Update webapp fields from DTO. Returns enabled change info."""
        enabled_changed = {
            'changed': False,
            'was_enabled': webapp.enabled,
            'will_be_enabled': webapp.enabled
        }

        if dto.settings is not None:
            settings_dict = dto.settings.model_dump()
            webapp.settings = settings_dict

            exposure_type = settings_dict.get('exposure', {}).get('type', 'http')
            exposure_visibility = settings_dict.get('exposure', {}).get('visibility', 'cluster')

            if exposure_type != 'http' or exposure_visibility == 'cluster':
                webapp.url = None
            elif dto.url is not None:
                webapp.url = dto.url

        if dto.enabled is not None:
            enabled_changed['changed'] = dto.enabled != webapp.enabled
            enabled_changed['will_be_enabled'] = dto.enabled
            webapp.enabled = dto.enabled

        final_settings = webapp.settings or {}
        exposure_type = final_settings.get('exposure', {}).get('type', 'http')
        exposure_visibility = final_settings.get('exposure', {}).get('visibility', 'cluster')

        if exposure_type == 'http' and exposure_visibility != 'cluster' and not webapp.url:
            raise InvalidURLError(
                "URL is required for webapp components with HTTP exposure type and visibility 'public' or 'private'"
            )

        self.repository.update(webapp)
        return enabled_changed


    def _deploy_to_kubernetes(
        self,
        webapp: ApplicationComponentModel,
        environment_id: int,
        cluster: any,
        cluster_instance: ClusterInstanceModel
    ) -> None:
        """Deploy webapp to Kubernetes."""
        deploy_to_kubernetes(
            webapp, environment_id, cluster, cluster_instance,
            self.db, self.repository, upsert_to_kubernetes, 'webapp'
        )

    def _delete_from_kubernetes_safe(self, webapp: ApplicationComponentModel, cluster: any) -> None:
        """Safely delete webapp from Kubernetes (logs errors but doesn't fail)."""
        delete_from_kubernetes_safe(
            webapp, cluster, self.db, self.repository, delete_from_kubernetes, 'webapp'
        )

    def _serialize_webapp(self, webapp: ApplicationComponentModel) -> Webapp:
        """Serialize webapp to DTO."""
        return Webapp.model_validate(webapp)

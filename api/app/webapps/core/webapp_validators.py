from uuid import UUID
from typing import Dict, Any
from app.webapps.infra.webapp_repository import WebappRepository
from app.webapps.api.webapp_dto import WebappCreate, WebappUpdate
from app.clusters.infra.cluster_model import Cluster as ClusterModel


class WebappNotFoundError(Exception):
    """Raised when webapp is not found."""
    pass


class WebappNotWebappTypeError(Exception):
    """Raised when component is not a webapp type."""
    pass


class InstanceNotFoundError(Exception):
    """Raised when instance is not found."""
    pass


class InvalidExposureTypeError(Exception):
    """Raised when exposure type is invalid for cluster."""
    pass


class InvalidVisibilityError(Exception):
    """Raised when visibility requires Gateway API but cluster doesn't have it."""
    pass


class InvalidURLError(Exception):
    """Raised when URL validation fails."""
    pass


def validate_webapp_create_dto(dto: WebappCreate) -> None:
    """Validate webapp create DTO. Raises ValueError if validation fails."""
    if not dto.name or not dto.name.strip():
        raise ValueError("Webapp name is required and cannot be empty")

    if ' ' in dto.name:
        raise ValueError("Component name cannot contain spaces")

    if not dto.instance_uuid:
        raise ValueError("Instance UUID is required")

    if not dto.settings:
        raise ValueError("Webapp settings are required")


def validate_webapp_update_dto(dto: WebappUpdate) -> None:
    """Validate webapp update DTO. Raises ValueError if validation fails."""
    # URL validation is done in DTO model_validator
    pass


def validate_webapp_exists(repository: WebappRepository, uuid: UUID) -> None:
    """Validate that webapp exists. Raises WebappNotFoundError if not found."""
    webapp = repository.find_by_uuid(uuid)
    if not webapp:
        raise WebappNotFoundError(f"Webapp with UUID '{uuid}' not found")


def validate_webapp_type(webapp) -> None:
    """Validate that component is a webapp type."""
    from app.webapps.infra.application_component_model import WebappType
    if webapp.type != WebappType.webapp:
        raise WebappNotWebappTypeError("Component is not a webapp")


def validate_instance_exists(repository: WebappRepository, uuid: UUID) -> None:
    """Validate that instance exists."""
    instance = repository.find_instance_by_uuid(uuid)
    if not instance:
        raise InstanceNotFoundError(f"Instance with UUID '{uuid}' not found")


def validate_exposure_type_for_cluster(cluster: ClusterModel, exposure_type: str) -> None:
    """Validate that exposure type is available in cluster Gateway API resources."""
    from app.k8s.client import K8sClient
    from fastapi import HTTPException

    type_to_resource = {
        'http': 'HTTPRoute',
        'tcp': 'TCPRoute',
        'udp': 'UDPRoute'
    }

    required_resource = type_to_resource.get(exposure_type)
    if not required_resource:
        return  # Not a Gateway API type

    k8s_client = K8sClient(url=cluster.api_address, token=cluster.token)
    gateway_api_available = k8s_client.check_api_available("gateway.networking.k8s.io")

    if not gateway_api_available:
        raise InvalidExposureTypeError(
            f"Gateway API is not available in cluster '{cluster.name}'. "
            f"Exposure type '{exposure_type}' requires Gateway API support."
        )

    gateway_resources = k8s_client.get_gateway_api_resources()
    if required_resource not in gateway_resources:
        raise InvalidExposureTypeError(
            f"Gateway API resource '{required_resource}' is not available in cluster '{cluster.name}'. "
            f"Required for exposure type '{exposure_type}'. "
            f"Available resources: {', '.join(gateway_resources) if gateway_resources else 'none'}"
        )


def validate_visibility_for_cluster(cluster: ClusterModel, visibility: str) -> None:
    """Validate that visibility is supported by cluster."""
    from app.k8s.client import K8sClient

    if visibility not in ['public', 'private']:
        return  # Cluster visibility doesn't need Gateway API

    k8s_client = K8sClient(url=cluster.api_address, token=cluster.token)
    gateway_api_available = k8s_client.check_api_available("gateway.networking.k8s.io")

    if not gateway_api_available:
        raise InvalidVisibilityError(
            f"Cluster '{cluster.name}' does not have Gateway API available. "
            f"Visibility 'public' or 'private' requires Gateway API support. "
            f"Please use 'cluster' visibility instead."
        )


def validate_url_for_exposure(
    url: str | None,
    exposure_type: str,
    exposure_visibility: str,
    is_update: bool = False
) -> None:
    """Validate URL based on exposure type and visibility."""
    # URL is required only if exposure.type is 'http' AND visibility is not 'cluster'
    if exposure_type == 'http' and exposure_visibility != 'cluster' and not url:
        if not is_update:
            raise InvalidURLError(
                "URL is required for webapp components with HTTP exposure type and visibility 'public' or 'private'"
            )

    # URL is not allowed if exposure.type is not 'http' or visibility is 'cluster'
    if (exposure_type != 'http' or exposure_visibility == 'cluster') and url:
        if exposure_type != 'http':
            raise InvalidURLError(
                f"URL is not allowed for webapp components with exposure type '{exposure_type}'. "
                f"URL is only allowed for HTTP exposure type."
            )
        else:
            raise InvalidURLError(
                "URL is not allowed for webapp components with 'cluster' visibility. "
                "URL is only allowed for 'public' or 'private' visibility."
            )

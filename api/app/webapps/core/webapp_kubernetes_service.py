"""Kubernetes operations for webapps. Isolated from business logic."""
from app.k8s.client import K8sClient
from app.shared.k8s.application_component_manager import KubernetesApplicationComponentManager
from app.clusters.core.cluster_service import get_gateway_reference_from_cluster
from app.shared.serializers.serializers import serialize_application_component, serialize_settings
from app.webapps.infra.application_component_model import ApplicationComponent as ApplicationComponentModel
from app.clusters.infra.cluster_model import Cluster as ClusterModel
from typing import Dict, Any


def ensure_namespace_exists(k8s_client: K8sClient, application_name: str) -> None:
    """Ensure namespace exists in cluster."""
    if application_name:
        k8s_client.ensure_namespace_exists(application_name)


def build_kubernetes_payload(
    component: ApplicationComponentModel,
    component_type: str,
    settings_serialized: Dict[str, Any],
    gateway_reference: Dict[str, str],
    database_session
) -> Dict[str, Any]:
    """Build Kubernetes payload for component."""
    application_component_serialized = serialize_application_component(component)
    return KubernetesApplicationComponentManager.instance_management(
        application_component_serialized,
        component_type,
        settings_serialized,
        db=database_session,
        gateway_reference=gateway_reference
    )


def apply_to_kubernetes(
    cluster: ClusterModel,
    component: ApplicationComponentModel,
    settings_serialized: Dict[str, Any],
    operation: str,
    database_session
) -> None:
    """Apply or delete component in Kubernetes."""
    k8s_client = K8sClient(url=cluster.api_address, token=cluster.token)

    application_component_serialized = serialize_application_component(component)
    component_type = component.type.value if hasattr(component.type, 'value') else str(component.type)
    application_name = application_component_serialized.get("application_name")

    ensure_namespace_exists(k8s_client, application_name)

    gateway_reference = get_gateway_reference_from_cluster(cluster)
    kubernetes_payload = build_kubernetes_payload(
        component,
        component_type,
        settings_serialized,
        gateway_reference,
        database_session
    )

    k8s_client.apply_or_delete_yaml_to_k8s(kubernetes_payload, operation=operation)


def delete_from_kubernetes(
    cluster: ClusterModel,
    component: ApplicationComponentModel,
    settings_serialized: Dict[str, Any],
    database_session
) -> None:
    """Delete component from Kubernetes."""
    apply_to_kubernetes(cluster, component, settings_serialized, "delete", database_session)


def upsert_to_kubernetes(
    cluster: ClusterModel,
    component: ApplicationComponentModel,
    settings_serialized: Dict[str, Any],
    database_session
) -> None:
    """Upsert component to Kubernetes."""
    apply_to_kubernetes(cluster, component, settings_serialized, "upsert", database_session)

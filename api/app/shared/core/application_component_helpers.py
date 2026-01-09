"""Shared helper functions for application components (webapps, workers, cron)."""
from uuid import uuid4
from typing import Any, Dict
from sqlalchemy.orm import Session

from app.shared.k8s.cluster_selection import ClusterSelectionService
from app.shared.infra.cluster_instance_model import ClusterInstance as ClusterInstanceModel
from app.webapps.infra.application_component_model import ApplicationComponent as ApplicationComponentModel
from app.shared.serializers.serializers import serialize_settings


def get_cluster_for_instance(db: Session, instance: Any) -> Any:
    """Get cluster with least load for instance."""
    return ClusterSelectionService.get_cluster_with_least_load_or_raise(
        db, instance.environment_id, instance.environment.name
    )


def ensure_cluster_instance(
    repository: Any,
    component: ApplicationComponentModel,
    cluster: Any
) -> ClusterInstanceModel:
    """
    Ensure cluster instance exists for component.

    Args:
        repository: Repository with find_cluster_instance_by_component_id and create_cluster_instance methods
        component: ApplicationComponent entity
        cluster: Cluster entity

    Returns:
        ClusterInstanceModel
    """
    existing = repository.find_cluster_instance_by_component_id(component.id)
    if existing:
        return existing

    cluster_instance = ClusterInstanceModel(
        uuid=uuid4(),
        cluster_id=cluster.id,
        application_component_id=component.id,
    )
    repository.create_cluster_instance(cluster_instance)
    return cluster_instance


def get_or_create_cluster_instance(
    repository: Any,
    db: Session,
    component: ApplicationComponentModel
) -> ClusterInstanceModel:
    """
    Get or create cluster instance for component.

    Args:
        repository: Repository with find_cluster_instance_by_component_id and create_cluster_instance methods
        db: Database session
        component: ApplicationComponent entity

    Returns:
        ClusterInstanceModel
    """
    cluster_instance = repository.find_cluster_instance_by_component_id(component.id)
    if cluster_instance:
        return cluster_instance

    instance = component.instance
    cluster = get_cluster_for_instance(db, instance)
    return ensure_cluster_instance(repository, component, cluster)


def handle_enabled_change(
    component: ApplicationComponentModel,
    enabled_changed: Dict[str, Any],
    cluster: Any,
    cluster_instance: ClusterInstanceModel,
    delete_from_k8s_func: Any,
    deploy_to_k8s_func: Any
) -> None:
    """
    Handle enabled status change for component.

    Args:
        component: ApplicationComponent entity
        enabled_changed: Dict with 'was_enabled', 'will_be_enabled', 'changed' keys
        cluster: Cluster entity
        cluster_instance: ClusterInstanceModel
        delete_from_k8s_func: Function to delete from Kubernetes (takes component, cluster)
        deploy_to_k8s_func: Function to deploy to Kubernetes (takes component, env_id, cluster, cluster_instance)
    """
    if enabled_changed['was_enabled'] and not enabled_changed['will_be_enabled']:
        delete_from_k8s_func(component, cluster)
    elif not enabled_changed['was_enabled'] and enabled_changed['will_be_enabled']:
        deploy_to_k8s_func(component, component.instance.environment_id, cluster, cluster_instance)


def deploy_to_kubernetes(
    component: ApplicationComponentModel,
    environment_id: int,
    cluster: Any,
    cluster_instance: ClusterInstanceModel,
    db: Session,
    repository: Any,
    upsert_to_k8s_func: Any,
    component_type: str
) -> None:
    """
    Deploy component to Kubernetes.

    Args:
        component: ApplicationComponent entity
        environment_id: Environment ID
        cluster: Cluster entity
        cluster_instance: ClusterInstanceModel
        db: Database session
        repository: Repository with find_settings_by_environment_id method
        upsert_to_k8s_func: Function to upsert to Kubernetes
        component_type: Type of component ('webapp', 'worker', 'cron')
    """
    settings = repository.find_settings_by_environment_id(environment_id)
    settings_serialized = serialize_settings(settings)

    try:
        upsert_to_k8s_func(cluster, component, settings_serialized, db)
        db.commit()
        db.refresh(component)
        db.refresh(cluster_instance)
    except Exception as e:
        db.rollback()
        raise Exception(f"Failed to deploy {component_type} to Kubernetes cluster '{cluster.name}': {str(e)}")


def delete_from_kubernetes_safe(
    component: ApplicationComponentModel,
    cluster: Any,
    db: Session,
    repository: Any,
    delete_from_k8s_func: Any,
    component_type: str
) -> None:
    """
    Safely delete component from Kubernetes (logs errors but doesn't fail).

    Args:
        component: ApplicationComponent entity
        cluster: Cluster entity
        db: Database session
        repository: Repository with find_settings_by_environment_id method
        delete_from_k8s_func: Function to delete from Kubernetes
        component_type: Type of component ('webapp', 'worker', 'cron')
    """
    try:
        settings = repository.find_settings_by_environment_id(component.instance.environment_id)
        settings_serialized = serialize_settings(settings)
        delete_from_k8s_func(cluster, component, settings_serialized, db)
        db.commit()
        db.refresh(component)
    except Exception as e:
        print(f"Error removing {component_type} '{component.name}' from Kubernetes: {e}")
        db.commit()
        db.refresh(component)


def ensure_private_exposure_settings(settings_dict: Dict[str, Any]) -> Dict[str, Any]:
    """
    Ensure settings have exposure with visibility private.
    Used by workers and crons.

    Args:
        settings_dict: Settings dictionary

    Returns:
        Updated settings dictionary
    """
    if 'exposure' not in settings_dict:
        settings_dict['exposure'] = {
            'type': 'http',
            'port': 80,
            'visibility': 'private'
        }
    elif 'visibility' not in settings_dict.get('exposure', {}):
        settings_dict['exposure']['visibility'] = 'private'
    return settings_dict


def delete_component(
    component: ApplicationComponentModel,
    repository: Any,
    db: Session,
    delete_from_k8s_safe_func: Any,
    component_type: str
) -> dict:
    """
    Delete a component (webapp, worker, or cron).
    Handles Kubernetes cleanup and database deletion.

    Args:
        component: ApplicationComponent entity
        repository: Repository with delete_cluster_instance and delete methods
        db: Database session
        delete_from_k8s_safe_func: Function to safely delete from Kubernetes
        component_type: Type of component ('webapp', 'worker', 'cron')

    Returns:
        Success message dict
    """
    cluster_instance = repository.find_cluster_instance_by_component_id(component.id)
    if cluster_instance:
        delete_from_k8s_safe_func(component, cluster_instance.cluster)
        repository.delete_cluster_instance(cluster_instance)

    repository.delete(component)
    return {"detail": f"{component_type.capitalize()} deleted successfully"}


def update_component_enabled_field(
    component: ApplicationComponentModel,
    enabled: bool,
    repository: Any
) -> Dict[str, Any]:
    """
    Update enabled field for component and return change info.
    Used by workers and crons (webapps have additional URL logic).

    Args:
        component: ApplicationComponent entity
        enabled: New enabled value
        repository: Repository with update method

    Returns:
        Dict with 'changed', 'was_enabled', 'will_be_enabled' keys
    """
    enabled_changed = {
        'changed': False,
        'was_enabled': component.enabled,
        'will_be_enabled': component.enabled
    }

    if enabled is not None:
        enabled_changed['changed'] = enabled != component.enabled
        enabled_changed['will_be_enabled'] = enabled
        component.enabled = enabled

    repository.update(component)
    return enabled_changed


def build_application_component_entity(
    name: str,
    instance_id: int,
    settings_dict: Dict[str, Any],
    component_type: Any,  # WebappType enum value
    url: str = None,
    enabled: bool = True
) -> ApplicationComponentModel:
    """
    Build ApplicationComponent entity.
    Used by workers and crons (webapps have custom logic for URL).

    Args:
        name: Component name
        instance_id: Instance ID
        settings_dict: Settings dictionary
        component_type: WebappType enum value (worker, cron)
        url: Optional URL (None for workers and crons)
        enabled: Enabled status

    Returns:
        ApplicationComponentModel
    """
    return ApplicationComponentModel(
        uuid=uuid4(),
        instance_id=instance_id,
        name=name,
        type=component_type,
        settings=settings_dict,
        url=url,
        enabled=enabled,
    )

"""Kubernetes pods operations for webapps. Isolated from business logic."""
from app.k8s.client import K8sClient
from app.webapps.infra.application_component_model import ApplicationComponent as ApplicationComponentModel
from app.clusters.infra.cluster_model import Cluster as ClusterModel
from typing import List, Dict, Any


def get_webapp_pods_from_cluster(
    cluster: ClusterModel,
    application_name: str,
    component_name: str
) -> List[Dict[str, Any]]:
    """Get pods for webapp from cluster."""
    k8s_client = K8sClient(url=cluster.api_address, token=cluster.token)
    label_selector = f"app={component_name}"
    pods = k8s_client.list_pods(namespace=application_name, label_selector=label_selector)

    if not pods:
        all_pods = k8s_client.list_pods(namespace=application_name)
        pods = [pod for pod in all_pods if component_name in pod['name']]

    return pods


def delete_webapp_pod_from_cluster(
    cluster: ClusterModel,
    application_name: str,
    pod_name: str
) -> None:
    """Delete pod from cluster."""
    k8s_client = K8sClient(url=cluster.api_address, token=cluster.token)
    k8s_client.delete_pod(namespace=application_name, pod_name=pod_name)


def get_webapp_pod_logs_from_cluster(
    cluster: ClusterModel,
    application_name: str,
    pod_name: str,
    container_name: str = None,
    tail_lines: int = 100
) -> str:
    """Get pod logs from cluster."""
    k8s_client = K8sClient(url=cluster.api_address, token=cluster.token)
    return k8s_client.get_pod_logs(
        namespace=application_name,
        pod_name=pod_name,
        container_name=container_name,
        tail_lines=tail_lines
    )


def exec_webapp_pod_command_from_cluster(
    cluster: ClusterModel,
    application_name: str,
    pod_name: str,
    command: List[str],
    container_name: str = None
) -> Dict[str, Any]:
    """Execute command in pod from cluster."""
    k8s_client = K8sClient(url=cluster.api_address, token=cluster.token)
    return k8s_client.exec_pod_command(
        namespace=application_name,
        pod_name=pod_name,
        command=command,
        container_name=container_name
    )

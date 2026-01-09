"""Kubernetes CronJob operations. Isolated from business logic."""
from app.k8s.client import K8sClient
from app.clusters.infra.cluster_model import Cluster as ClusterModel
from typing import List, Dict, Any


def get_cron_jobs_from_cluster(
    cluster: ClusterModel,
    application_name: str,
    component_name: str
) -> List[Dict[str, Any]]:
    """Get jobs for cron from cluster."""
    k8s_client = K8sClient(url=cluster.api_address, token=cluster.token)
    label_selector = f"app={component_name}"
    jobs = k8s_client.list_jobs(namespace=application_name, label_selector=label_selector)

    if not jobs:
        all_jobs = k8s_client.list_jobs(namespace=application_name)
        jobs = [job for job in all_jobs if component_name in job['name']]

    return jobs


def get_cron_job_logs_from_cluster(
    cluster: ClusterModel,
    application_name: str,
    job_name: str,
    container_name: str = None,
    tail_lines: int = 100
) -> Dict[str, Any]:
    """Get logs for a cron job from cluster."""
    k8s_client = K8sClient(url=cluster.api_address, token=cluster.token)

    # Find pods for the job
    label_selector = f"job-name={job_name}"
    pods = k8s_client.list_pods(namespace=application_name, label_selector=label_selector)

    if not pods:
        raise Exception(f"No pods found for job {job_name}")

    pod_name = pods[0]['name']
    logs = k8s_client.get_pod_logs(
        namespace=application_name,
        pod_name=pod_name,
        container_name=container_name,
        tail_lines=tail_lines
    )

    return {
        "logs": logs,
        "pod_name": pod_name,
        "job_name": job_name,
        "container_name": container_name
    }


def delete_cron_job_from_cluster(
    cluster: ClusterModel,
    application_name: str,
    job_name: str
) -> None:
    """Delete a cron job from cluster."""
    k8s_client = K8sClient(url=cluster.api_address, token=cluster.token)
    k8s_client.delete_job(namespace=application_name, job_name=job_name)

import pytest
from unittest.mock import patch, MagicMock
from app.shared.k8s.application_component_manager import (
    KubernetesApplicationComponentManager,
)


def test_instance_management():

    # Updated to match new serialize_application_component format
    application_component_serialized = {
        "component_name": "teste",
        "component_uuid": "4329360f-19fe-4674-813f-4ab7146ac0b3",
        "component_type": "webapp",
        "application_name": "teste-app",
        "application_uuid": "a8ef62c3-2860-461e-ad74-dc1472691f2d",
        "environment": "staging",
        "environment_uuid": "b9ef62c3-2860-461e-ad74-dc1472691f2e",
        "image": "nginx",
        "version": "1.0.0",
        "url": None,
        "enabled": True,
        "settings": {
            "cpu": 0.25,
            "memory": 128,
            "cpu_scaling_threshold": 80,
            "memory_scaling_threshold": 80,
            "envs": [{"key": "value"}],
            "secrets": [],
            "custom_metrics": {"enabled": False, "path": "/metrics", "port": 0},
            "healthcheck": {
                "path": "/healthcheck",
                "protocol": "http",
                "port": 80,
                "timeout": 5,
                "interval": 31,
                "initial_interval": 30,
                "failure_threshold": 2,
            },
            "exposure": {
                "type": "http",
                "port": 80,
                "visibility": "cluster"
            }
        }
    }

    # Mock database session
    mock_db = MagicMock()

    # Mock templates - need multiple templates to get 3 resources
    mock_template_deployment = MagicMock()
    mock_template_deployment.content = "kind: Deployment\napiVersion: apps/v1\nmetadata:\n  name: test"
    mock_template_deployment.name = "deployment-template"

    mock_template_hpa = MagicMock()
    mock_template_hpa.content = "kind: HorizontalPodAutoscaler\napiVersion: autoscaling/v2\nmetadata:\n  name: test"
    mock_template_hpa.name = "hpa-template"

    mock_template_service = MagicMock()
    mock_template_service.content = "kind: Service\napiVersion: v1\nmetadata:\n  name: test"
    mock_template_service.name = "service-template"

    # Mock the repositories and service
    with patch('app.shared.k8s.application_component_manager.ComponentTemplateConfigRepository') as mock_config_repo_class, \
         patch('app.shared.k8s.application_component_manager.TemplateRepository') as mock_template_repo_class, \
         patch('app.shared.k8s.application_component_manager.ComponentTemplateConfigService') as mock_service_class:

        mock_config_repo = MagicMock()
        mock_template_repo = MagicMock()
        mock_config_repo_class.return_value = mock_config_repo
        mock_template_repo_class.return_value = mock_template_repo

        mock_service = MagicMock()
        # Return 3 templates to get 3 resources
        mock_service.get_templates_for_component_type.return_value = [
            mock_template_deployment,
            mock_template_hpa,
            mock_template_service
        ]
        mock_service_class.return_value = mock_service

        kubernetes_payload = KubernetesApplicationComponentManager.instance_management(
            application_component_serialized, "webapp", db=mock_db
        )

    kinds = []
    api_versions = []

    for item in kubernetes_payload:
        kinds.append(item.get("kind"))
        api_versions.append(item.get("apiVersion"))

    assert len(kubernetes_payload) == 3
    assert "Deployment" in kinds
    assert "HorizontalPodAutoscaler" in kinds
    assert "Service" in kinds
    assert "apps/v1" in api_versions
    assert "autoscaling/v2" in api_versions
    assert "v1" in api_versions

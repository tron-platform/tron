
import pytest
from unittest.mock import MagicMock
from app.shared.serializers.serializers import serialize_webapp_deploy

def test_serialize_webapp_deploy():

    # Mock ApplicationComponent with new structure
    mock_webapp_deploy = MagicMock()

    # Component attributes
    mock_webapp_deploy.name = "test-webapp"
    mock_webapp_deploy.uuid = "123e4567-e89b-12d3-a456-426614174000"
    mock_webapp_deploy.url = None
    mock_webapp_deploy.enabled = True

    # Type enum
    from app.webapps.infra.application_component_model import WebappType
    mock_webapp_deploy.type = WebappType.webapp

    # Instance attributes
    mock_instance = MagicMock()
    mock_instance.image = "nginx"
    mock_instance.version = "1.0.0"

    # Application attributes
    mock_application = MagicMock()
    mock_application.name = "test-app"
    mock_application.uuid = "223e4567-e89b-12d3-a456-426614174001"
    mock_instance.application = mock_application

    # Environment attributes
    mock_environment = MagicMock()
    mock_environment.name = "staging"
    mock_environment.uuid = "323e4567-e89b-12d3-a456-426614174002"
    mock_instance.environment = mock_environment

    mock_webapp_deploy.instance = mock_instance

    # Settings
    mock_webapp_deploy.settings = {
        "cpu": 0.25,
        "memory": 128,
        "cpu_scaling_threshold": 80,
        "memory_scaling_threshold": 70,
        "envs": [{"key": "chave", "value": "valor"}],
        "secrets": [],
        "custom_metrics": {"enabled": False, "path": "/metrics", "port": 8080},
        "healthcheck": {
            "path": "/healthcheck",
            "protocol": "http",
            "port": 80,
            "timeout": 5,
            "interval": 31,
            "initial_interval": 30,
            "failure_threshold": 2
        },
        "exposure": {
            "type": "http",
            "port": 80,
            "visibility": "cluster"
        }
    }

    result = serialize_webapp_deploy(mock_webapp_deploy)

    # Verify new format
    assert result["component_name"] == "test-webapp"
    assert result["component_uuid"] == "123e4567-e89b-12d3-a456-426614174000"
    assert result["component_type"] == "webapp"
    assert result["application_name"] == "test-app"
    assert result["application_uuid"] == "223e4567-e89b-12d3-a456-426614174001"
    assert result["environment"] == "staging"
    assert result["environment_uuid"] == "323e4567-e89b-12d3-a456-426614174002"
    assert result["image"] == "nginx"
    assert result["version"] == "1.0.0"
    assert result["url"] is None
    assert result["enabled"] is True
    assert "settings" in result
    assert result["settings"]["cpu"] == 0.25
    assert result["settings"]["memory"] == 128

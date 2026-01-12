"""Integration tests for webapps endpoints."""
import pytest
from fastapi import status
from uuid import uuid4
from unittest.mock import patch


@pytest.fixture
def test_instance(client, admin_token):
    """Create a test instance for webapp tests."""
    from unittest.mock import patch, MagicMock

    # Create application
    app_response = client.post(
        "/applications/",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "name": "test-app-for-webapp",
            "repository": "https://github.com/example/test-app"
        }
    )
    assert app_response.status_code == status.HTTP_200_OK
    app_uuid = app_response.json()["uuid"]

    # Create environment
    env_response = client.post(
        "/environments/",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"name": "test-env-for-webapp"}
    )
    assert env_response.status_code == status.HTTP_200_OK
    env_uuid = env_response.json()["uuid"]

    # Create cluster (required for components)
    with patch('app.clusters.core.cluster_service.K8sClient') as mock_k8s_client:
        mock_client_instance = MagicMock()
        mock_client_instance.validate_connection.return_value = (True, {"message": "Connection successful"})
        mock_k8s_client.return_value = mock_client_instance

        cluster_response = client.post(
            "/clusters/",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "name": "test-cluster-for-webapp",
                "api_address": "https://k8s.example.com",
                "token": "test-token-123",
                "environment_uuid": env_uuid
            }
        )
        assert cluster_response.status_code == status.HTTP_200_OK

    # Create instance
    instance_response = client.post(
        "/instances/",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "application_uuid": app_uuid,
            "environment_uuid": env_uuid,
            "image": "nginx:latest",
            "version": "1.0.0"
        }
    )
    assert instance_response.status_code == status.HTTP_200_OK
    return instance_response.json()


@patch('app.webapps.core.webapp_service.validate_exposure_type_for_cluster')
@patch('app.webapps.core.webapp_service.validate_visibility_for_cluster')
@patch('app.clusters.core.cluster_service.get_gateway_reference_from_cluster')
@patch('app.webapps.core.webapp_kubernetes_service.apply_to_kubernetes')
@patch('app.shared.k8s.cluster_selection.ClusterSelectionService.get_cluster_with_least_load_or_raise')
def test_create_webapp_success(mock_get_cluster, mock_apply, mock_gateway, mock_validate_visibility, mock_validate_exposure, client, admin_token, test_instance):
    """Test successful webapp creation."""
    from unittest.mock import MagicMock

    # Mock cluster
    mock_cluster = MagicMock(spec=['id', 'name', 'api_address', 'token', 'environment_id'])
    mock_cluster.id = 1
    mock_cluster.name = "test-cluster"
    mock_cluster.api_address = "https://k8s.example.com"
    mock_cluster.token = "test-token"
    mock_cluster.environment_id = 1
    mock_get_cluster.return_value = mock_cluster
    mock_apply.return_value = None
    mock_gateway.return_value = {"namespace": "", "name": ""}
    mock_validate_exposure.return_value = None
    mock_validate_visibility.return_value = None

    response = client.post(
        "/application_components/webapp/",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "instance_uuid": test_instance["uuid"],
            "name": "test-webapp",
            "enabled": True,
            "settings": {
                "exposure": {
                    "type": "http",
                    "port": 80,
                    "visibility": "cluster"
                },
                "cpu": 0.5,
                "memory": 512,
                "healthcheck": {
                    "path": "/health",
                    "protocol": "http",
                    "port": 80
                },
                "custom_metrics": {
                    "enabled": False,
                    "path": "/metrics",
                    "port": 8080
                },
                "autoscaling": {
                    "min": 1,
                    "max": 3
                }
            }
        }
    )

    if response.status_code != status.HTTP_200_OK:
        print(f"\n[test_create_webapp_success] Error {response.status_code}: {response.json()}")

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["name"] == "test-webapp"
    assert data["enabled"] is True
    assert "uuid" in data


def test_create_webapp_requires_authentication(client, test_instance):
    """Test that webapp creation requires authentication."""
    response = client.post(
        "/application_components/webapp/",
        json={
            "instance_uuid": test_instance["uuid"],
            "name": "test-webapp",
            "settings": {
                "exposure": {
                    "type": "http",
                    "port": 80,
                    "visibility": "cluster"
                },
                "cpu": 0.5,
                "memory": 512,
                "healthcheck": {
                    "path": "/health",
                    "protocol": "http",
                    "port": 80
                },
                "custom_metrics": {
                    "enabled": False,
                    "path": "/metrics",
                    "port": 8080
                },
                "autoscaling": {
                    "min": 1,
                    "max": 3
                }
            }
        }
    )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_create_webapp_requires_admin_role(client, user_token, test_instance):
    """Test that webapp creation requires admin role."""
    response = client.post(
        "/application_components/webapp/",
        headers={"Authorization": f"Bearer {user_token}"},
        json={
            "instance_uuid": test_instance["uuid"],
            "name": "test-webapp",
            "settings": {
                "exposure": {
                    "type": "http",
                    "port": 80,
                    "visibility": "cluster"
                },
                "cpu": 0.5,
                "memory": 512,
                "healthcheck": {
                    "path": "/health",
                    "protocol": "http",
                    "port": 80
                },
                "custom_metrics": {
                    "enabled": False,
                    "path": "/metrics",
                    "port": 8080
                },
                "autoscaling": {
                    "min": 1,
                    "max": 3
                }
            }
        }
    )

    assert response.status_code == status.HTTP_403_FORBIDDEN


@patch('app.webapps.core.webapp_service.validate_exposure_type_for_cluster')
@patch('app.webapps.core.webapp_service.validate_visibility_for_cluster')
@patch('app.clusters.core.cluster_service.get_gateway_reference_from_cluster')
@patch('app.webapps.core.webapp_kubernetes_service.apply_to_kubernetes')
@patch('app.shared.k8s.cluster_selection.ClusterSelectionService.get_cluster_with_least_load_or_raise')
def test_list_webapps_success(mock_get_cluster, mock_apply, mock_gateway, mock_validate_visibility, mock_validate_exposure, client, admin_token, test_instance):
    """Test successful webapp listing."""
    from unittest.mock import MagicMock

    # Mock cluster
    mock_cluster = MagicMock(spec=['id', 'name', 'api_address', 'token', 'environment_id'])
    mock_cluster.id = 1
    mock_cluster.name = "test-cluster"
    mock_cluster.api_address = "https://k8s.example.com"
    mock_cluster.token = "test-token"
    mock_cluster.environment_id = 1
    mock_get_cluster.return_value = mock_cluster
    mock_apply.return_value = None
    mock_gateway.return_value = {"namespace": "", "name": ""}
    mock_validate_exposure.return_value = None
    mock_validate_visibility.return_value = None

    # Create a webapp first
    create_response = client.post(
        "/application_components/webapp/",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "instance_uuid": test_instance["uuid"],
            "name": "list-test-webapp",
            "settings": {
                "exposure": {
                    "type": "http",
                    "port": 80,
                    "visibility": "cluster"
                },
                "cpu": 0.5,
                "memory": 512,
                "healthcheck": {
                    "path": "/health",
                    "protocol": "http",
                    "port": 80
                },
                "custom_metrics": {
                    "enabled": False,
                    "path": "/metrics",
                    "port": 8080
                },
                "autoscaling": {
                    "min": 1,
                    "max": 3
                }
            }
        }
    )
    if create_response.status_code != status.HTTP_200_OK:
        print(f"\n[test_list_webapps_success - create] Error {create_response.status_code}: {create_response.json()}")
    assert create_response.status_code == status.HTTP_200_OK

    # List webapps
    response = client.get(
        "/application_components/webapp/",
        headers={"Authorization": f"Bearer {admin_token}"}
    )

    if response.status_code != status.HTTP_200_OK:
        print(f"\n[test_list_webapps_success - list] Error {response.status_code}: {response.json()}")

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1


def test_list_webapps_requires_authentication(client):
    """Test that listing webapps requires authentication."""
    response = client.get("/application_components/webapp/")

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


@patch('app.webapps.core.webapp_service.validate_exposure_type_for_cluster')
@patch('app.webapps.core.webapp_service.validate_visibility_for_cluster')
@patch('app.clusters.core.cluster_service.get_gateway_reference_from_cluster')
@patch('app.webapps.core.webapp_kubernetes_service.apply_to_kubernetes')
@patch('app.shared.k8s.cluster_selection.ClusterSelectionService.get_cluster_with_least_load_or_raise')
def test_get_webapp_success(mock_get_cluster, mock_apply, mock_gateway, mock_validate_visibility, mock_validate_exposure, client, admin_token, test_instance):
    """Test successful retrieval of webapp by UUID."""
    from unittest.mock import MagicMock

    # Mock cluster
    mock_cluster = MagicMock(spec=['id', 'name', 'api_address', 'token', 'environment_id'])
    mock_cluster.id = 1
    mock_cluster.name = "test-cluster"
    mock_cluster.api_address = "https://k8s.example.com"
    mock_cluster.token = "test-token"
    mock_cluster.environment_id = 1
    mock_get_cluster.return_value = mock_cluster
    mock_apply.return_value = None
    mock_gateway.return_value = {"namespace": "", "name": ""}
    mock_validate_exposure.return_value = None
    mock_validate_visibility.return_value = None

    # Create a webapp
    create_response = client.post(
        "/application_components/webapp/",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "instance_uuid": test_instance["uuid"],
            "name": "get-test-webapp",
            "settings": {
                "exposure": {
                    "type": "http",
                    "port": 80,
                    "visibility": "cluster"
                },
                "cpu": 0.5,
                "memory": 512,
                "healthcheck": {
                    "path": "/health",
                    "protocol": "http",
                    "port": 80
                },
                "custom_metrics": {
                    "enabled": False,
                    "path": "/metrics",
                    "port": 8080
                },
                "autoscaling": {
                    "min": 1,
                    "max": 3
                }
            }
        }
    )
    if create_response.status_code != status.HTTP_200_OK:
        print(f"\n[test_get_webapp_success - create] Error {create_response.status_code}: {create_response.json()}")
    assert create_response.status_code == status.HTTP_200_OK
    webapp_uuid = create_response.json()["uuid"]

    # Get webapp
    response = client.get(
        f"/application_components/webapp/{webapp_uuid}",
        headers={"Authorization": f"Bearer {admin_token}"}
    )

    if response.status_code != status.HTTP_200_OK:
        print(f"\n[test_get_webapp_success - get] Error {response.status_code}: {response.json()}")

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["name"] == "get-test-webapp"
    assert data["uuid"] == webapp_uuid


def test_get_webapp_not_found(client, admin_token):
    """Test that getting non-existent webapp returns 404."""
    fake_uuid = uuid4()
    response = client.get(
        f"/application_components/webapp/{fake_uuid}",
        headers={"Authorization": f"Bearer {admin_token}"}
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_get_webapp_requires_authentication(client):
    """Test that getting webapp requires authentication."""
    fake_uuid = uuid4()
    response = client.get(f"/application_components/webapp/{fake_uuid}")

    assert response.status_code == status.HTTP_401_UNAUTHORIZED

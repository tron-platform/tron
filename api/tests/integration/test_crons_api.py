"""Integration tests for crons endpoints."""
import pytest
from fastapi import status
from uuid import uuid4
from unittest.mock import patch


@pytest.fixture
def test_instance(client, admin_token):
    """Create a test instance for cron tests."""
    from unittest.mock import patch, MagicMock

    # Create application
    app_response = client.post(
        "/applications/",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "name": "test-app-for-cron",
            "repository": "https://github.com/example/test-app"
        }
    )
    assert app_response.status_code == status.HTTP_200_OK
    app_uuid = app_response.json()["uuid"]

    # Create environment
    env_response = client.post(
        "/environments/",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"name": "test-env-for-cron"}
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
                "name": "test-cluster-for-cron",
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


@patch('app.clusters.core.cluster_service.get_gateway_reference_from_cluster')
@patch('app.webapps.core.webapp_kubernetes_service.apply_to_kubernetes')
@patch('app.shared.k8s.cluster_selection.ClusterSelectionService.get_cluster_with_least_load_or_raise')
def test_create_cron_success(mock_get_cluster, mock_apply, mock_gateway, client, admin_token, test_instance):
    """Test successful cron creation."""
    from unittest.mock import MagicMock

    # Mock cluster - need to use spec to ensure name is a string, not MagicMock
    mock_cluster = MagicMock(spec=['id', 'name', 'api_address', 'token', 'environment_id'])
    mock_cluster.id = 1
    mock_cluster.name = "test-cluster"  # This will be a string, not MagicMock
    mock_cluster.api_address = "https://k8s.example.com"
    mock_cluster.token = "test-token"
    mock_cluster.environment_id = 1
    mock_get_cluster.return_value = mock_cluster
    mock_apply.return_value = None
    mock_gateway.return_value = {"namespace": "", "name": ""}

    response = client.post(
        "/application_components/cron/",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "instance_uuid": test_instance["uuid"],
            "name": "test-cron",
            "enabled": True,
            "settings": {
                "cpu": 0.5,
                "memory": 512,
                "schedule": "0 0 * * *"
            }
        }
    )

    if response.status_code != status.HTTP_200_OK:
        print(f"\n[test_create_cron_success] Error {response.status_code}: {response.json()}")

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["name"] == "test-cron"
    assert data["enabled"] is True
    assert "uuid" in data


def test_create_cron_requires_authentication(client, test_instance):
    """Test that cron creation requires authentication."""
    response = client.post(
        "/application_components/cron/",
        json={
            "instance_uuid": test_instance["uuid"],
            "name": "test-cron",
            "settings": {
                "cpu": 0.5,
                "memory": 512,
                "schedule": "0 0 * * *"
            }
        }
    )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_create_cron_requires_admin_role(client, user_token, test_instance):
    """Test that cron creation requires admin role."""
    response = client.post(
        "/application_components/cron/",
        headers={"Authorization": f"Bearer {user_token}"},
        json={
            "instance_uuid": test_instance["uuid"],
            "name": "test-cron",
            "settings": {
                "cpu": 0.5,
                "memory": 512,
                "schedule": "0 0 * * *"
            }
        }
    )

    assert response.status_code == status.HTTP_403_FORBIDDEN


@patch('app.clusters.core.cluster_service.get_gateway_reference_from_cluster')
@patch('app.webapps.core.webapp_kubernetes_service.apply_to_kubernetes')
@patch('app.shared.k8s.cluster_selection.ClusterSelectionService.get_cluster_with_least_load_or_raise')
def test_list_crons_success(mock_get_cluster, mock_apply, mock_gateway, client, admin_token, test_instance):
    """Test successful cron listing."""
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

    # Create a cron first
    create_response = client.post(
        "/application_components/cron/",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "instance_uuid": test_instance["uuid"],
            "name": "list-test-cron",
            "settings": {
                "cpu": 0.5,
                "memory": 512,
                "schedule": "0 0 * * *"
            }
        }
    )
    if create_response.status_code != status.HTTP_200_OK:
        print(f"\n[test_list_crons_success - create] Error {create_response.status_code}: {create_response.json()}")
    assert create_response.status_code == status.HTTP_200_OK

    # List crons
    response = client.get(
        "/application_components/cron/",
        headers={"Authorization": f"Bearer {admin_token}"}
    )

    if response.status_code != status.HTTP_200_OK:
        print(f"\n[test_list_crons_success - list] Error {response.status_code}: {response.json()}")

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1


def test_list_crons_requires_authentication(client):
    """Test that listing crons requires authentication."""
    response = client.get("/application_components/cron/")

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


@patch('app.clusters.core.cluster_service.get_gateway_reference_from_cluster')
@patch('app.webapps.core.webapp_kubernetes_service.apply_to_kubernetes')
@patch('app.shared.k8s.cluster_selection.ClusterSelectionService.get_cluster_with_least_load_or_raise')
def test_get_cron_success(mock_get_cluster, mock_apply, mock_gateway, client, admin_token, test_instance):
    """Test successful retrieval of cron by UUID."""
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

    # Create a cron
    create_response = client.post(
        "/application_components/cron/",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "instance_uuid": test_instance["uuid"],
            "name": "get-test-cron",
            "settings": {
                "cpu": 0.5,
                "memory": 512,
                "schedule": "0 0 * * *"
            }
        }
    )
    if create_response.status_code != status.HTTP_200_OK:
        print(f"\n[test_get_cron_success - create] Error {create_response.status_code}: {create_response.json()}")
    assert create_response.status_code == status.HTTP_200_OK
    cron_uuid = create_response.json()["uuid"]

    # Get cron
    response = client.get(
        f"/application_components/cron/{cron_uuid}",
        headers={"Authorization": f"Bearer {admin_token}"}
    )

    if response.status_code != status.HTTP_200_OK:
        print(f"\n[test_get_cron_success - get] Error {response.status_code}: {response.json()}")

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["name"] == "get-test-cron"
    assert data["uuid"] == cron_uuid


def test_get_cron_not_found(client, admin_token):
    """Test that getting non-existent cron returns 404."""
    fake_uuid = uuid4()
    response = client.get(
        f"/application_components/cron/{fake_uuid}",
        headers={"Authorization": f"Bearer {admin_token}"}
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_get_cron_requires_authentication(client):
    """Test that getting cron requires authentication."""
    fake_uuid = uuid4()
    response = client.get(f"/application_components/cron/{fake_uuid}")

    assert response.status_code == status.HTTP_401_UNAUTHORIZED

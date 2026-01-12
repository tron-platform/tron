"""Integration tests for instances endpoints."""
import pytest
from fastapi import status
from uuid import uuid4


@pytest.fixture
def test_application(client, admin_token):
    """Create a test application."""
    response = client.post(
        "/applications/",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "name": "test-app-for-instance",
            "repository": "https://github.com/example/test-app"
        }
    )
    assert response.status_code == status.HTTP_200_OK
    return response.json()


@pytest.fixture
def test_environment(client, admin_token):
    """Create a test environment."""
    response = client.post(
        "/environments/",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"name": "test-env-for-instance"}
    )
    assert response.status_code == status.HTTP_200_OK
    return response.json()


def test_create_instance_success(client, admin_token, test_application, test_environment):
    """Test successful instance creation."""
    response = client.post(
        "/instances/",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "application_uuid": test_application["uuid"],
            "environment_uuid": test_environment["uuid"],
            "image": "nginx:latest",
            "version": "1.0.0",
            "enabled": True
        }
    )

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["image"] == "nginx:latest"
    assert data["version"] == "1.0.0"
    assert data["enabled"] is True
    assert "uuid" in data
    assert data["application"]["uuid"] == test_application["uuid"]
    assert data["environment"]["uuid"] == test_environment["uuid"]


def test_create_instance_requires_authentication(client, test_application, test_environment):
    """Test that instance creation requires authentication."""
    response = client.post(
        "/instances/",
        json={
            "application_uuid": test_application["uuid"],
            "environment_uuid": test_environment["uuid"],
            "image": "nginx:latest",
            "version": "1.0.0"
        }
    )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_create_instance_requires_admin_role(client, user_token, test_application, test_environment):
    """Test that instance creation requires admin role."""
    response = client.post(
        "/instances/",
        headers={"Authorization": f"Bearer {user_token}"},
        json={
            "application_uuid": test_application["uuid"],
            "environment_uuid": test_environment["uuid"],
            "image": "nginx:latest",
            "version": "1.0.0"
        }
    )

    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_create_instance_invalid_application(client, admin_token, test_environment):
    """Test that creating instance with invalid application UUID fails."""
    fake_uuid = uuid4()
    response = client.post(
        "/instances/",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "application_uuid": str(fake_uuid),
            "environment_uuid": test_environment["uuid"],
            "image": "nginx:latest",
            "version": "1.0.0"
        }
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_create_instance_invalid_environment(client, admin_token, test_application):
    """Test that creating instance with invalid environment UUID fails."""
    fake_uuid = uuid4()
    response = client.post(
        "/instances/",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "application_uuid": test_application["uuid"],
            "environment_uuid": str(fake_uuid),
            "image": "nginx:latest",
            "version": "1.0.0"
        }
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_list_instances_success(client, admin_token, test_application, test_environment):
    """Test successful instance listing."""
    # Create an instance first
    create_response = client.post(
        "/instances/",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "application_uuid": test_application["uuid"],
            "environment_uuid": test_environment["uuid"],
            "image": "nginx:latest",
            "version": "1.0.0"
        }
    )
    assert create_response.status_code == status.HTTP_200_OK

    # List instances
    response = client.get(
        "/instances/",
        headers={"Authorization": f"Bearer {admin_token}"}
    )

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1


def test_list_instances_requires_authentication(client):
    """Test that listing instances requires authentication."""
    response = client.get("/instances/")

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_get_instance_success(client, admin_token, test_application, test_environment):
    """Test successful retrieval of instance by UUID."""
    # Create an instance
    create_response = client.post(
        "/instances/",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "application_uuid": test_application["uuid"],
            "environment_uuid": test_environment["uuid"],
            "image": "nginx:latest",
            "version": "1.0.0"
        }
    )
    assert create_response.status_code == status.HTTP_200_OK
    instance_uuid = create_response.json()["uuid"]

    # Get instance
    response = client.get(
        f"/instances/{instance_uuid}",
        headers={"Authorization": f"Bearer {admin_token}"}
    )

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["uuid"] == instance_uuid
    assert data["image"] == "nginx:latest"
    assert data["version"] == "1.0.0"


def test_get_instance_not_found(client, admin_token):
    """Test that getting non-existent instance returns 404."""
    fake_uuid = uuid4()
    response = client.get(
        f"/instances/{fake_uuid}",
        headers={"Authorization": f"Bearer {admin_token}"}
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_get_instance_requires_authentication(client):
    """Test that getting instance requires authentication."""
    fake_uuid = uuid4()
    response = client.get(f"/instances/{fake_uuid}")

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_update_instance_success(client, admin_token, test_application, test_environment):
    """Test successful instance update."""
    # Create an instance
    create_response = client.post(
        "/instances/",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "application_uuid": test_application["uuid"],
            "environment_uuid": test_environment["uuid"],
            "image": "nginx:latest",
            "version": "1.0.0"
        }
    )
    assert create_response.status_code == status.HTTP_200_OK
    instance_uuid = create_response.json()["uuid"]

    # Update instance
    response = client.put(
        f"/instances/{instance_uuid}",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "image": "nginx:1.21",
            "version": "1.1.0",
            "enabled": False
        }
    )

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["image"] == "nginx:1.21"
    assert data["version"] == "1.1.0"
    assert data["enabled"] is False


def test_update_instance_not_found(client, admin_token):
    """Test that updating non-existent instance returns 404."""
    fake_uuid = uuid4()
    response = client.put(
        f"/instances/{fake_uuid}",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"image": "nginx:latest"}
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_update_instance_requires_admin_role(client, user_token):
    """Test that updating instance requires admin role."""
    fake_uuid = uuid4()
    response = client.put(
        f"/instances/{fake_uuid}",
        headers={"Authorization": f"Bearer {user_token}"},
        json={"image": "nginx:latest"}
    )

    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_delete_instance_success(client, admin_token, test_application, test_environment):
    """Test successful instance deletion."""
    # Create an instance
    create_response = client.post(
        "/instances/",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "application_uuid": test_application["uuid"],
            "environment_uuid": test_environment["uuid"],
            "image": "nginx:latest",
            "version": "1.0.0"
        }
    )
    assert create_response.status_code == status.HTTP_200_OK
    instance_uuid = create_response.json()["uuid"]

    # Delete instance
    response = client.delete(
        f"/instances/{instance_uuid}",
        headers={"Authorization": f"Bearer {admin_token}"}
    )

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "detail" in data

    # Verify it's deleted
    get_response = client.get(
        f"/instances/{instance_uuid}",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert get_response.status_code == status.HTTP_404_NOT_FOUND


def test_delete_instance_not_found(client, admin_token):
    """Test that deleting non-existent instance returns 404."""
    fake_uuid = uuid4()
    response = client.delete(
        f"/instances/{fake_uuid}",
        headers={"Authorization": f"Bearer {admin_token}"}
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_delete_instance_requires_admin_role(client, user_token):
    """Test that deleting instance requires admin role."""
    fake_uuid = uuid4()
    response = client.delete(
        f"/instances/{fake_uuid}",
        headers={"Authorization": f"Bearer {user_token}"}
    )

    assert response.status_code == status.HTTP_403_FORBIDDEN

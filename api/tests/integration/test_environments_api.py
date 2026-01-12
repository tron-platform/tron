"""Integration tests for environments endpoints."""
import pytest
from fastapi import status
from uuid import uuid4


def test_create_environment_success(client, admin_token):
    """Test successful environment creation."""
    response = client.post(
        "/environments/",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"name": "test-environment"}
    )

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["name"] == "test-environment"
    assert "uuid" in data


def test_create_environment_requires_authentication(client):
    """Test that environment creation requires authentication."""
    response = client.post(
        "/environments/",
        json={"name": "test-environment"}
    )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_create_environment_requires_admin_role(client, user_token):
    """Test that environment creation requires admin role."""
    response = client.post(
        "/environments/",
        headers={"Authorization": f"Bearer {user_token}"},
        json={"name": "test-environment"}
    )

    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_create_environment_duplicate_name(client, admin_token):
    """Test that creating environment with duplicate name fails."""
    # Create first environment
    response1 = client.post(
        "/environments/",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"name": "duplicate-env"}
    )
    assert response1.status_code == status.HTTP_200_OK

    # Try to create duplicate
    response2 = client.post(
        "/environments/",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"name": "duplicate-env"}
    )
    assert response2.status_code == status.HTTP_400_BAD_REQUEST


def test_list_environments_success(client, admin_token):
    """Test successful listing of environments."""
    # Create an environment first
    create_response = client.post(
        "/environments/",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"name": "list-test-env"}
    )
    assert create_response.status_code == status.HTTP_200_OK

    # List environments
    response = client.get(
        "/environments/",
        headers={"Authorization": f"Bearer {admin_token}"}
    )

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    assert any(env["name"] == "list-test-env" for env in data)


def test_list_environments_requires_authentication(client):
    """Test that listing environments requires authentication."""
    response = client.get("/environments/")

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_get_environment_success(client, admin_token):
    """Test successful retrieval of environment by UUID."""
    # Create an environment
    create_response = client.post(
        "/environments/",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"name": "get-test-env"}
    )
    assert create_response.status_code == status.HTTP_200_OK
    env_uuid = create_response.json()["uuid"]

    # Get environment
    response = client.get(
        f"/environments/{env_uuid}",
        headers={"Authorization": f"Bearer {admin_token}"}
    )

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["name"] == "get-test-env"
    assert data["uuid"] == env_uuid
    assert "clusters" in data
    assert "settings" in data


def test_get_environment_not_found(client, admin_token):
    """Test that getting non-existent environment returns 404."""
    fake_uuid = uuid4()
    response = client.get(
        f"/environments/{fake_uuid}",
        headers={"Authorization": f"Bearer {admin_token}"}
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_get_environment_requires_authentication(client):
    """Test that getting environment requires authentication."""
    fake_uuid = uuid4()
    response = client.get(f"/environments/{fake_uuid}")

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_update_environment_success(client, admin_token):
    """Test successful environment update."""
    # Create an environment
    create_response = client.post(
        "/environments/",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"name": "update-test-env"}
    )
    assert create_response.status_code == status.HTTP_200_OK
    env_uuid = create_response.json()["uuid"]

    # Update environment
    response = client.put(
        f"/environments/{env_uuid}",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"name": "updated-env-name"}
    )

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["name"] == "updated-env-name"
    assert data["uuid"] == env_uuid


def test_update_environment_not_found(client, admin_token):
    """Test that updating non-existent environment returns 404."""
    fake_uuid = uuid4()
    response = client.put(
        f"/environments/{fake_uuid}",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"name": "updated-name"}
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_update_environment_requires_admin_role(client, user_token):
    """Test that updating environment requires admin role."""
    fake_uuid = uuid4()
    response = client.put(
        f"/environments/{fake_uuid}",
        headers={"Authorization": f"Bearer {user_token}"},
        json={"name": "updated-name"}
    )

    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_delete_environment_success(client, admin_token):
    """Test successful environment deletion."""
    # Create an environment
    create_response = client.post(
        "/environments/",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"name": "delete-test-env"}
    )
    assert create_response.status_code == status.HTTP_200_OK
    env_uuid = create_response.json()["uuid"]

    # Delete environment
    response = client.delete(
        f"/environments/{env_uuid}",
        headers={"Authorization": f"Bearer {admin_token}"}
    )

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "detail" in data

    # Verify it's deleted
    get_response = client.get(
        f"/environments/{env_uuid}",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert get_response.status_code == status.HTTP_404_NOT_FOUND


def test_delete_environment_not_found(client, admin_token):
    """Test that deleting non-existent environment returns 404."""
    fake_uuid = uuid4()
    response = client.delete(
        f"/environments/{fake_uuid}",
        headers={"Authorization": f"Bearer {admin_token}"}
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_delete_environment_requires_admin_role(client, user_token):
    """Test that deleting environment requires admin role."""
    fake_uuid = uuid4()
    response = client.delete(
        f"/environments/{fake_uuid}",
        headers={"Authorization": f"Bearer {user_token}"}
    )

    assert response.status_code == status.HTTP_403_FORBIDDEN

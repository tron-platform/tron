"""Integration tests for users endpoints."""
import pytest
from fastapi import status
from uuid import uuid4


def test_create_user_success(client, admin_token):
    """Test successful user creation."""
    response = client.post(
        "/users",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "email": "newuser@test.com",
            "full_name": "New User",
            "password": "password123"
        }
    )

    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["email"] == "newuser@test.com"
    assert data["full_name"] == "New User"
    assert "uuid" in data
    assert data["is_active"] is True
    assert data["role"] == "user"


def test_create_user_requires_authentication(client):
    """Test that user creation requires authentication."""
    response = client.post(
        "/users",
        json={
            "email": "newuser@test.com",
            "password": "password123"
        }
    )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_create_user_requires_admin_role(client, user_token):
    """Test that user creation requires admin role."""
    response = client.post(
        "/users",
        headers={"Authorization": f"Bearer {user_token}"},
        json={
            "email": "newuser@test.com",
            "password": "password123"
        }
    )

    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_create_user_duplicate_email(client, admin_token):
    """Test that creating user with duplicate email fails."""
    # Create first user
    response1 = client.post(
        "/users",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "email": "duplicate@test.com",
            "password": "password123"
        }
    )
    assert response1.status_code == status.HTTP_201_CREATED

    # Try to create duplicate
    response2 = client.post(
        "/users",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "email": "duplicate@test.com",
            "password": "password123"
        }
    )
    assert response2.status_code == status.HTTP_400_BAD_REQUEST


def test_list_users_success(client, admin_token):
    """Test successful user listing."""
    response = client.get(
        "/users",
        headers={"Authorization": f"Bearer {admin_token}"}
    )

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1  # At least admin user from fixtures


def test_list_users_requires_authentication(client):
    """Test that listing users requires authentication."""
    response = client.get("/users")

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_list_users_requires_admin_role(client, user_token):
    """Test that listing users requires admin role."""
    response = client.get(
        "/users",
        headers={"Authorization": f"Bearer {user_token}"}
    )

    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_get_user_success(client, admin_token, regular_user):
    """Test successful retrieval of user by UUID."""
    response = client.get(
        f"/users/{regular_user.uuid}",
        headers={"Authorization": f"Bearer {admin_token}"}
    )

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["email"] == regular_user.email
    assert data["uuid"] == str(regular_user.uuid)


def test_get_user_not_found(client, admin_token):
    """Test that getting non-existent user returns 404."""
    fake_uuid = uuid4()
    response = client.get(
        f"/users/{fake_uuid}",
        headers={"Authorization": f"Bearer {admin_token}"}
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_get_user_requires_admin_role(client, user_token, regular_user):
    """Test that getting user requires admin role."""
    response = client.get(
        f"/users/{regular_user.uuid}",
        headers={"Authorization": f"Bearer {user_token}"}
    )

    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_update_user_success(client, admin_token, regular_user):
    """Test successful user update."""
    response = client.put(
        f"/users/{regular_user.uuid}",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "full_name": "Updated Name",
            "is_active": False
        }
    )

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["full_name"] == "Updated Name"
    assert data["is_active"] is False
    assert data["email"] == regular_user.email


def test_update_user_email(client, admin_token, regular_user):
    """Test successful user email update."""
    response = client.put(
        f"/users/{regular_user.uuid}",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "email": "updated@test.com"
        }
    )

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["email"] == "updated@test.com"


def test_update_user_duplicate_email(client, admin_token, admin_user, regular_user):
    """Test that updating user with duplicate email fails."""
    response = client.put(
        f"/users/{regular_user.uuid}",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "email": admin_user.email
        }
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_update_user_not_found(client, admin_token):
    """Test that updating non-existent user returns 404."""
    fake_uuid = uuid4()
    response = client.put(
        f"/users/{fake_uuid}",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"full_name": "Updated Name"}
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_update_user_requires_admin_role(client, user_token, regular_user):
    """Test that updating user requires admin role."""
    response = client.put(
        f"/users/{regular_user.uuid}",
        headers={"Authorization": f"Bearer {user_token}"},
        json={"full_name": "Updated Name"}
    )

    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_delete_user_success(client, admin_token):
    """Test successful user deletion."""
    # Create a user to delete
    create_response = client.post(
        "/users",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "email": "todelete@test.com",
            "password": "password123"
        }
    )
    assert create_response.status_code == status.HTTP_201_CREATED
    user_uuid = create_response.json()["uuid"]

    # Delete user
    response = client.delete(
        f"/users/{user_uuid}",
        headers={"Authorization": f"Bearer {admin_token}"}
    )

    assert response.status_code == status.HTTP_204_NO_CONTENT

    # Verify it's deleted
    get_response = client.get(
        f"/users/{user_uuid}",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert get_response.status_code == status.HTTP_404_NOT_FOUND


def test_delete_user_not_found(client, admin_token):
    """Test that deleting non-existent user returns 404."""
    fake_uuid = uuid4()
    response = client.delete(
        f"/users/{fake_uuid}",
        headers={"Authorization": f"Bearer {admin_token}"}
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_delete_user_cannot_delete_self(client, admin_token, admin_user):
    """Test that user cannot delete themselves."""
    response = client.delete(
        f"/users/{admin_user.uuid}",
        headers={"Authorization": f"Bearer {admin_token}"}
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_delete_user_requires_admin_role(client, user_token):
    """Test that deleting user requires admin role."""
    fake_uuid = uuid4()
    response = client.delete(
        f"/users/{fake_uuid}",
        headers={"Authorization": f"Bearer {user_token}"}
    )

    assert response.status_code == status.HTTP_403_FORBIDDEN

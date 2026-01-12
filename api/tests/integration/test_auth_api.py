"""Integration tests for authentication endpoints."""
import pytest
from fastapi import status


def test_login_success(client, admin_user):
    """Test successful login."""
    response = client.post(
        "/auth/login",
        json={"email": "admin@test.com", "password": "admin123"}
    )

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"
    assert len(data["access_token"]) > 0
    assert len(data["refresh_token"]) > 0


def test_login_invalid_email(client):
    """Test login with invalid email."""
    response = client.post(
        "/auth/login",
        json={"email": "nonexistent@test.com", "password": "password123"}
    )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert "incorretos" in response.json()["detail"].lower()


def test_login_invalid_password(client, admin_user):
    """Test login with invalid password."""
    response = client.post(
        "/auth/login",
        json={"email": "admin@test.com", "password": "wrongpassword"}
    )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert "incorretos" in response.json()["detail"].lower()


def test_login_missing_fields(client):
    """Test login with missing required fields."""
    response = client.post(
        "/auth/login",
        json={"email": "admin@test.com"}
    )

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_register_success(client):
    """Test successful user registration."""
    response = client.post(
        "/auth/register",
        json={
            "email": "newuser@test.com",
            "password": "password123",
            "full_name": "New User"
        }
    )

    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["email"] == "newuser@test.com"
    assert data["full_name"] == "New User"
    assert "uuid" in data
    assert "password" not in data  # Password should not be in response


def test_register_duplicate_email(client, admin_user):
    """Test registration with duplicate email."""
    response = client.post(
        "/auth/register",
        json={
            "email": "admin@test.com",
            "password": "password123",
            "full_name": "Duplicate User"
        }
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_register_missing_fields(client):
    """Test registration with missing required fields."""
    response = client.post(
        "/auth/register",
        json={"email": "newuser@test.com"}
    )

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_refresh_token_success(client, admin_token, admin_user):
    """Test successful token refresh."""
    # First, get refresh token from login
    login_response = client.post(
        "/auth/login",
        json={"email": "admin@test.com", "password": "admin123"}
    )
    refresh_token = login_response.json()["refresh_token"]

    # Now refresh the token
    response = client.post(
        "/auth/refresh",
        json={"refresh_token": refresh_token}
    )

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


def test_refresh_token_invalid(client):
    """Test refresh with invalid token."""
    response = client.post(
        "/auth/refresh",
        json={"refresh_token": "invalid_token"}
    )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_get_current_user_success(client, admin_token):
    """Test getting current user information."""
    response = client.get(
        "/auth/me",
        headers={"Authorization": f"Bearer {admin_token}"}
    )

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["email"] == "admin@test.com"
    assert "uuid" in data
    assert "password" not in data


def test_get_current_user_unauthorized(client):
    """Test getting current user without authentication."""
    response = client.get("/auth/me")

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_get_current_user_invalid_token(client):
    """Test getting current user with invalid token."""
    response = client.get(
        "/auth/me",
        headers={"Authorization": "Bearer invalid_token"}
    )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_update_profile_success(client, admin_token, admin_user):
    """Test successful profile update."""
    response = client.put(
        "/auth/me",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "full_name": "Updated Admin Name",
            "email": "admin@test.com"
        }
    )

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["full_name"] == "Updated Admin Name"


def test_update_profile_with_password(client, admin_token, admin_user):
    """Test profile update with password change."""
    response = client.put(
        "/auth/me",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "current_password": "admin123",
            "password": "newpassword123"
        }
    )

    assert response.status_code == status.HTTP_200_OK

    # Verify new password works
    login_response = client.post(
        "/auth/login",
        json={"email": "admin@test.com", "password": "newpassword123"}
    )
    assert login_response.status_code == status.HTTP_200_OK


def test_update_profile_wrong_current_password(client, admin_token, admin_user):
    """Test profile update with wrong current password."""
    response = client.put(
        "/auth/me",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "current_password": "wrongpassword",
            "password": "newpassword123"
        }
    )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED

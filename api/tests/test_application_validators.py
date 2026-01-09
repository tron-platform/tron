"""Tests for application validators."""
import pytest
from uuid import uuid4
from unittest.mock import MagicMock
from app.applications.core.application_validators import (
    validate_application_name_uniqueness,
    validate_application_exists,
    ApplicationNameAlreadyExistsError,
    ApplicationNotFoundError
)


def test_validate_application_name_uniqueness_unique(mock_db):
    """Test validation when name is unique."""
    repository = MagicMock()
    repository.find_by_name.return_value = None

    # Should not raise exception
    validate_application_name_uniqueness(repository, "unique-name")


def test_validate_application_name_uniqueness_duplicate(mock_db):
    """Test validation when name already exists."""
    repository = MagicMock()
    existing_app = MagicMock()
    existing_app.name = "existing-name"
    repository.find_by_name.return_value = existing_app

    with pytest.raises(ApplicationNameAlreadyExistsError):
        validate_application_name_uniqueness(repository, "existing-name")


def test_validate_application_name_uniqueness_excluding_uuid(mock_db):
    """Test validation when excluding UUID."""
    repository = MagicMock()
    exclude_uuid = uuid4()
    repository.find_by_name_excluding_uuid.return_value = None

    # Should not raise exception when excluding UUID
    validate_application_name_uniqueness(repository, "name", exclude_uuid=exclude_uuid)


def test_validate_application_exists_found(mock_db):
    """Test validation when application exists."""
    repository = MagicMock()
    app_uuid = uuid4()
    mock_application = MagicMock()
    mock_application.uuid = app_uuid
    repository.find_by_uuid.return_value = mock_application

    # Should not raise exception
    validate_application_exists(repository, app_uuid)


def test_validate_application_exists_not_found(mock_db):
    """Test validation when application doesn't exist."""
    repository = MagicMock()
    app_uuid = uuid4()
    repository.find_by_uuid.return_value = None

    with pytest.raises(ApplicationNotFoundError):
        validate_application_exists(repository, app_uuid)

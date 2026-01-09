"""Tests for shared application component helpers."""
import pytest
from uuid import uuid4
from unittest.mock import MagicMock, patch
from app.shared.core.application_component_helpers import (
    ensure_private_exposure_settings,
    build_application_component_entity,
    update_component_enabled_field
)
from app.webapps.infra.application_component_model import WebappType


def test_ensure_private_exposure_settings_no_exposure():
    """Test ensuring private exposure when exposure doesn't exist."""
    settings = {"cpu": 0.25, "memory": 128}

    result = ensure_private_exposure_settings(settings)

    assert "exposure" in result
    assert result["exposure"]["type"] == "http"
    assert result["exposure"]["port"] == 80
    assert result["exposure"]["visibility"] == "private"


def test_ensure_private_exposure_settings_no_visibility():
    """Test ensuring private exposure when visibility is missing."""
    settings = {
        "cpu": 0.25,
        "exposure": {"type": "http", "port": 80}
    }

    result = ensure_private_exposure_settings(settings)

    assert result["exposure"]["visibility"] == "private"


def test_ensure_private_exposure_settings_already_has_visibility():
    """Test when visibility already exists."""
    settings = {
        "cpu": 0.25,
        "exposure": {"type": "http", "port": 80, "visibility": "private"}
    }

    result = ensure_private_exposure_settings(settings)

    assert result["exposure"]["visibility"] == "private"


def test_build_application_component_entity(mock_db):
    """Test building application component entity."""
    settings_dict = {"cpu": 0.25, "memory": 128}

    # Mock ApplicationComponentModel to avoid SQLAlchemy initialization issues
    with patch('app.shared.core.application_component_helpers.ApplicationComponentModel') as mock_model:
        mock_instance = MagicMock()
        mock_instance.name = "test-component"
        mock_instance.instance_id = 1
        mock_instance.settings = settings_dict
        mock_instance.type = WebappType.worker
        mock_instance.url = None
        mock_instance.enabled = True
        mock_instance.uuid = uuid4()
        mock_model.return_value = mock_instance

        result = build_application_component_entity(
            name="test-component",
            instance_id=1,
            settings_dict=settings_dict,
            component_type=WebappType.worker,
            url=None,
            enabled=True
        )

        assert result == mock_instance
        mock_model.assert_called_once()


def test_update_component_enabled_field_changed(mock_db):
    """Test updating enabled field when it changes."""
    repository = MagicMock()
    component = MagicMock()
    component.enabled = False

    result = update_component_enabled_field(component, True, repository)

    assert result["changed"] is True
    assert result["was_enabled"] is False
    assert result["will_be_enabled"] is True
    assert component.enabled is True
    repository.update.assert_called_once_with(component)


def test_update_component_enabled_field_not_changed(mock_db):
    """Test updating enabled field when it doesn't change."""
    repository = MagicMock()
    component = MagicMock()
    component.enabled = True

    result = update_component_enabled_field(component, True, repository)

    assert result["changed"] is False
    assert result["was_enabled"] is True
    assert result["will_be_enabled"] is True
    assert component.enabled is True
    repository.update.assert_called_once_with(component)


def test_update_component_enabled_field_none(mock_db):
    """Test updating enabled field when value is None."""
    repository = MagicMock()
    component = MagicMock()
    component.enabled = True

    result = update_component_enabled_field(component, None, repository)

    assert result["changed"] is False
    assert result["was_enabled"] is True
    assert result["will_be_enabled"] is True
    assert component.enabled is True
    repository.update.assert_called_once_with(component)

"""Tests for WebappService."""
import pytest
from uuid import uuid4, UUID
from unittest.mock import MagicMock, patch
from app.webapps.core.webapp_service import WebappService
from app.webapps.infra.webapp_repository import WebappRepository
from app.webapps.api.webapp_dto import WebappCreate, WebappUpdate
from app.webapps.core.webapp_validators import (
    WebappNotFoundError,
    InstanceNotFoundError
)
from app.webapps.infra.application_component_model import WebappType


@pytest.fixture
def mock_repository():
    """Create a mock WebappRepository."""
    return MagicMock(spec=WebappRepository)


@pytest.fixture
def mock_db():
    """Create a mock database session."""
    return MagicMock()


@pytest.fixture
def webapp_service(mock_repository, mock_db):
    """Create WebappService instance."""
    return WebappService(mock_repository, mock_db)


@pytest.fixture
def mock_instance():
    """Create a mock instance."""
    instance = MagicMock()
    instance.id = 1
    instance.uuid = uuid4()
    instance.environment_id = 1
    instance.application = MagicMock()
    instance.application.name = "test-app"
    return instance


@pytest.fixture
def mock_cluster():
    """Create a mock cluster."""
    cluster = MagicMock()
    cluster.id = 1
    cluster.name = "test-cluster"
    cluster.api_address = "https://k8s.example.com"
    cluster.token = "test-token"
    return cluster


@pytest.fixture
def mock_webapp():
    """Create a mock webapp component."""
    from datetime import datetime

    webapp = MagicMock()
    webapp.uuid = uuid4()
    webapp.id = 1
    webapp.name = "test-webapp"
    webapp.type = WebappType.webapp
    webapp.enabled = True
    webapp.url = "https://test.example.com"
    webapp.settings = {
        "cpu": 0.5,
        "memory": 512,
        "exposure": {"type": "http", "port": 80, "visibility": "public"}
    }
    webapp.created_at = datetime.now()
    webapp.updated_at = datetime.now()
    webapp.instance = MagicMock()
    webapp.instance.environment_id = 1
    return webapp


def test_create_webapp_success(webapp_service, mock_repository, mock_db, mock_instance, mock_cluster):
    """Test successful webapp creation."""
    from app.webapps.api.webapp_dto import WebappSettings, WebappExposure, VisibilityType, WebappCustomMetrics, WebappHealthcheck, WebappAutoscaling

    dto = WebappCreate(
        instance_uuid=mock_instance.uuid,
        name="test-webapp",
        url="https://test.example.com",
        enabled=True,
        settings=WebappSettings(
            cpu=0.5,
            memory=512,
            exposure=WebappExposure(type="http", port=80, visibility=VisibilityType.public),
            custom_metrics=WebappCustomMetrics(enabled=False, path="/metrics", port=9090),
            healthcheck=WebappHealthcheck(path="/health", protocol="http", port=80),
            autoscaling=WebappAutoscaling(min=2, max=10),
            envs=[],
            command=None
        )
    )

    from datetime import datetime

    mock_webapp = MagicMock()
    mock_webapp.uuid = uuid4()
    mock_webapp.name = dto.name
    mock_webapp.type = WebappType.webapp
    mock_webapp.enabled = dto.enabled
    mock_webapp.url = dto.url
    mock_webapp.created_at = datetime.now()
    mock_webapp.updated_at = datetime.now()
    mock_webapp.settings = dto.settings.model_dump()

    mock_repository.find_instance_by_uuid.return_value = mock_instance
    mock_repository.create.return_value = mock_webapp

    mock_cluster_instance = MagicMock()
    mock_cluster_instance.cluster = mock_cluster

    with patch('app.webapps.core.webapp_service.get_cluster_for_instance', return_value=mock_cluster), \
         patch('app.webapps.core.webapp_service.ensure_cluster_instance', return_value=mock_cluster_instance), \
         patch.object(webapp_service, '_deploy_to_kubernetes') as mock_deploy, \
         patch.object(webapp_service, '_build_webapp_entity', return_value=mock_webapp), \
         patch('app.webapps.core.webapp_service.validate_exposure_type_for_cluster') as mock_validate_exposure, \
         patch('app.webapps.core.webapp_service.validate_visibility_for_cluster') as mock_validate_visibility, \
         patch('app.webapps.core.webapp_service.validate_url_for_exposure'):

        result = webapp_service.create_webapp(dto)

        assert result.uuid == mock_webapp.uuid
        # Validator also calls find_instance_by_uuid
        assert mock_repository.find_instance_by_uuid.call_count >= 1
        mock_repository.create.assert_called_once()
        mock_deploy.assert_called_once()
        # Validations should be called
        mock_validate_exposure.assert_called_once()
        mock_validate_visibility.assert_called_once()


def test_create_webapp_instance_not_found(webapp_service, mock_repository):
    """Test webapp creation with non-existent instance."""
    from app.webapps.api.webapp_dto import WebappSettings, WebappExposure, VisibilityType, WebappCustomMetrics, WebappHealthcheck, WebappAutoscaling

    dto = WebappCreate(
        instance_uuid=uuid4(),
        name="test-webapp",
        url="https://test.example.com",
        enabled=True,
        settings=WebappSettings(
            cpu=0.5,
            memory=512,
            exposure=WebappExposure(type="http", port=80, visibility=VisibilityType.public),
            custom_metrics=WebappCustomMetrics(enabled=False, path="/metrics", port=9090),
            healthcheck=WebappHealthcheck(path="/health", protocol="http", port=80),
            autoscaling=WebappAutoscaling(min=2, max=10),
            envs=[],
            command=None
        )
    )

    mock_repository.find_instance_by_uuid.return_value = None

    with pytest.raises(InstanceNotFoundError):
        webapp_service.create_webapp(dto)


def test_update_webapp_success(webapp_service, mock_repository, mock_db, mock_webapp, mock_cluster):
    """Test successful webapp update."""
    from app.webapps.api.webapp_dto import WebappSettings, WebappExposure, VisibilityType, WebappCustomMetrics, WebappHealthcheck, WebappAutoscaling

    webapp_uuid = mock_webapp.uuid
    dto = WebappUpdate(
        enabled=False,
        settings=WebappSettings(
            cpu=1.0,
            memory=1024,
            exposure=WebappExposure(type="http", port=80, visibility=VisibilityType.public),
            custom_metrics=WebappCustomMetrics(enabled=False, path="/metrics", port=9090),
            healthcheck=WebappHealthcheck(path="/health", protocol="http", port=80),
            autoscaling=WebappAutoscaling(min=2, max=10),
            envs=[],
            command=None
        )
    )

    mock_repository.find_by_uuid.return_value = mock_webapp

    mock_cluster_instance = MagicMock()
    mock_cluster_instance.cluster = mock_cluster

    with patch('app.webapps.core.webapp_service.get_or_create_cluster_instance', return_value=mock_cluster_instance), \
         patch.object(webapp_service, '_update_webapp_fields', return_value={'changed': True, 'was_enabled': True, 'will_be_enabled': False}), \
         patch.object(webapp_service, '_delete_from_kubernetes_safe') as mock_delete:

        result = webapp_service.update_webapp(webapp_uuid, dto)

        assert result is not None
        mock_repository.find_by_uuid.assert_called()


def test_get_webapp_success(webapp_service, mock_repository, mock_webapp):
    """Test getting webapp by UUID."""
    webapp_uuid = mock_webapp.uuid
    mock_repository.find_by_uuid.return_value = mock_webapp

    result = webapp_service.get_webapp(webapp_uuid)

    assert result.uuid == webapp_uuid
    mock_repository.find_by_uuid.assert_called()


def test_get_webapp_not_found(webapp_service, mock_repository):
    """Test getting non-existent webapp."""
    webapp_uuid = uuid4()
    mock_repository.find_by_uuid.return_value = None

    with pytest.raises(WebappNotFoundError):
        webapp_service.get_webapp(webapp_uuid)


def test_get_webapps(webapp_service, mock_repository, mock_webapp):
    """Test getting all webapps."""
    from datetime import datetime

    mock_webapp2 = MagicMock()
    mock_webapp2.uuid = uuid4()
    mock_webapp2.name = "test-webapp-2"
    mock_webapp2.type = WebappType.webapp
    mock_webapp2.enabled = True
    mock_webapp2.url = None
    mock_webapp2.settings = {}
    mock_webapp2.created_at = datetime.now()
    mock_webapp2.updated_at = datetime.now()

    mock_repository.find_all.return_value = [mock_webapp, mock_webapp2]

    result = webapp_service.get_webapps(skip=0, limit=10)

    assert len(result) == 2
    mock_repository.find_all.assert_called_once_with(skip=0, limit=10)


def test_delete_webapp_success(webapp_service, mock_repository, mock_db, mock_webapp, mock_cluster):
    """Test successful webapp deletion."""
    webapp_uuid = mock_webapp.uuid
    mock_repository.find_by_uuid.return_value = mock_webapp

    with patch('app.webapps.core.webapp_service.delete_component', return_value={"detail": "Webapp deleted successfully"}) as mock_delete:
        result = webapp_service.delete_webapp(webapp_uuid)

        assert result == {"detail": "Webapp deleted successfully"}
        mock_repository.find_by_uuid.assert_called()
        mock_delete.assert_called_once()


def test_delete_webapp_not_found(webapp_service, mock_repository):
    """Test deleting non-existent webapp."""
    webapp_uuid = uuid4()
    mock_repository.find_by_uuid.return_value = None

    with pytest.raises(WebappNotFoundError):
        webapp_service.delete_webapp(webapp_uuid)

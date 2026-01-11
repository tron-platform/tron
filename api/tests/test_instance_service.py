"""Tests for InstanceService."""
import pytest
from uuid import uuid4, UUID
from unittest.mock import MagicMock, patch
from app.instances.core.instance_service import InstanceService
from app.instances.infra.instance_repository import InstanceRepository
from app.instances.api.instance_dto import InstanceCreate, InstanceUpdate
from app.instances.core.instance_validators import (
    InstanceNotFoundError,
    InstanceAlreadyExistsError,
    ApplicationNotFoundError,
    EnvironmentNotFoundError
)
from app.webapps.infra.application_component_model import WebappType


@pytest.fixture
def mock_repository():
    """Create a mock InstanceRepository."""
    return MagicMock(spec=InstanceRepository)


@pytest.fixture
def mock_db():
    """Create a mock database session."""
    return MagicMock()


@pytest.fixture
def instance_service(mock_repository, mock_db):
    """Create InstanceService instance."""
    return InstanceService(mock_repository, mock_db)


def test_create_instance_success(instance_service, mock_repository):
    """Test successful instance creation."""
    app_uuid = uuid4()
    env_uuid = uuid4()
    dto = InstanceCreate(
        application_uuid=app_uuid,
        environment_uuid=env_uuid,
        image="nginx",
        version="1.0.0"
    )

    mock_application = MagicMock()
    mock_application.id = 1
    mock_application.uuid = app_uuid

    mock_environment = MagicMock()
    mock_environment.id = 1
    mock_environment.uuid = env_uuid

    mock_instance = MagicMock()
    mock_instance.uuid = uuid4()

    mock_repository.find_application_by_uuid.return_value = mock_application
    mock_repository.find_environment_by_uuid.return_value = mock_environment
    mock_repository.find_by_application_and_environment.return_value = None  # Unique
    mock_repository.create.return_value = mock_instance

    # Mock _build_instance_entity to avoid SQLAlchemy initialization issues
    with patch.object(instance_service, '_build_instance_entity') as mock_build:
        mock_build.return_value = mock_instance
        result = instance_service.create_instance(dto)

    assert result == mock_instance
    # Validator calls find_application_by_uuid, then service calls it again
    assert mock_repository.find_application_by_uuid.call_count >= 1
    # Check that it was called with the correct UUID at least once
    assert any(call[0][0] == app_uuid for call in mock_repository.find_application_by_uuid.call_args_list)
    # Validator calls find_environment_by_uuid, then service calls it again
    assert mock_repository.find_environment_by_uuid.call_count >= 1
    # Check that it was called with the correct UUID at least once
    assert any(call[0][0] == env_uuid for call in mock_repository.find_environment_by_uuid.call_args_list)
    mock_repository.create.assert_called_once()


def test_create_instance_application_not_found(instance_service, mock_repository):
    """Test instance creation with non-existent application."""
    app_uuid = uuid4()
    env_uuid = uuid4()
    dto = InstanceCreate(
        application_uuid=app_uuid,
        environment_uuid=env_uuid,
        image="nginx",
        version="1.0.0"
    )

    mock_repository.find_application_by_uuid.return_value = None

    with pytest.raises(ApplicationNotFoundError):
        instance_service.create_instance(dto)

    mock_repository.find_application_by_uuid.assert_called_once_with(app_uuid)
    mock_repository.create.assert_not_called()


def test_create_instance_environment_not_found(instance_service, mock_repository):
    """Test instance creation with non-existent environment."""
    app_uuid = uuid4()
    env_uuid = uuid4()
    dto = InstanceCreate(
        application_uuid=app_uuid,
        environment_uuid=env_uuid,
        image="nginx",
        version="1.0.0"
    )

    mock_application = MagicMock()
    mock_application.id = 1
    mock_repository.find_application_by_uuid.return_value = mock_application
    mock_repository.find_environment_by_uuid.return_value = None

    with pytest.raises(EnvironmentNotFoundError):
        instance_service.create_instance(dto)

    mock_repository.find_environment_by_uuid.assert_called_once_with(env_uuid)
    mock_repository.create.assert_not_called()


def test_update_instance_success(instance_service, mock_repository):
    """Test successful instance update."""
    instance_uuid = uuid4()
    dto = InstanceUpdate(image="nginx:latest", version="2.0.0")

    mock_instance = MagicMock()
    mock_instance.uuid = instance_uuid
    mock_instance.image = "nginx"
    mock_instance.version = "1.0.0"
    mock_instance.enabled = True

    updated_instance = MagicMock()
    updated_instance.uuid = instance_uuid
    updated_instance.image = dto.image
    updated_instance.version = dto.version

    mock_repository.find_by_uuid.return_value = mock_instance
    mock_repository.update.return_value = updated_instance

    result = instance_service.update_instance(instance_uuid, dto)

    assert result == updated_instance
    assert mock_instance.image == dto.image
    assert mock_instance.version == dto.version
    mock_repository.update.assert_called_once()


def test_get_instance_success(instance_service, mock_repository):
    """Test getting instance by UUID."""
    instance_uuid = uuid4()
    mock_instance = MagicMock()
    mock_instance.uuid = instance_uuid
    mock_repository.find_by_uuid.return_value = mock_instance

    result = instance_service.get_instance(instance_uuid)

    assert result == mock_instance
    # Validator calls find_by_uuid without load_components, service calls with load_components=True
    assert mock_repository.find_by_uuid.call_count >= 1
    # Check that it was called with load_components=True at least once
    assert any(
        call.kwargs.get('load_components') == True
        for call in mock_repository.find_by_uuid.call_args_list
        if call.kwargs
    )


def test_get_instance_not_found(instance_service, mock_repository):
    """Test getting non-existent instance."""
    instance_uuid = uuid4()
    mock_repository.find_by_uuid.return_value = None

    with pytest.raises(InstanceNotFoundError):
        instance_service.get_instance(instance_uuid)

    # Validator calls find_by_uuid without load_components first, which returns None
    # So the exception is raised before service calls it with load_components
    assert mock_repository.find_by_uuid.call_count >= 1


def test_delete_instance_success(instance_service, mock_repository, mock_db):
    """Test successful instance deletion."""
    instance_uuid = uuid4()
    mock_instance = MagicMock()
    mock_instance.uuid = instance_uuid
    mock_instance.id = 1
    mock_instance.components = []  # No components

    mock_repository.find_by_uuid.return_value = mock_instance
    mock_repository.find_by_uuid_with_relations.return_value = mock_instance

    with patch.object(instance_service, '_get_component_repository') as mock_get_repo:
        result = instance_service.delete_instance(instance_uuid, mock_db)

        assert result == {"detail": "Instance deleted successfully"}
        # Validator calls find_by_uuid, then service calls find_by_uuid_with_relations
        assert mock_repository.find_by_uuid.call_count >= 1
        assert mock_repository.find_by_uuid_with_relations.call_count >= 1
        mock_repository.delete_by_id.assert_called_once_with(mock_instance.id)


def test_delete_instance_with_components(instance_service, mock_repository, mock_db):
    """Test instance deletion with components."""
    instance_uuid = uuid4()
    mock_instance = MagicMock()
    mock_instance.uuid = instance_uuid
    mock_instance.id = 1

    # Create mock components
    mock_component1 = MagicMock()
    mock_component1.id = 1
    mock_component1.name = "webapp-1"
    mock_component1.type = WebappType.webapp  # Use real enum value

    mock_component2 = MagicMock()
    mock_component2.id = 2
    mock_component2.name = "worker-1"
    mock_component2.type = WebappType.worker  # Use real enum value

    mock_instance.components = [mock_component1, mock_component2]

    mock_repository.find_by_uuid.return_value = mock_instance
    mock_repository.find_by_uuid_with_relations.return_value = mock_instance

    # Mock component repositories
    mock_webapp_repo = MagicMock()
    mock_webapp_repo.find_cluster_instance_by_component_id.return_value = None
    mock_webapp_repo.delete.return_value = None

    mock_worker_repo = MagicMock()
    mock_worker_repo.find_cluster_instance_by_component_id.return_value = None
    mock_worker_repo.delete.return_value = None

    with patch.object(instance_service, '_get_component_repository') as mock_get_repo:
        def get_repo_side_effect(component):
            if component.type == WebappType.webapp:
                return mock_webapp_repo
            elif component.type == WebappType.worker:
                return mock_worker_repo
            return mock_webapp_repo

        mock_get_repo.side_effect = get_repo_side_effect

        with patch('app.instances.core.instance_service.delete_component') as mock_delete_component:
            mock_delete_component.return_value = {"detail": "Component deleted successfully"}

            result = instance_service.delete_instance(instance_uuid, mock_db)

            assert result == {"detail": "Instance deleted successfully"}
            # Should delete both components
            assert mock_delete_component.call_count == 2
            # Should commit after component deletions
            assert mock_db.commit.call_count >= 2
            mock_repository.delete_by_id.assert_called_once_with(mock_instance.id)


def test_delete_instance_not_found(instance_service, mock_repository, mock_db):
    """Test deleting non-existent instance."""
    instance_uuid = uuid4()
    mock_repository.find_by_uuid.return_value = None

    with pytest.raises(InstanceNotFoundError):
        instance_service.delete_instance(instance_uuid, mock_db)

    mock_repository.delete_by_id.assert_not_called()


def test_get_instance_events_success(instance_service, mock_repository, mock_db):
    """Test getting instance events successfully."""
    instance_uuid = uuid4()
    mock_instance = MagicMock()
    mock_instance.uuid = instance_uuid
    mock_instance.id = 1
    mock_instance.environment_id = 1
    mock_instance.environment = MagicMock()
    mock_instance.environment.name = "test-env"
    mock_instance.application = MagicMock()
    mock_instance.application.name = "test-app"

    mock_repository.find_by_uuid.return_value = mock_instance
    mock_repository.find_by_uuid_with_relations.return_value = mock_instance

    mock_cluster = MagicMock()
    mock_cluster.api_address = "https://k8s.example.com"
    mock_cluster.token = "test-token"

    mock_events = [
        {
            "name": "event-1",
            "namespace": "test-app",
            "type": "Normal",
            "reason": "Started",
            "message": "Container started",
            "involved_object": {"kind": "Pod", "name": "pod-1", "namespace": "test-app"},
            "source": {"component": "kubelet", "host": "node-1"},
            "first_timestamp": "2024-01-01T00:00:00Z",
            "last_timestamp": "2024-01-01T00:00:00Z",
            "count": 1,
            "age_seconds": 3600,
        }
    ]

    with patch('app.instances.core.instance_service.ClusterSelectionService.get_cluster_with_least_load_or_raise') as mock_get_cluster, \
         patch('app.instances.core.instance_service.K8sClient') as mock_k8s_client_class:
        mock_get_cluster.return_value = mock_cluster
        mock_k8s_client = MagicMock()
        mock_k8s_client.list_events.return_value = mock_events
        mock_k8s_client_class.return_value = mock_k8s_client

        result = instance_service.get_instance_events(instance_uuid)

        assert len(result) == 1
        assert result[0]["name"] == "event-1"
        assert result[0]["namespace"] == "test-app"
        assert result[0]["type"] == "Normal"
        mock_k8s_client.list_events.assert_called_once_with(namespace="test-app")


def test_get_instance_events_no_cluster(instance_service, mock_repository, mock_db):
    """Test getting instance events when no cluster is available."""
    instance_uuid = uuid4()
    mock_instance = MagicMock()
    mock_instance.uuid = instance_uuid
    mock_instance.id = 1
    mock_instance.environment_id = 1
    mock_instance.environment = MagicMock()
    mock_instance.environment.name = "test-env"
    mock_instance.application = MagicMock()
    mock_instance.application.name = "test-app"

    mock_repository.find_by_uuid.return_value = mock_instance
    mock_repository.find_by_uuid_with_relations.return_value = mock_instance

    with patch('app.instances.core.instance_service.ClusterSelectionService.get_cluster_with_least_load_or_raise') as mock_get_cluster:
        # Simulate no cluster available
        mock_get_cluster.side_effect = Exception("No clusters available")

        result = instance_service.get_instance_events(instance_uuid)

        assert result == []


def test_sync_instance_success(instance_service, mock_repository, mock_db):
    """Test successful instance sync."""
    instance_uuid = uuid4()
    mock_instance = MagicMock()
    mock_instance.uuid = instance_uuid
    mock_instance.id = 1
    mock_instance.environment_id = 1

    # Create mock components
    mock_component = MagicMock()
    mock_component.id = 1
    mock_component.name = "webapp-1"
    mock_component.enabled = True
    mock_component.type = WebappType.webapp  # Use real enum value

    mock_instance.components = [mock_component]

    mock_repository.find_by_uuid.return_value = mock_instance
    mock_repository.find_by_uuid_with_relations.return_value = mock_instance

    # Mock settings
    mock_settings = MagicMock()
    mock_db.query.return_value.filter.return_value.first.return_value = mock_settings

    # Mock component repository
    mock_component_repo = MagicMock()
    mock_cluster_instance = MagicMock()
    mock_cluster_instance.cluster = MagicMock()
    mock_cluster_instance.cluster.name = "test-cluster"
    mock_component_repo.find_cluster_instance_by_component_id.return_value = mock_cluster_instance

    with patch.object(instance_service, '_get_component_repository') as mock_get_repo, \
         patch('app.instances.core.instance_service.get_or_create_cluster_instance') as mock_get_cluster_instance, \
         patch('app.instances.core.instance_service.upsert_webapp_to_k8s') as mock_upsert, \
         patch('app.instances.core.instance_service.serialize_settings') as mock_serialize:
        mock_get_repo.return_value = mock_component_repo
        mock_get_cluster_instance.return_value = mock_cluster_instance
        mock_serialize.return_value = {}

        result = instance_service.sync_instance(instance_uuid)

        assert result["synced_components"] == 1
        assert result["total_components"] == 1
        assert len(result["errors"]) == 0
        mock_upsert.assert_called_once()
        assert mock_db.commit.call_count >= 1


def test_sync_instance_with_errors(instance_service, mock_repository, mock_db):
    """Test instance sync with errors."""
    instance_uuid = uuid4()
    mock_instance = MagicMock()
    mock_instance.uuid = instance_uuid
    mock_instance.id = 1
    mock_instance.environment_id = 1

    # Create mock components
    mock_component = MagicMock()
    mock_component.id = 1
    mock_component.name = "webapp-1"
    mock_component.enabled = True
    mock_component.type = WebappType.webapp  # Use real enum value

    mock_instance.components = [mock_component]

    mock_repository.find_by_uuid.return_value = mock_instance
    mock_repository.find_by_uuid_with_relations.return_value = mock_instance

    # Mock settings
    mock_settings = MagicMock()
    mock_db.query.return_value.filter.return_value.first.return_value = mock_settings

    # Mock component repository
    mock_component_repo = MagicMock()
    mock_cluster_instance = MagicMock()
    mock_cluster_instance.cluster = MagicMock()
    mock_cluster_instance.cluster.name = "test-cluster"
    mock_component_repo.find_cluster_instance_by_component_id.return_value = mock_cluster_instance

    with patch.object(instance_service, '_get_component_repository') as mock_get_repo, \
         patch('app.instances.core.instance_service.get_or_create_cluster_instance') as mock_get_cluster_instance, \
         patch('app.instances.core.instance_service.upsert_webapp_to_k8s') as mock_upsert, \
         patch('app.instances.core.instance_service.serialize_settings') as mock_serialize:
        mock_get_repo.return_value = mock_component_repo
        mock_get_cluster_instance.return_value = mock_cluster_instance
        mock_serialize.return_value = {}
        # Simulate error during sync
        mock_upsert.side_effect = Exception("Kubernetes error")

        result = instance_service.sync_instance(instance_uuid)

        assert result["synced_components"] == 0
        assert result["total_components"] == 1
        assert len(result["errors"]) == 1
        assert result["errors"][0]["component"] == "webapp-1"
        assert "error" in result["errors"][0]


def test_update_instance_partial(instance_service, mock_repository):
    """Test partial instance update."""
    instance_uuid = uuid4()
    dto = InstanceUpdate(version="2.0.0")  # Only update version

    mock_instance = MagicMock()
    mock_instance.uuid = instance_uuid
    mock_instance.image = "nginx"
    mock_instance.version = "1.0.0"
    mock_instance.enabled = True

    updated_instance = MagicMock()
    updated_instance.uuid = instance_uuid

    mock_repository.find_by_uuid.return_value = mock_instance
    mock_repository.update.return_value = updated_instance

    result = instance_service.update_instance(instance_uuid, dto)

    assert result == updated_instance
    assert mock_instance.version == dto.version
    # Image should not be updated
    mock_repository.update.assert_called_once()


def test_get_instances(instance_service, mock_repository):
    """Test getting all instances."""
    mock_instance1 = MagicMock()
    mock_instance1.uuid = uuid4()
    mock_instance2 = MagicMock()
    mock_instance2.uuid = uuid4()

    mock_repository.find_all.return_value = [mock_instance1, mock_instance2]

    result = instance_service.get_instances(skip=0, limit=10)

    assert len(result) == 2
    mock_repository.find_all.assert_called_once_with(skip=0, limit=10, load_components=True)

"""Tests for ClusterService."""
import pytest
from uuid import uuid4, UUID
from unittest.mock import MagicMock, patch
from app.clusters.core.cluster_service import ClusterService
from app.clusters.infra.cluster_repository import ClusterRepository
from app.clusters.api.cluster_dto import ClusterCreate
from app.clusters.core.cluster_validators import (
    ClusterNotFoundError,
    ClusterConnectionError,
    EnvironmentNotFoundError
)


@pytest.fixture
def mock_repository():
    """Create a mock ClusterRepository."""
    return MagicMock(spec=ClusterRepository)


@pytest.fixture
def cluster_service(mock_repository):
    """Create ClusterService instance."""
    return ClusterService(mock_repository)


@pytest.fixture
def mock_environment():
    """Create a mock environment."""
    environment = MagicMock()
    environment.id = 1
    environment.uuid = uuid4()
    environment.name = "test-env"
    return environment


@pytest.fixture
def mock_cluster():
    """Create a mock cluster."""
    cluster = MagicMock()
    cluster.uuid = uuid4()
    cluster.id = 1
    cluster.name = "test-cluster"
    cluster.api_address = "https://k8s.example.com"
    cluster.token = "test-token"
    cluster.environment_id = 1
    cluster.environment = MagicMock()
    cluster.environment.name = "test-env"
    return cluster


def test_create_cluster_success(cluster_service, mock_repository, mock_environment):
    """Test successful cluster creation."""
    dto = ClusterCreate(
        name="test-cluster",
        api_address="https://k8s.example.com",
        token="test-token",
        environment_uuid=mock_environment.uuid
    )

    mock_cluster = MagicMock()
    mock_cluster.uuid = uuid4()
    mock_cluster.name = dto.name

    mock_repository.find_environment_by_uuid.return_value = mock_environment
    mock_repository.create.return_value = mock_cluster

    with patch.object(cluster_service, '_validate_cluster_connection'), \
         patch.object(cluster_service, '_build_cluster_entity', return_value=mock_cluster):

        result = cluster_service.create_cluster(dto)

        assert result == mock_cluster
        # Validator also calls find_environment_by_uuid
        assert mock_repository.find_environment_by_uuid.call_count >= 1
        mock_repository.create.assert_called_once()


def test_create_cluster_environment_not_found(cluster_service, mock_repository):
    """Test cluster creation with non-existent environment."""
    dto = ClusterCreate(
        name="test-cluster",
        api_address="https://k8s.example.com",
        token="test-token",
        environment_uuid=uuid4()
    )

    mock_repository.find_environment_by_uuid.return_value = None

    with pytest.raises(EnvironmentNotFoundError):
        cluster_service.create_cluster(dto)


def test_create_cluster_connection_error(cluster_service, mock_repository, mock_environment):
    """Test cluster creation with connection validation failure."""
    dto = ClusterCreate(
        name="test-cluster",
        api_address="https://invalid.example.com",
        token="invalid-token",
        environment_uuid=mock_environment.uuid
    )

    mock_repository.find_environment_by_uuid.return_value = mock_environment

    with patch.object(cluster_service, '_validate_cluster_connection', side_effect=ClusterConnectionError("Connection failed")):
        with pytest.raises(ClusterConnectionError):
            cluster_service.create_cluster(dto)


def test_update_cluster_success(cluster_service, mock_repository, mock_environment, mock_cluster):
    """Test successful cluster update."""
    cluster_uuid = mock_cluster.uuid
    dto = ClusterCreate(
        name="updated-cluster",
        api_address="https://k8s-updated.example.com",
        token="updated-token",
        environment_uuid=mock_environment.uuid
    )

    updated_cluster = MagicMock()
    updated_cluster.uuid = cluster_uuid
    updated_cluster.name = dto.name

    mock_repository.find_by_uuid.return_value = mock_cluster
    mock_repository.find_environment_by_uuid.return_value = mock_environment
    mock_repository.update.return_value = updated_cluster

    with patch.object(cluster_service, '_validate_cluster_connection'):
        result = cluster_service.update_cluster(cluster_uuid, dto)

        assert result == updated_cluster
        assert mock_cluster.name == dto.name
        assert mock_cluster.api_address == dto.api_address
        assert mock_cluster.token == dto.token
        mock_repository.update.assert_called_once()


def test_update_cluster_not_found(cluster_service, mock_repository, mock_environment):
    """Test updating non-existent cluster."""
    cluster_uuid = uuid4()
    dto = ClusterCreate(
        name="updated-cluster",
        api_address="https://k8s.example.com",
        token="test-token",
        environment_uuid=mock_environment.uuid
    )

    mock_repository.find_by_uuid.return_value = None

    with pytest.raises(ClusterNotFoundError):
        cluster_service.update_cluster(cluster_uuid, dto)


def test_get_cluster_success(cluster_service, mock_repository, mock_cluster):
    """Test getting cluster by UUID."""
    cluster_uuid = mock_cluster.uuid
    mock_repository.find_by_uuid.return_value = mock_cluster

    with patch.object(cluster_service, '_build_cluster_completed_response') as mock_build:
        mock_response = MagicMock()
        mock_build.return_value = mock_response

        result = cluster_service.get_cluster(cluster_uuid)

        assert result == mock_response
        # Validator also calls find_by_uuid
        assert mock_repository.find_by_uuid.call_count >= 1
        mock_build.assert_called_once_with(mock_cluster)


def test_get_cluster_not_found(cluster_service, mock_repository):
    """Test getting non-existent cluster."""
    cluster_uuid = uuid4()
    mock_repository.find_by_uuid.return_value = None

    with pytest.raises(ClusterNotFoundError):
        cluster_service.get_cluster(cluster_uuid)


def test_get_clusters(cluster_service, mock_repository, mock_cluster):
    """Test getting all clusters."""
    mock_cluster2 = MagicMock()
    mock_cluster2.uuid = uuid4()
    mock_cluster2.name = "test-cluster-2"

    mock_repository.find_all.return_value = [mock_cluster, mock_cluster2]

    with patch.object(cluster_service, '_build_cluster_response_with_validation') as mock_build:
        mock_build.side_effect = lambda c: MagicMock(uuid=c.uuid, name=c.name)

        result = cluster_service.get_clusters(skip=0, limit=10)

        assert len(result) == 2
        mock_repository.find_all.assert_called_once_with(skip=0, limit=10)


def test_delete_cluster_success(cluster_service, mock_repository, mock_cluster):
    """Test successful cluster deletion."""
    cluster_uuid = mock_cluster.uuid
    mock_repository.find_by_uuid.return_value = mock_cluster

    result = cluster_service.delete_cluster(cluster_uuid)

    assert result == {"detail": "Cluster deleted successfully"}
    # Validator also calls find_by_uuid
    assert mock_repository.find_by_uuid.call_count >= 1
    mock_repository.delete.assert_called_once_with(mock_cluster)


def test_delete_cluster_not_found(cluster_service, mock_repository):
    """Test deleting non-existent cluster."""
    cluster_uuid = uuid4()
    mock_repository.find_by_uuid.return_value = None

    with pytest.raises(ClusterNotFoundError):
        cluster_service.delete_cluster(cluster_uuid)


def test_validate_cluster_connection_success(cluster_service):
    """Test successful cluster connection validation."""
    api_address = "https://k8s.example.com"
    token = "test-token"

    with patch('app.clusters.core.cluster_service.K8sClient') as mock_k8s_client_class:
        mock_k8s_client = MagicMock()
        mock_k8s_client.validate_connection.return_value = (True, {"message": "Connected"})
        mock_k8s_client_class.return_value = mock_k8s_client

        # Should not raise exception
        cluster_service._validate_cluster_connection(api_address, token)

        mock_k8s_client.validate_connection.assert_called_once()


def test_validate_cluster_connection_failure(cluster_service):
    """Test cluster connection validation failure."""
    api_address = "https://invalid.example.com"
    token = "invalid-token"

    with patch('app.clusters.core.cluster_service.K8sClient') as mock_k8s_client_class:
        mock_k8s_client = MagicMock()
        mock_k8s_client.validate_connection.return_value = (False, {"message": "Connection failed"})
        mock_k8s_client_class.return_value = mock_k8s_client

        with pytest.raises(ClusterConnectionError):
            cluster_service._validate_cluster_connection(api_address, token)

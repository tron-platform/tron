"""Tests for WorkerService."""
import pytest
from uuid import uuid4, UUID
from unittest.mock import MagicMock, patch
from app.workers.core.worker_service import WorkerService
from app.workers.infra.worker_repository import WorkerRepository
from app.workers.api.worker_dto import WorkerCreate, WorkerUpdate
from app.workers.core.worker_validators import (
    WorkerNotFoundError,
    InstanceNotFoundError
)
from app.workers.infra.application_component_model import WebappType


@pytest.fixture
def mock_repository():
    """Create a mock WorkerRepository."""
    return MagicMock(spec=WorkerRepository)


@pytest.fixture
def mock_db():
    """Create a mock database session."""
    return MagicMock()


@pytest.fixture
def worker_service(mock_repository, mock_db):
    """Create WorkerService instance."""
    return WorkerService(mock_repository, mock_db)


@pytest.fixture
def mock_instance():
    """Create a mock instance."""
    instance = MagicMock()
    instance.id = 1
    instance.uuid = uuid4()
    instance.environment_id = 1
    return instance


@pytest.fixture
def mock_cluster():
    """Create a mock cluster."""
    cluster = MagicMock()
    cluster.id = 1
    cluster.name = "test-cluster"
    return cluster


@pytest.fixture
def mock_worker():
    """Create a mock worker component."""
    from datetime import datetime

    worker = MagicMock()
    worker.uuid = uuid4()
    worker.id = 1
    worker.name = "test-worker"
    worker.type = WebappType.worker
    worker.enabled = True
    worker.settings = {"cpu": 0.5, "memory": 512}
    worker.created_at = datetime.now()
    worker.updated_at = datetime.now()
    worker.instance = MagicMock()
    worker.instance.environment_id = 1
    return worker


def test_create_worker_success(worker_service, mock_repository, mock_db, mock_instance, mock_cluster):
    """Test successful worker creation."""
    from app.workers.api.worker_dto import WorkerSettings, WorkerCustomMetrics, WorkerAutoscaling

    dto = WorkerCreate(
        instance_uuid=mock_instance.uuid,
        name="test-worker",
        enabled=True,
        settings=WorkerSettings(
            cpu=0.5,
            memory=512,
            custom_metrics=WorkerCustomMetrics(enabled=False, path="/metrics", port=9090),
            autoscaling=WorkerAutoscaling(min=2, max=10),
            envs=[],
            command=None
        )
    )

    from datetime import datetime

    mock_worker = MagicMock()
    mock_worker.uuid = uuid4()
    mock_worker.name = dto.name
    mock_worker.type = WebappType.worker
    mock_worker.enabled = dto.enabled
    mock_worker.settings = dto.settings.model_dump()
    mock_worker.created_at = datetime.now()
    mock_worker.updated_at = datetime.now()

    mock_repository.find_instance_by_uuid.return_value = mock_instance
    mock_repository.create.return_value = mock_worker

    mock_cluster_instance = MagicMock()
    mock_cluster_instance.cluster = mock_cluster

    with patch('app.workers.core.worker_service.get_cluster_for_instance', return_value=mock_cluster), \
         patch('app.workers.core.worker_service.ensure_cluster_instance', return_value=mock_cluster_instance), \
         patch.object(worker_service, '_deploy_to_kubernetes') as mock_deploy, \
         patch.object(worker_service, '_build_worker_entity', return_value=mock_worker):

        result = worker_service.create_worker(dto)

        assert result.uuid == mock_worker.uuid
        # Validator also calls find_instance_by_uuid
        assert mock_repository.find_instance_by_uuid.call_count >= 1
        mock_repository.create.assert_called_once()
        mock_deploy.assert_called_once()


def test_create_worker_instance_not_found(worker_service, mock_repository):
    """Test worker creation with non-existent instance."""
    from app.workers.api.worker_dto import WorkerSettings, WorkerCustomMetrics, WorkerAutoscaling

    dto = WorkerCreate(
        instance_uuid=uuid4(),
        name="test-worker",
        enabled=True,
        settings=WorkerSettings(
            cpu=0.5,
            memory=512,
            custom_metrics=WorkerCustomMetrics(enabled=False, path="/metrics", port=9090),
            autoscaling=WorkerAutoscaling(min=2, max=10),
            envs=[],
            command=None
        )
    )

    mock_repository.find_instance_by_uuid.return_value = None

    with pytest.raises(InstanceNotFoundError):
        worker_service.create_worker(dto)


def test_update_worker_success(worker_service, mock_repository, mock_db, mock_worker, mock_cluster):
    """Test successful worker update."""
    from app.workers.api.worker_dto import WorkerSettings, WorkerCustomMetrics, WorkerAutoscaling

    worker_uuid = mock_worker.uuid
    dto = WorkerUpdate(
        enabled=False,
        settings=WorkerSettings(
            cpu=1.0,
            memory=1024,
            custom_metrics=WorkerCustomMetrics(enabled=False, path="/metrics", port=9090),
            autoscaling=WorkerAutoscaling(min=2, max=10),
            envs=[],
            command=None
        )
    )

    mock_repository.find_by_uuid.return_value = mock_worker

    mock_cluster_instance = MagicMock()
    mock_cluster_instance.cluster = mock_cluster

    with patch('app.workers.core.worker_service.get_or_create_cluster_instance', return_value=mock_cluster_instance), \
         patch.object(worker_service, '_update_worker_fields', return_value={'changed': True, 'was_enabled': True, 'will_be_enabled': False}), \
         patch.object(worker_service, '_delete_from_kubernetes_safe') as mock_delete:

        result = worker_service.update_worker(worker_uuid, dto)

        assert result is not None
        mock_repository.find_by_uuid.assert_called()


def test_get_worker_success(worker_service, mock_repository, mock_worker):
    """Test getting worker by UUID."""
    worker_uuid = mock_worker.uuid
    mock_repository.find_by_uuid.return_value = mock_worker

    result = worker_service.get_worker(worker_uuid)

    assert result.uuid == worker_uuid
    mock_repository.find_by_uuid.assert_called()


def test_get_worker_not_found(worker_service, mock_repository):
    """Test getting non-existent worker."""
    worker_uuid = uuid4()
    mock_repository.find_by_uuid.return_value = None

    with pytest.raises(WorkerNotFoundError):
        worker_service.get_worker(worker_uuid)


def test_get_workers(worker_service, mock_repository, mock_worker):
    """Test getting all workers."""
    from datetime import datetime

    mock_worker2 = MagicMock()
    mock_worker2.uuid = uuid4()
    mock_worker2.name = "test-worker-2"
    mock_worker2.type = WebappType.worker
    mock_worker2.enabled = True
    mock_worker2.settings = {}
    mock_worker2.created_at = datetime.now()
    mock_worker2.updated_at = datetime.now()

    mock_repository.find_all.return_value = [mock_worker, mock_worker2]

    result = worker_service.get_workers(skip=0, limit=10)

    assert len(result) == 2
    mock_repository.find_all.assert_called_once_with(skip=0, limit=10)


def test_delete_worker_success(worker_service, mock_repository, mock_db, mock_worker):
    """Test successful worker deletion."""
    worker_uuid = mock_worker.uuid
    mock_repository.find_by_uuid.return_value = mock_worker

    with patch('app.workers.core.worker_service.delete_component', return_value={"detail": "Worker deleted successfully"}):
        result = worker_service.delete_worker(worker_uuid)

        assert result == {"detail": "Worker deleted successfully"}
        mock_repository.find_by_uuid.assert_called()


def test_delete_worker_not_found(worker_service, mock_repository):
    """Test deleting non-existent worker."""
    worker_uuid = uuid4()
    mock_repository.find_by_uuid.return_value = None

    with pytest.raises(WorkerNotFoundError):
        worker_service.delete_worker(worker_uuid)

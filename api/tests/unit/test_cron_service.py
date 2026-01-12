"""Tests for CronService."""
import pytest
from uuid import uuid4, UUID
from unittest.mock import MagicMock, patch
from app.cron.core.cron_service import CronService
from app.cron.infra.cron_repository import CronRepository
from app.cron.api.cron_dto import CronCreate, CronUpdate
from app.cron.core.cron_validators import (
    CronNotFoundError,
    InstanceNotFoundError
)
from app.cron.infra.application_component_model import WebappType


@pytest.fixture
def mock_repository():
    """Create a mock CronRepository."""
    return MagicMock(spec=CronRepository)


@pytest.fixture
def mock_db():
    """Create a mock database session."""
    return MagicMock()


@pytest.fixture
def cron_service(mock_repository, mock_db):
    """Create CronService instance."""
    return CronService(mock_repository, mock_db)


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
def mock_cron():
    """Create a mock cron component."""
    from datetime import datetime

    cron = MagicMock()
    cron.uuid = uuid4()
    cron.id = 1
    cron.name = "test-cron"
    cron.type = WebappType.cron
    cron.enabled = True
    cron.settings = {"cpu": 0.5, "memory": 512, "schedule": "0 0 * * *"}
    cron.created_at = datetime.now()
    cron.updated_at = datetime.now()
    cron.instance = MagicMock()
    cron.instance.environment_id = 1
    return cron


def test_create_cron_success(cron_service, mock_repository, mock_db, mock_instance, mock_cluster):
    """Test successful cron creation."""
    from app.cron.api.cron_dto import CronSettings

    dto = CronCreate(
        instance_uuid=mock_instance.uuid,
        name="test-cron",
        enabled=True,
        settings=CronSettings(
            cpu=0.5,
            memory=512,
            schedule="0 0 * * *",
            envs=[],
            command=None
        )
    )

    from datetime import datetime

    mock_cron = MagicMock()
    mock_cron.uuid = uuid4()
    mock_cron.name = dto.name
    mock_cron.type = WebappType.cron
    mock_cron.enabled = dto.enabled
    mock_cron.settings = dto.settings.model_dump()
    mock_cron.created_at = datetime.now()
    mock_cron.updated_at = datetime.now()

    mock_repository.find_instance_by_uuid.return_value = mock_instance
    mock_repository.create.return_value = mock_cron

    mock_cluster_instance = MagicMock()
    mock_cluster_instance.cluster = mock_cluster

    with patch('app.cron.core.cron_service.get_cluster_for_instance', return_value=mock_cluster), \
         patch('app.cron.core.cron_service.ensure_cluster_instance', return_value=mock_cluster_instance), \
         patch.object(cron_service, '_deploy_to_kubernetes') as mock_deploy, \
         patch.object(cron_service, '_build_cron_entity', return_value=mock_cron):

        result = cron_service.create_cron(dto)

        assert result.uuid == mock_cron.uuid
        # Validator also calls find_instance_by_uuid
        assert mock_repository.find_instance_by_uuid.call_count >= 1
        mock_repository.create.assert_called_once()
        mock_deploy.assert_called_once()


def test_create_cron_instance_not_found(cron_service, mock_repository):
    """Test cron creation with non-existent instance."""
    from app.cron.api.cron_dto import CronSettings

    dto = CronCreate(
        instance_uuid=uuid4(),
        name="test-cron",
        enabled=True,
        settings=CronSettings(
            cpu=0.5,
            memory=512,
            schedule="0 0 * * *",
            envs=[],
            command=None
        )
    )

    mock_repository.find_instance_by_uuid.return_value = None

    with pytest.raises(InstanceNotFoundError):
        cron_service.create_cron(dto)


def test_update_cron_success(cron_service, mock_repository, mock_db, mock_cron, mock_cluster):
    """Test successful cron update."""
    from app.cron.api.cron_dto import CronSettings

    cron_uuid = mock_cron.uuid
    dto = CronUpdate(
        enabled=False,
        settings=CronSettings(
            cpu=1.0,
            memory=1024,
            schedule="0 1 * * *",
            envs=[],
            command=None
        )
    )

    mock_repository.find_by_uuid.return_value = mock_cron

    mock_cluster_instance = MagicMock()
    mock_cluster_instance.cluster = mock_cluster

    with patch('app.cron.core.cron_service.get_or_create_cluster_instance', return_value=mock_cluster_instance), \
         patch.object(cron_service, '_update_cron_fields', return_value={'changed': True, 'was_enabled': True, 'will_be_enabled': False}), \
         patch.object(cron_service, '_delete_from_kubernetes_safe') as mock_delete:

        result = cron_service.update_cron(cron_uuid, dto)

        assert result is not None
        mock_repository.find_by_uuid.assert_called()


def test_get_cron_success(cron_service, mock_repository, mock_cron):
    """Test getting cron by UUID."""
    cron_uuid = mock_cron.uuid
    mock_repository.find_by_uuid.return_value = mock_cron

    result = cron_service.get_cron(cron_uuid)

    assert result.uuid == cron_uuid
    mock_repository.find_by_uuid.assert_called()


def test_get_cron_not_found(cron_service, mock_repository):
    """Test getting non-existent cron."""
    cron_uuid = uuid4()
    mock_repository.find_by_uuid.return_value = None

    with pytest.raises(CronNotFoundError):
        cron_service.get_cron(cron_uuid)


def test_get_crons(cron_service, mock_repository, mock_cron):
    """Test getting all crons."""
    from datetime import datetime

    mock_cron2 = MagicMock()
    mock_cron2.uuid = uuid4()
    mock_cron2.name = "test-cron-2"
    mock_cron2.type = WebappType.cron
    mock_cron2.enabled = True
    mock_cron2.settings = {}
    mock_cron2.created_at = datetime.now()
    mock_cron2.updated_at = datetime.now()

    mock_repository.find_all.return_value = [mock_cron, mock_cron2]

    result = cron_service.get_crons(skip=0, limit=10)

    assert len(result) == 2
    mock_repository.find_all.assert_called_once_with(skip=0, limit=10)


def test_delete_cron_success(cron_service, mock_repository, mock_db, mock_cron):
    """Test successful cron deletion."""
    cron_uuid = mock_cron.uuid
    mock_repository.find_by_uuid.return_value = mock_cron

    with patch('app.cron.core.cron_service.delete_component', return_value={"detail": "Cron deleted successfully"}):
        result = cron_service.delete_cron(cron_uuid)

        assert result == {"detail": "Cron deleted successfully"}
        mock_repository.find_by_uuid.assert_called()


def test_delete_cron_not_found(cron_service, mock_repository):
    """Test deleting non-existent cron."""
    cron_uuid = uuid4()
    mock_repository.find_by_uuid.return_value = None

    with pytest.raises(CronNotFoundError):
        cron_service.delete_cron(cron_uuid)

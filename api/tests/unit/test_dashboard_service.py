"""Tests for DashboardService."""
import pytest
from unittest.mock import MagicMock
from app.dashboard.core.dashboard_service import DashboardService
from app.dashboard.infra.dashboard_repository import DashboardRepository


@pytest.fixture
def mock_repository():
    """Create a mock DashboardRepository."""
    return MagicMock(spec=DashboardRepository)


@pytest.fixture
def dashboard_service(mock_repository):
    """Create DashboardService instance."""
    return DashboardService(mock_repository)


def test_get_dashboard_overview_success(dashboard_service, mock_repository):
    """Test successful dashboard overview retrieval."""
    # Mock repository methods
    mock_repository.count_applications.return_value = 5
    mock_repository.count_instances.return_value = 10
    mock_repository.count_total_components.return_value = 20
    mock_repository.count_components_by_type.side_effect = lambda t: {
        "webapp": 8,
        "worker": 7,
        "cron": 5
    }.get(t, 0)
    mock_repository.count_enabled_components.return_value = 15
    mock_repository.count_disabled_components.return_value = 5
    mock_repository.count_clusters.return_value = 3
    mock_repository.count_environments.return_value = 2
    mock_repository.get_components_by_environment.return_value = [
        ("prod", 12),
        ("dev", 8)
    ]
    mock_repository.get_components_by_cluster.return_value = [
        ("cluster-1", 10),
        ("cluster-2", 10)
    ]

    result = dashboard_service.get_dashboard_overview()

    assert result.applications == 5
    assert result.instances == 10
    assert result.components.total == 20
    assert result.components.webapp == 8
    assert result.components.worker == 7
    assert result.components.cron == 5
    assert result.components.enabled == 15
    assert result.components.disabled == 5
    assert result.clusters == 3
    assert result.environments == 2
    assert result.components_by_environment == {"prod": 12, "dev": 8}
    assert result.components_by_cluster == {"cluster-1": 10, "cluster-2": 10}

    # Verify all repository methods were called
    mock_repository.count_applications.assert_called_once()
    mock_repository.count_instances.assert_called_once()
    mock_repository.count_total_components.assert_called_once()
    assert mock_repository.count_components_by_type.call_count == 3
    mock_repository.count_enabled_components.assert_called_once()
    mock_repository.count_disabled_components.assert_called_once()
    mock_repository.count_clusters.assert_called_once()
    mock_repository.count_environments.assert_called_once()
    mock_repository.get_components_by_environment.assert_called_once()
    mock_repository.get_components_by_cluster.assert_called_once()


def test_get_dashboard_overview_empty(dashboard_service, mock_repository):
    """Test dashboard overview with no data."""
    # Mock repository methods to return zeros/empty
    mock_repository.count_applications.return_value = 0
    mock_repository.count_instances.return_value = 0
    mock_repository.count_total_components.return_value = 0
    mock_repository.count_components_by_type.return_value = 0
    mock_repository.count_enabled_components.return_value = 0
    mock_repository.count_disabled_components.return_value = 0
    mock_repository.count_clusters.return_value = 0
    mock_repository.count_environments.return_value = 0
    mock_repository.get_components_by_environment.return_value = []
    mock_repository.get_components_by_cluster.return_value = []

    result = dashboard_service.get_dashboard_overview()

    assert result.applications == 0
    assert result.instances == 0
    assert result.components.total == 0
    assert result.components.webapp == 0
    assert result.components.worker == 0
    assert result.components.cron == 0
    assert result.components.enabled == 0
    assert result.components.disabled == 0
    assert result.clusters == 0
    assert result.environments == 0
    assert result.components_by_environment == {}
    assert result.components_by_cluster == {}

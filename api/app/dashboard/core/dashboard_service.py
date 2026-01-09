from app.dashboard.infra.dashboard_repository import DashboardRepository
from app.dashboard.api.dashboard_dto import DashboardOverview, ComponentStats


class DashboardService:
    """Business logic for dashboard. No direct database access."""

    def __init__(self, repository: DashboardRepository):
        self.repository = repository

    def get_dashboard_overview(self) -> DashboardOverview:
        """Get dashboard overview with statistics."""
        applications_count = self.repository.count_applications()
        instances_count = self.repository.count_instances()

        total_components = self.repository.count_total_components()
        webapp_count = self.repository.count_components_by_type("webapp")
        worker_count = self.repository.count_components_by_type("worker")
        cron_count = self.repository.count_components_by_type("cron")
        enabled_components = self.repository.count_enabled_components()
        disabled_components = self.repository.count_disabled_components()

        clusters_count = self.repository.count_clusters()
        environments_count = self.repository.count_environments()

        components_by_environment = {}
        environment_components = self.repository.get_components_by_environment()
        for env_name, count in environment_components:
            components_by_environment[env_name] = count

        components_by_cluster = {}
        cluster_components = self.repository.get_components_by_cluster()
        for cluster_name, count in cluster_components:
            components_by_cluster[cluster_name] = count

        return DashboardOverview(
            applications=applications_count,
            instances=instances_count,
            components=ComponentStats(
                total=total_components,
                webapp=webapp_count,
                worker=worker_count,
                cron=cron_count,
                enabled=enabled_components,
                disabled=disabled_components,
            ),
            clusters=clusters_count,
            environments=environments_count,
            components_by_environment=components_by_environment,
            components_by_cluster=components_by_cluster,
        )

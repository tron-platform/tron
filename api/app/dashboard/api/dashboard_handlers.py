from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.shared.database.database import get_db
from app.dashboard.infra.dashboard_repository import DashboardRepository
from app.dashboard.core.dashboard_service import DashboardService
from app.dashboard.api.dashboard_dto import DashboardOverview
from app.users.infra.user_model import User
from app.shared.dependencies.auth import get_current_user


router = APIRouter(prefix="/dashboard", tags=["dashboard"])


def get_dashboard_service(database_session: Session = Depends(get_db)) -> DashboardService:
    """Dependency to get DashboardService instance."""
    dashboard_repository = DashboardRepository(database_session)
    return DashboardService(dashboard_repository)


@router.get("/", response_model=DashboardOverview)
def get_dashboard_overview(
    service: DashboardService = Depends(get_dashboard_service),
    current_user: User = Depends(get_current_user)
):
    """
    Get dashboard overview with statistics about applications, instances, components, clusters, and environments.
    """
    return service.get_dashboard_overview()

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from uuid import UUID

from app.shared.database.database import get_db
from app.settings.infra.settings_repository import SettingsRepository
from app.settings.core.settings_service import SettingsService
from app.settings.api.settings_dto import (
    SettingsCreate,
    SettingsUpdate,
    Settings,
    SettingsWithEnvironment
)
from app.settings.core.settings_validators import (
    SettingsNotFoundError,
    EnvironmentNotFoundError,
    SettingsKeyAlreadyExistsError
)
from app.users.infra.user_model import UserRole, User
from app.shared.dependencies.auth import require_role, get_current_user


router = APIRouter()


def get_settings_service(database_session: Session = Depends(get_db)) -> SettingsService:
    """Dependency to get SettingsService instance."""
    settings_repository = SettingsRepository(database_session)
    return SettingsService(settings_repository)


@router.post("/settings", response_model=Settings)
def create_settings(
    setting: SettingsCreate,
    service: SettingsService = Depends(get_settings_service),
    current_user: User = Depends(require_role([UserRole.ADMIN]))
):
    """Create a new settings."""
    try:
        return service.create_settings(setting)
    except (EnvironmentNotFoundError, SettingsKeyAlreadyExistsError) as e:
        raise HTTPException(status_code=400, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/settings/{uuid}", response_model=Settings)
def update_settings(
    uuid: UUID,
    setting: SettingsUpdate,
    service: SettingsService = Depends(get_settings_service),
    current_user: User = Depends(require_role([UserRole.ADMIN]))
):
    """Update an existing settings."""
    try:
        return service.update_settings(uuid, setting)
    except SettingsNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except (SettingsKeyAlreadyExistsError, ValueError) as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/settings/", response_model=list[SettingsWithEnvironment])
def list_settings(
    skip: int = 0,
    limit: int = 100,
    service: SettingsService = Depends(get_settings_service),
    current_user: User = Depends(get_current_user)
):
    """List all settings."""
    return service.get_settings_list(skip=skip, limit=limit)


@router.get("/settings/{uuid}", response_model=SettingsWithEnvironment)
def get_settings(
    uuid: UUID,
    service: SettingsService = Depends(get_settings_service),
    current_user: User = Depends(get_current_user)
):
    """Get settings by UUID."""
    try:
        return service.get_settings(uuid)
    except SettingsNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/settings/{uuid}", response_model=dict)
def delete_settings(
    uuid: UUID,
    service: SettingsService = Depends(get_settings_service),
    current_user: User = Depends(require_role([UserRole.ADMIN]))
):
    """Delete a settings."""
    try:
        return service.delete_settings(uuid)
    except SettingsNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

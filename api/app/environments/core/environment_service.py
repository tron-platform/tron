from uuid import uuid4, UUID
from typing import List
from app.environments.infra.environment_repository import EnvironmentRepository
from app.environments.infra.environment_model import Environment as EnvironmentModel
from app.environments.api.environment_dto import EnvironmentCreate, Environment, EnvironmentWithClusters
from app.environments.core.environment_validators import (
    validate_environment_create_dto,
    validate_environment_exists,
    validate_environment_can_be_deleted,
    EnvironmentNotFoundError,
    EnvironmentHasComponentsError
)


class EnvironmentService:
    """Business logic for environments. No direct database access."""

    def __init__(self, repository: EnvironmentRepository):
        self.repository = repository

    def create_environment(self, dto: EnvironmentCreate) -> Environment:
        """Create a new environment."""
        validate_environment_create_dto(dto)

        environment = self._build_environment_entity(dto)
        return self.repository.create(environment)

    def update_environment(self, uuid: UUID, dto: EnvironmentCreate) -> Environment:
        """Update an existing environment."""
        validate_environment_create_dto(dto)
        validate_environment_exists(self.repository, uuid)

        environment = self.repository.find_by_uuid(uuid)
        environment.name = dto.name

        return self.repository.update(environment)

    def get_environment(self, uuid: UUID) -> EnvironmentWithClusters:
        """Get environment by UUID with clusters and settings."""
        validate_environment_exists(self.repository, uuid)

        environment = self.repository.find_by_uuid(uuid)
        return self._serialize_environment_with_clusters(environment)

    def get_environments(self, skip: int = 0, limit: int = 100) -> List[EnvironmentWithClusters]:
        """Get all environments with clusters and settings."""
        environments = self.repository.find_all(skip=skip, limit=limit)
        return [self._serialize_environment_with_clusters(env) for env in environments]

    def delete_environment(self, uuid: UUID) -> dict:
        """Delete an environment."""
        validate_environment_can_be_deleted(self.repository, uuid)

        environment = self.repository.find_by_uuid(uuid)
        self.repository.delete(environment)

        return {"detail": "Environment deleted successfully"}

    def _build_environment_entity(self, dto: EnvironmentCreate) -> EnvironmentModel:
        """Build Environment entity from DTO."""
        return EnvironmentModel(
            uuid=uuid4(),
            name=dto.name
        )

    def _serialize_environment_with_clusters(self, environment: EnvironmentModel) -> EnvironmentWithClusters:
        """Serialize environment with clusters and settings."""
        return EnvironmentWithClusters(
            uuid=environment.uuid,
            name=environment.name,
            clusters=[cluster.name for cluster in environment.clusters],
            settings=[
                {
                    "key": setting.key,
                    "value": setting.value,
                    "description": setting.description
                }
                for setting in environment.settings
            ],
            created_at=environment.created_at.isoformat(),
            updated_at=environment.updated_at.isoformat()
        )

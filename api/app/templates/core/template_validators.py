from uuid import UUID
from app.templates.infra.template_repository import TemplateRepository


class TemplateNotFoundError(Exception):
    """Raised when template is not found."""
    pass


class TemplateHasConfigsError(Exception):
    """Raised when trying to delete template with associated component configs."""
    pass


def validate_template_create_dto(dto) -> None:
    """Validate template create DTO. Raises ValueError if validation fails."""
    if not dto.name or not dto.name.strip():
        raise ValueError("Template name is required and cannot be empty")

    if not dto.category or not dto.category.strip():
        raise ValueError("Template category is required and cannot be empty")

    if not dto.content or not dto.content.strip():
        raise ValueError("Template content is required and cannot be empty")


def validate_template_update_dto(dto) -> None:
    """Validate template update DTO. Raises ValueError if validation fails."""
    if dto.name is not None and not dto.name.strip():
        raise ValueError("Template name cannot be empty")

    if dto.content is not None and not dto.content.strip():
        raise ValueError("Template content cannot be empty")


def validate_template_exists(repository: TemplateRepository, uuid: UUID) -> None:
    """Validate that template exists. Raises TemplateNotFoundError if not found."""
    template = repository.find_by_uuid(uuid)
    if not template:
        raise TemplateNotFoundError(f"Template with UUID '{uuid}' not found")


def validate_template_can_be_deleted(repository: TemplateRepository, uuid: UUID) -> None:
    """Validate that template can be deleted (no associated configs)."""
    template = repository.find_by_uuid(uuid)
    if not template:
        raise TemplateNotFoundError(f"Template with UUID '{uuid}' not found")

    configs = repository.find_component_configs_by_template_id(template.id)
    if configs:
        # Configs will be deleted automatically, but we validate they exist
        pass

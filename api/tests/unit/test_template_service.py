"""Tests for TemplateService."""
import pytest
from uuid import uuid4, UUID
from unittest.mock import MagicMock, patch
from app.templates.core.template_service import TemplateService
from app.templates.infra.template_repository import TemplateRepository
from app.templates.api.template_dto import TemplateCreate, TemplateUpdate
from app.templates.core.template_validators import (
    TemplateNotFoundError
)


@pytest.fixture
def mock_repository():
    """Create a mock TemplateRepository."""
    return MagicMock(spec=TemplateRepository)


@pytest.fixture
def template_service(mock_repository):
    """Create TemplateService instance."""
    return TemplateService(mock_repository)


@pytest.fixture
def mock_template():
    """Create a mock template."""
    template = MagicMock()
    template.uuid = uuid4()
    template.id = 1
    template.name = "test-template"
    template.description = "Test description"
    template.category = "webapp"
    template.content = "template content"
    template.variables_schema = '{"type": "object"}'
    return template


def test_create_template_success(template_service, mock_repository, mock_template):
    """Test successful template creation."""
    dto = TemplateCreate(
        name="test-template",
        description="Test description",
        category="webapp",
        content="template content",
        variables_schema='{"type": "object"}'
    )

    mock_repository.create.return_value = mock_template

    with patch.object(template_service, '_build_template_entity', return_value=mock_template):
        result = template_service.create_template(dto)

        assert result == mock_template
        mock_repository.create.assert_called_once()


def test_update_template_success(template_service, mock_repository, mock_template):
    """Test successful template update."""
    template_uuid = mock_template.uuid
    dto = TemplateUpdate(
        name="updated-template",
        description="Updated description",
        content="updated content"
    )

    updated_template = MagicMock()
    updated_template.uuid = template_uuid
    updated_template.name = dto.name

    mock_repository.find_by_uuid.return_value = mock_template
    mock_repository.update.return_value = updated_template

    result = template_service.update_template(template_uuid, dto)

    assert result == updated_template
    assert mock_template.name == dto.name
    assert mock_template.description == dto.description
    assert mock_template.content == dto.content
    mock_repository.update.assert_called_once()


def test_update_template_partial(template_service, mock_repository, mock_template):
    """Test partial template update."""
    template_uuid = mock_template.uuid
    dto = TemplateUpdate(name="updated-name")  # Only update name

    updated_template = MagicMock()
    updated_template.uuid = template_uuid

    mock_repository.find_by_uuid.return_value = mock_template
    mock_repository.update.return_value = updated_template

    result = template_service.update_template(template_uuid, dto)

    assert result == updated_template
    assert mock_template.name == dto.name
    mock_repository.update.assert_called_once()


def test_update_template_not_found(template_service, mock_repository):
    """Test updating non-existent template."""
    template_uuid = uuid4()
    dto = TemplateUpdate(name="updated-template")

    mock_repository.find_by_uuid.return_value = None

    with pytest.raises(TemplateNotFoundError):
        template_service.update_template(template_uuid, dto)


def test_get_template_success(template_service, mock_repository, mock_template):
    """Test getting template by UUID."""
    template_uuid = mock_template.uuid
    mock_repository.find_by_uuid.return_value = mock_template

    result = template_service.get_template(template_uuid)

    assert result == mock_template
    # Validator also calls find_by_uuid
    assert mock_repository.find_by_uuid.call_count >= 1


def test_get_template_not_found(template_service, mock_repository):
    """Test getting non-existent template."""
    template_uuid = uuid4()
    mock_repository.find_by_uuid.return_value = None

    with pytest.raises(TemplateNotFoundError):
        template_service.get_template(template_uuid)


def test_get_templates(template_service, mock_repository, mock_template):
    """Test getting all templates."""
    mock_template2 = MagicMock()
    mock_template2.uuid = uuid4()
    mock_template2.name = "test-template-2"

    mock_repository.find_all.return_value = [mock_template, mock_template2]

    result = template_service.get_templates(skip=0, limit=10)

    assert len(result) == 2
    mock_repository.find_all.assert_called_once_with(skip=0, limit=10, category=None)


def test_get_templates_with_category(template_service, mock_repository, mock_template):
    """Test getting templates filtered by category."""
    mock_repository.find_all.return_value = [mock_template]

    result = template_service.get_templates(skip=0, limit=10, category="webapp")

    assert len(result) == 1
    mock_repository.find_all.assert_called_once_with(skip=0, limit=10, category="webapp")


def test_delete_template_success(template_service, mock_repository, mock_template):
    """Test successful template deletion."""
    template_uuid = mock_template.uuid
    mock_repository.find_by_uuid.return_value = mock_template
    mock_repository.find_component_configs_by_template_id.return_value = []

    with patch('app.templates.core.template_service.validate_template_can_be_deleted'):
        result = template_service.delete_template(template_uuid)

        assert result == {"status": "success", "message": "Template deleted successfully"}
        # Validator also calls find_by_uuid
        assert mock_repository.find_by_uuid.call_count >= 1
        mock_repository.delete.assert_called_once_with(mock_template)


def test_delete_template_with_configs(template_service, mock_repository, mock_template):
    """Test template deletion with associated configs."""
    template_uuid = mock_template.uuid
    mock_config1 = MagicMock()
    mock_config2 = MagicMock()

    mock_repository.find_by_uuid.return_value = mock_template
    mock_repository.find_component_configs_by_template_id.return_value = [mock_config1, mock_config2]

    with patch('app.templates.core.template_service.validate_template_can_be_deleted'):
        result = template_service.delete_template(template_uuid)

        assert result == {"status": "success", "message": "Template deleted successfully"}
        mock_repository.delete_component_configs.assert_called_once_with([mock_config1, mock_config2])
        mock_repository.delete.assert_called_once_with(mock_template)


def test_delete_template_not_found(template_service, mock_repository):
    """Test deleting non-existent template."""
    template_uuid = uuid4()
    mock_repository.find_by_uuid.return_value = None

    with pytest.raises(TemplateNotFoundError):
        template_service.delete_template(template_uuid)

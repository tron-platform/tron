"""Validators for component template config business rules."""


class ComponentTemplateConfigNotFoundError(Exception):
    """Raised when component template config is not found."""
    pass


class ComponentTemplateConfigAlreadyExistsError(Exception):
    """Raised when component template config already exists."""
    pass


class TemplateNotFoundError(Exception):
    """Raised when template is not found."""
    pass

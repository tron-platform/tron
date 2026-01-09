import yaml
from typing import Optional
from jinja2 import Environment, BaseLoader
from sqlalchemy.orm import Session

from app.templates.infra.component_template_config_repository import ComponentTemplateConfigRepository
from app.templates.infra.template_repository import TemplateRepository
from app.templates.core.component_template_config_service import ComponentTemplateConfigService


class KubernetesApplicationComponentManager:
    """
    Gerencia a renderização de templates Kubernetes para componentes de aplicação.
    Utiliza a configuração de templates (component_template_config) para determinar
    quais templates devem ser renderizados e em que ordem.
    """

    @staticmethod
    def instance_management(
        application_component: dict,
        component_type: str,
        settings: Optional[dict] = None,
        db: Optional[Session] = None,
        gateway_reference: Optional[dict] = None
    ):
        """
        Renderiza templates Kubernetes para um componente de aplicação.

        Args:
            application_component: Dict com informações do componente (name, uuid, settings, etc.)
            component_type: Tipo do componente (webapp, worker, cron)
            settings: Dict opcional com configurações do ambiente
            db: Sessão do banco de dados (obrigatória)
            gateway_reference: Dict opcional com informações do gateway (namespace, name)

        Returns:
            Lista de dicionários YAML renderizados, ordenados por render_order

        Raises:
            ValueError: Se não houver templates configurados ou erro na renderização
        """
        if db is None:
            raise ValueError("Database session is required")

        if settings is None:
            settings = {}

        # Valores padrão para gateway_reference se não fornecido
        if gateway_reference is None:
            gateway_reference = {
                "namespace": "",
                "name": ""
            }

        # Preparar variáveis para os templates
        variables = {
            "application": application_component,
            "environment": settings,
            "cluster": {
                "gateway": {
                    "reference": gateway_reference
                }
            }
        }

        # Buscar templates configurados para o tipo de componente
        # Os templates já vêm ordenados por render_order
        config_repository = ComponentTemplateConfigRepository(db)
        template_repository = TemplateRepository(db)
        service = ComponentTemplateConfigService(config_repository, template_repository)
        templates = service.get_templates_for_component_type(component_type)

        if not templates:
            raise ValueError(
                f"No templates configured for component type '{component_type}'. "
                "Please configure templates in the Component Template Config section."
            )

        combined_payloads = []

        # Renderizar cada template na ordem configurada
        for template in templates:
            try:
                rendered_yaml = KubernetesApplicationComponentManager.render_template_from_string(
                    template.content, variables
                )
                # Filtrar documentos None (quando template não renderiza nada devido a condições)
                if rendered_yaml is not None:
                    combined_payloads.append(rendered_yaml)
            except Exception as e:
                raise ValueError(
                    f"Error rendering template '{template.name}': {e}"
                )

        return combined_payloads

    @staticmethod
    def render_template_from_string(template_content: str, variables: dict):
        """
        Renderiza um template Jinja2 a partir de uma string.

        Args:
            template_content: Conteúdo do template Jinja2
            variables: Dicionário com variáveis para renderização

        Returns:
            Dicionário Python representando o YAML renderizado

        Raises:
            FileNotFoundError: Se houver erro na criação do template
            ValueError: Se houver erro no parsing do YAML
        """
        env = Environment(loader=BaseLoader())

        try:
            template = env.from_string(template_content)
        except Exception as e:
            raise FileNotFoundError(f"Template rendering error: {e}")

        rendered_yaml = template.render(variables)

        # Se o template renderizou uma string vazia ou apenas espaços em branco, retornar None
        if not rendered_yaml or not rendered_yaml.strip():
            return None

        try:
            # Usar safe_load para um único documento YAML
            parsed_yaml = yaml.safe_load(rendered_yaml)
            return parsed_yaml
        except yaml.YAMLError as e:
            # Debug: log erro de parsing para httproute
            if 'httproute' in template_content.lower():
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"HTTPRoute YAML parsing error: {e}. Rendered content:\n{rendered_yaml[:500]}")
            raise ValueError(f"Error parsing YAML template: {e}")

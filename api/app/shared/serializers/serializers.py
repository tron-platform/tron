
def serialize_application_component(application_component):
    """
    Serializa um ApplicationComponent para uso nos templates Kubernetes.
    Inclui informações do componente, instância, aplicação e ambiente.
    """
    # Fazer uma cópia do settings para não modificar o original
    import copy
    settings = copy.deepcopy(application_component.settings) if application_component.settings else {}

    # Garantir que command seja sempre uma lista quando não for None
    # Isso é necessário porque o schema pode retornar string, lista ou None
    # mas os templates esperam lista ou None
    if settings and 'command' in settings:
        command = settings.get('command')
        if command is not None:
            # Se já for uma lista, manter como está
            if isinstance(command, list):
                pass  # Já é lista
            # Se for string, converter para lista (já foi processado pelo schema, mas garantir)
            elif isinstance(command, str):
                import shlex
                command_str = command.strip()
                if command_str:
                    settings['command'] = shlex.split(command_str)
                else:
                    settings['command'] = None
            # Se for None, manter None
        else:
            settings['command'] = None

    # Garantir que todos os campos do settings sejam preservados
    # Isso é importante para campos como schedule, cpu, memory, envs, etc.
    # O deepcopy já faz isso, mas garantimos explicitamente
    if not settings:
        settings = {}

    # Garantir que webapps sempre tenham exposure definido
    component_type = application_component.type.value if hasattr(application_component.type, 'value') else str(application_component.type)
    if component_type == 'webapp' and 'exposure' not in settings:
        settings['exposure'] = {
            'type': 'http',
            'port': 80,
            'visibility': 'cluster'
        }
    elif component_type == 'webapp' and settings.get('exposure') is None:
        settings['exposure'] = {
            'type': 'http',
            'port': 80,
            'visibility': 'cluster'
        }

    # Converter Enums para strings nos settings (especialmente exposure.visibility)
    if settings and 'exposure' in settings and isinstance(settings.get('exposure'), dict):
        exposure = settings['exposure']
        if 'visibility' in exposure:
            # Se visibility for um Enum, converter para string
            visibility_value = exposure['visibility']
            if hasattr(visibility_value, 'value'):
                exposure['visibility'] = visibility_value.value
            elif not isinstance(visibility_value, str):
                exposure['visibility'] = str(visibility_value)

    return {
        "component_name": application_component.name,
        "component_uuid": str(application_component.uuid),
        "component_type": application_component.type.value if hasattr(application_component.type, 'value') else str(application_component.type),
        "application_name": application_component.instance.application.name,
        "application_uuid": str(application_component.instance.application.uuid),
        "environment": application_component.instance.environment.name,
        "environment_uuid": str(application_component.instance.environment.uuid),
        "image": application_component.instance.image,
        "version": application_component.instance.version,
        "url": application_component.url,
        "enabled": application_component.enabled,
        "settings": settings
    }

# Mantido para compatibilidade (deprecated)
def serialize_webapp_deploy(webapp_deploy):
    return serialize_application_component(webapp_deploy)

def serialize_settings(settings):

    serialized_settings = {}

    for item in settings:
        serialized_settings.update({
            item.key: item.value
        })

    return serialized_settings

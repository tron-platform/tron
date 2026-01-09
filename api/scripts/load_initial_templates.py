#!/usr/bin/env python3
"""
Script para carregar templates iniciais e configurações de component_template_config.
Este script deve ser executado após as migrations para popular o banco com dados iniciais.
"""

import os
import sys
from pathlib import Path

# Adicionar o diretório raiz ao path para importar os módulos
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.orm import Session
from app.shared.database.database import SessionLocal
from uuid import uuid4

from app.templates.infra.template_model import Template as TemplateModel
from app.templates.infra.component_template_config_model import ComponentTemplateConfig as ComponentTemplateConfigModel


def read_template_file(file_path: Path) -> str:
    """Lê o conteúdo de um arquivo de template."""
    with open(file_path, 'r', encoding='utf-8') as f:
        return f.read()


def get_variables_schema() -> str:
    """Retorna o schema JSON das variáveis disponíveis para os templates."""
    return """{
  "application": {
    "component_name": "string",
    "application_name": "string",
    "environment": "string",
    "image": "string",
    "version": "string",
    "workload": "string",
    "settings": {
      "cpu": "number",
      "memory": "number",
      "cpu_scaling_threshold": "number",
      "memory_scaling_threshold": "number",
      "autoscaling": {
        "min": "number",
        "max": "number"
      },
      "custom_metrics": {
        "enabled": "boolean",
        "port": "number",
        "path": "string"
      },
      "exposure": {
        "type": "string",
        "port": "number",
        "visibility": "string"
      },
      "envs": [
        {
          "key": "string",
          "value": "string"
        }
      ],
      "secrets": [
        {
          "key": "string",
          "value": "string"
        }
      ],
      "healthcheck": {
        "protocol": "string",
        "path": "string",
        "port": "number",
        "failure_threshold": "number",
        "initial_interval": "number",
        "interval": "number",
        "timeout": "number"
      },
      "schedule": "string",
      "command": "array"
    }
  },
  "environment": {
    "disable_workload": "boolean"
  }
}"""


def load_templates(db: Session):
    """Carrega os templates iniciais na tabela templates."""
    templates_base_dir = Path(__file__).parent.parent / "app" / "k8s" / "templates"
    webapp_dir = templates_base_dir / "webapp"
    cron_dir = templates_base_dir / "cron"
    worker_dir = templates_base_dir / "worker"

    templates_data = [
        # Templates Webapp
        {
            "name": "Webapp Deployment",
            "description": "Deployment template for webapp components",
            "category": "webapp",
            "file_path": webapp_dir / "deployment.yaml.j2",
            "render_order": 1,
        },
        {
            "name": "Webapp Service",
            "description": "Service template for webapp components",
            "category": "webapp",
            "file_path": webapp_dir / "service.yaml.j2",
            "render_order": 2,
        },
        {
            "name": "Webapp HPA",
            "description": "HorizontalPodAutoscaler template for webapp components",
            "category": "webapp",
            "file_path": webapp_dir / "hpa.yaml.j2",
            "render_order": 3,
        },
        {
            "name": "Webapp HTTPRoute",
            "description": "HTTPRoute template for webapp components",
            "category": "webapp",
            "file_path": webapp_dir / "httproute.yaml.j2",
            "render_order": 4,
        },
        {
            "name": "Webapp TCPRoute",
            "description": "TCPRoute template for webapp components",
            "category": "webapp",
            "file_path": webapp_dir / "tcproute.yaml.j2",
            "render_order": 5,
        },
        {
            "name": "Webapp UDPRoute",
            "description": "UDPRoute template for webapp components",
            "category": "webapp",
            "file_path": webapp_dir / "udproute.yaml.j2",
            "render_order": 6,
        },
        # Templates Cron
        {
            "name": "Cron CronJob",
            "description": "CronJob template for cron components",
            "category": "cron",
            "file_path": cron_dir / "cron.yaml.j2",
            "render_order": 1,
        },

        {
            "name": "Worker Deployment",
            "description": "Deployment template for worker components",
            "category": "worker",
            "file_path": worker_dir / "deployment.yaml.j2",
            "render_order": 1,
        },
        {
            "name": "Worker HPA",
            "description": "HorizontalPodAutoscaler template for worker components",
            "category": "worker",
            "file_path": worker_dir / "hpa.yaml.j2",
            "render_order": 2,
        },
    ]

    created_templates = []

    for template_data in templates_data:
        # Verificar se o template já existe (por nome e categoria)
        existing_template = (
            db.query(TemplateModel)
            .filter(
                TemplateModel.name == template_data["name"],
                TemplateModel.category == template_data["category"]
            )
            .first()
        )

        if existing_template:
            print(f"Template '{template_data['name']}' já existe, verificando configuração...")
            # Verificar se já existe component_template_config para este template
            # A constraint única é por component_type e template_id
            existing_config = (
                db.query(ComponentTemplateConfigModel)
                .filter(
                    ComponentTemplateConfigModel.template_id == existing_template.id,
                    ComponentTemplateConfigModel.component_type == template_data["category"]
                )
                .first()
            )

            if not existing_config:
                # Criar a configuração se não existir
                try:
                    config = ComponentTemplateConfigModel(
                        uuid=uuid4(),
                        component_type=template_data["category"],
                        template_id=existing_template.id,
                        render_order=template_data["render_order"],
                        enabled="true",
                    )
                    db.add(config)
                    db.flush()
                    print(f"  ✓ Configuração criada para template '{template_data['name']}'")
                except Exception as e:
                    print(f"  ⚠ Erro ao criar configuração: {e}")
            else:
                # Atualizar render_order se necessário
                if existing_config.render_order != template_data["render_order"]:
                    existing_config.render_order = template_data["render_order"]
                    print(f"  ✓ Render order atualizado para template '{template_data['name']}'")
                else:
                    print(f"  ✓ Configuração já existe para template '{template_data['name']}'")

            created_templates.append(existing_template)
            continue

        # Ler o conteúdo do arquivo
        if not template_data["file_path"].exists():
            print(f"AVISO: Arquivo não encontrado: {template_data['file_path']}")
            continue

        content = read_template_file(template_data["file_path"])

        # Criar o template
        new_template = TemplateModel(
            uuid=uuid4(),
            name=template_data["name"],
            description=template_data["description"],
            category=template_data["category"],
            content=content,
            variables_schema=get_variables_schema(),
        )

        db.add(new_template)
        db.flush()  # Flush para obter o ID

        # Criar a configuração de component_template_config
        config = ComponentTemplateConfigModel(
            uuid=uuid4(),
            component_type=template_data["category"],
            template_id=new_template.id,
            render_order=template_data["render_order"],
            enabled="true",
        )

        db.add(config)
        created_templates.append(new_template)
        print(f"✓ Template '{template_data['name']}' criado com sucesso")

    db.commit()
    return created_templates


def main():
    """Função principal."""
    print("🚀 Carregando templates iniciais...")

    db: Session = SessionLocal()
    try:
        templates = load_templates(db)
        print(f"\n✅ {len(templates)} template(s) processado(s) com sucesso!")
    except Exception as e:
        db.rollback()
        print(f"\n❌ Erro ao carregar templates: {e}")
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    main()


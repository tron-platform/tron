#!/usr/bin/env python3
"""
Script para resetar o histórico do Alembic e marcar a migration inicial como aplicada.
Este script deve ser executado após deletar as migrations antigas e criar uma nova migration inicial.
"""

import os
import sys
from pathlib import Path

# Adicionar o diretório raiz ao path para importar os módulos
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import create_engine, text
from app.database import SessionLocal
import os

def reset_alembic_history():
    """Reseta o histórico do Alembic no banco de dados."""
    # Obter URL do banco de dados das variáveis de ambiente
    DB_HOST = os.getenv('DB_HOST', 'localhost')
    DB_USER = os.getenv('DB_USER', 'tron')
    DB_PASSWORD = os.getenv('DB_PASSWORD', 'tron')
    DB_NAME = os.getenv('DB_NAME', 'api')
    DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}"

    engine = create_engine(DATABASE_URL)

    with engine.connect() as connection:
        # Deletar todas as entradas da tabela alembic_version
        connection.execute(text("DELETE FROM alembic_version"))
        connection.commit()

        # Inserir a nova migration inicial
        connection.execute(text("INSERT INTO alembic_version (version_num) VALUES ('initial_schema')"))
        connection.commit()

        print("✓ Histórico do Alembic resetado com sucesso!")
        print("✓ Migration 'initial_schema' marcada como aplicada")

if __name__ == "__main__":
    try:
        reset_alembic_history()
    except Exception as e:
        print(f"❌ Erro ao resetar histórico do Alembic: {e}")
        sys.exit(1)


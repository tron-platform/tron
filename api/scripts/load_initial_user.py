#!/usr/bin/env python3
"""
Script para carregar usuário admin inicial
"""
import sys
import os

# Adicionar o diretório raiz ao path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from sqlalchemy.orm import Session
from app.shared.database.database import SessionLocal
from app.users.infra.user_model import User, UserRole
import bcrypt


def load_initial_user():
    """Carrega usuário admin inicial se não existir"""
    db: Session = SessionLocal()

    try:
        # Verificar se já existe um usuário admin (usar string diretamente para evitar problema com enum)
        existing_admin = db.query(User).filter(
            User.email == 'admin@example.com'
        ).first()

        # Verificar se é admin (comparar com string)
        if existing_admin and existing_admin.role == UserRole.ADMIN.value:
            print("✓ Usuário admin já existe. Pulando criação.")
            return

        # Criar hash da senha usando bcrypt diretamente
        # (evita problemas de compatibilidade com passlib)
        password = 'admin'
        salt = bcrypt.gensalt()
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

        # Criar usuário admin
        admin_user = User(
            email='admin@example.com',
            hashed_password=hashed_password,
            full_name='Administrator',
            role=UserRole.ADMIN.value,  # Agora é String, funciona normalmente
            is_active=True
        )

        db.add(admin_user)
        db.commit()
        db.refresh(admin_user)

        # Buscar o usuário criado para exibir o UUID
        admin_user = db.query(User).filter(User.email == 'admin@example.com').first()

        print("✓ Usuário admin criado com sucesso!")
        print(f"  Email: admin@example.com")
        print(f"  Senha: admin")
        print(f"  UUID: {admin_user.uuid}")

    except Exception as e:
        db.rollback()
        print(f"✗ Erro ao criar usuário admin: {e}")
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    load_initial_user()


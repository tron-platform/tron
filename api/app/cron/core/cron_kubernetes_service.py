"""Kubernetes operations for crons. Reuses webapp Kubernetes service."""
from app.webapps.core.webapp_kubernetes_service import (
    delete_from_kubernetes,
    upsert_to_kubernetes
)

__all__ = ['delete_from_kubernetes', 'upsert_to_kubernetes']

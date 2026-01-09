from fastapi import HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.clusters.infra.cluster_model import Cluster as ClusterModel
from app.shared.infra.cluster_instance_model import ClusterInstance as ClusterInstanceModel


class ClusterSelectionService:
    """
    Serviço para seleção de clusters baseado em critérios de carga e disponibilidade.
    """

    @staticmethod
    def get_cluster_with_least_load(db: Session, environment_id: int):
        """
        Encontra o cluster de menor carga no environment especificado.
        A carga é medida pela quantidade de ClusterInstance que cada cluster possui.

        Args:
            db: Sessão do banco de dados
            environment_id: ID do environment

        Returns:
            Cluster com menor quantidade de instâncias, ou None se não houver clusters

        Raises:
            HTTPException: Se não houver clusters disponíveis no environment
        """
        # Buscar todos os clusters do environment
        clusters = (
            db.query(ClusterModel)
            .filter(ClusterModel.environment_id == environment_id)
            .all()
        )

        if not clusters:
            return None

        # Calcular a carga de cada cluster (quantidade de ClusterInstance)
        cluster_loads = []
        for cluster in clusters:
            instance_count = (
                db.query(func.count(ClusterInstanceModel.id))
                .filter(ClusterInstanceModel.cluster_id == cluster.id)
                .scalar()
            )
            cluster_loads.append((cluster, instance_count or 0))

        # Retornar o cluster com menor carga
        cluster_loads.sort(key=lambda x: x[1])
        return cluster_loads[0][0]

    @staticmethod
    def get_cluster_with_least_load_or_raise(db: Session, environment_id: int, environment_name: str = None):
        """
        Encontra o cluster de menor carga no environment especificado.
        Lança uma exceção HTTPException se não houver clusters disponíveis.

        Args:
            db: Sessão do banco de dados
            environment_id: ID do environment
            environment_name: Nome do environment (opcional, usado na mensagem de erro)

        Returns:
            Cluster com menor quantidade de instâncias

        Raises:
            HTTPException: Se não houver clusters disponíveis no environment
        """
        cluster = ClusterSelectionService.get_cluster_with_least_load(db, environment_id)

        if cluster is None:
            env_name = environment_name or f"ID {environment_id}"
            raise HTTPException(
                status_code=400,
                detail=f"No clusters available in environment '{env_name}'. Please create at least one cluster."
            )

        return cluster

    @staticmethod
    def get_cluster_loads(db: Session, environment_id: int):
        """
        Retorna a carga de todos os clusters do environment.

        Args:
            db: Sessão do banco de dados
            environment_id: ID do environment

        Returns:
            Lista de tuplas (cluster, carga) ordenada por carga crescente
        """
        clusters = (
            db.query(ClusterModel)
            .filter(ClusterModel.environment_id == environment_id)
            .all()
        )

        cluster_loads = []
        for cluster in clusters:
            instance_count = (
                db.query(func.count(ClusterInstanceModel.id))
                .filter(ClusterInstanceModel.cluster_id == cluster.id)
                .scalar()
            )
            cluster_loads.append((cluster, instance_count or 0))

        cluster_loads.sort(key=lambda x: x[1])
        return cluster_loads

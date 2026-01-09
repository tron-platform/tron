from pydantic import BaseModel
from typing import Dict


class ComponentStats(BaseModel):
    total: int
    webapp: int
    worker: int
    cron: int
    enabled: int
    disabled: int


class DashboardOverview(BaseModel):
    applications: int
    instances: int
    components: ComponentStats
    clusters: int
    environments: int
    components_by_environment: Dict[str, int]  # environment_name -> count
    components_by_cluster: Dict[str, int]  # cluster_name -> count

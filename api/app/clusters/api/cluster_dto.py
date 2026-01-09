from pydantic import BaseModel, ConfigDict
from typing import Optional
from uuid import UUID
from app.environments.api.environment_dto import Environment


class ClusterBase(BaseModel):
    name: str
    api_address: str
    token: str


class ClusterCreate(ClusterBase):
    environment_uuid: UUID


class ClusterResponse(ClusterBase):
    uuid: UUID

    model_config = ConfigDict(
        from_attributes=True,
    )


class GatewayApiReference(BaseModel):
    namespace: str = ""
    name: str = ""


class GatewayApi(BaseModel):
    enabled: bool = False
    resources: list[str] = []


class GatewayFeatures(BaseModel):
    api: GatewayApi
    reference: GatewayApiReference


class ClusterResponseWithValidation(BaseModel):
    uuid: UUID
    name: str
    api_address: str
    environment: Environment
    detail: dict
    gateway: GatewayFeatures

    model_config = ConfigDict(
        from_attributes=True,
    )


class ClusterCompletedResponse(BaseModel):
    uuid: UUID
    name: str
    api_address: str
    available_cpu: Optional[int]
    available_memory: Optional[int]
    environment: Environment
    gateway: GatewayFeatures

    model_config = ConfigDict(
        from_attributes=True,
    )


class Cluster(ClusterBase):
    uuid: UUID

    model_config = ConfigDict(
        from_attributes=True,
    )

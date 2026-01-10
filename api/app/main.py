import importlib
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.shared.database.database import Base, engine
# Also import Base from old database to ensure compatibility
from app.database import Base as OldBase
# Ensure both Bases are the same instance
assert Base is OldBase, "Base instances must be the same for SQLAlchemy relationships to work"

# Import all models to ensure they are registered with SQLAlchemy
# Import order matters for SQLAlchemy relationships
# 1. Base models first (no dependencies)
from app.users.infra.user_model import User
from app.auth.infra.token_model import Token
from app.applications.infra.application_model import Application
from app.environments.infra.environment_model import Environment
from app.templates.infra.template_model import Template

# 2. Models that depend on above
from app.instances.infra.instance_model import Instance
from app.settings.infra.settings_model import Settings

# 3. Models that depend on multiple above - IMPORTANT: ApplicationComponent before ClusterInstance
from app.webapps.infra.application_component_model import ApplicationComponent

# Import ClusterInstance from new structure (uses same Base now)
from app.shared.infra.cluster_instance_model import ClusterInstance

# 4. Cluster must be imported after ClusterInstance for relationships to work
from app.clusters.infra.cluster_model import Cluster

# Import component_template_config model
from app.templates.infra.component_template_config_model import ComponentTemplateConfig

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Tron",
    summary="Platform as a Service built on top of kubernetes",
    version="1.0.0",
    openapi_url="/openapi.json",
    docs_url="/docs",
    redoc_url=None,  # Disable default ReDoc to use custom one with fixed CDN URL
)

# CORS Configuration
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:3000,http://localhost:80").split(",")
CORS_ORIGINS = [origin.strip() for origin in CORS_ORIGINS if origin.strip()]

CORS_ALLOW_CREDENTIALS = os.getenv("CORS_ALLOW_CREDENTIALS", "true").lower() == "true"
CORS_ALLOW_METHODS = os.getenv("CORS_ALLOW_METHODS", "GET,POST,PUT,DELETE,OPTIONS").split(",")
CORS_ALLOW_METHODS = [method.strip() for method in CORS_ALLOW_METHODS if method.strip()]

CORS_ALLOW_HEADERS = os.getenv(
    "CORS_ALLOW_HEADERS",
    "Content-Type,Authorization,Accept,Origin,X-Requested-With,x-tron-token"
).split(",")
CORS_ALLOW_HEADERS = [header.strip() for header in CORS_ALLOW_HEADERS if header.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=CORS_ALLOW_CREDENTIALS,
    allow_methods=CORS_ALLOW_METHODS,
    allow_headers=CORS_ALLOW_HEADERS,
)

# Import new structure routers
from app.applications.api.application_handlers import router as applications_router
from app.instances.api.instance_handlers import router as instances_router
from app.environments.api.environment_handlers import router as environments_router
from app.clusters.api.cluster_handlers import router as clusters_router
from app.templates.api.template_handlers import router as templates_router
from app.templates.api.component_template_config_handlers import router as component_template_config_router
from app.users.api.user_handlers import router as users_router
from app.auth.api.auth_handlers import router as auth_router
from app.auth.api.token_handlers import router as tokens_router
from app.settings.api.settings_handlers import router as settings_router
from app.dashboard.api.dashboard_handlers import router as dashboard_router
from app.webapps.api.webapp_handlers import router as webapps_router
from app.workers.api.worker_handlers import router as workers_router
from app.cron.api.cron_handlers import router as crons_router

# Include new structure routers
app.include_router(applications_router)
app.include_router(instances_router)
app.include_router(environments_router)
app.include_router(clusters_router)
app.include_router(templates_router)
app.include_router(component_template_config_router)
app.include_router(users_router)
app.include_router(auth_router)
app.include_router(tokens_router)
app.include_router(settings_router)
app.include_router(dashboard_router)
app.include_router(webapps_router)
app.include_router(workers_router)
app.include_router(crons_router)

# Legacy routers removed - all features migrated to new structure

# Fix ReDoc CDN URL - use stable version instead of @next
from fastapi.openapi.docs import get_redoc_html

@app.get("/redoc", include_in_schema=False)
async def redoc_html():
    """Custom ReDoc endpoint with fixed CDN URL"""
    return get_redoc_html(
        openapi_url=app.openapi_url,
        title=app.title + " - ReDoc",
        redoc_js_url="https://cdn.jsdelivr.net/npm/redoc@2.1.3/bundles/redoc.standalone.js",
        redoc_favicon_url="https://fastapi.tiangolo.com/img/favicon.png",
    )

@app.get("/health", include_in_schema=False)
async def health_check():
    """Health check endpoint for container orchestration"""
    return {"status": "healthy"}

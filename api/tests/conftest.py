import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from unittest.mock import MagicMock
from app.shared.database.database import Base

# Import all models to ensure SQLAlchemy registers them correctly
# This prevents "failed to locate a name" errors when creating model instances
from app.applications.infra.application_model import Application
from app.environments.infra.environment_model import Environment
from app.instances.infra.instance_model import Instance
from app.settings.infra.settings_model import Settings
from app.clusters.infra.cluster_model import Cluster
from app.webapps.infra.application_component_model import ApplicationComponent
from app.shared.infra.cluster_instance_model import ClusterInstance
from app.users.infra.user_model import User
from app.auth.infra.token_model import Token
from app.templates.infra.template_model import Template
from app.templates.infra.component_template_config_model import ComponentTemplateConfig

@pytest.fixture()
def mock_db():
    engine = create_engine('sqlite:///:memory:')
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    Base.metadata.create_all(bind=engine)

    db = MagicMock()

    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)

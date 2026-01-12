"""Configuration for integration tests."""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.shared.database.database import Base, get_db
from app.users.infra.user_model import User, UserRole
from app.users.infra.user_repository import UserRepository
from app.auth.core.auth_service import AuthService
from app.auth.infra.token_repository import TokenRepository


# Create in-memory SQLite database for testing
# SQLAlchemy will automatically handle UUID conversion for SQLite
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={
        "check_same_thread": False,
        "timeout": 20
    },
    poolclass=StaticPool,
    echo=False
)

# Set SQLite pragmas for better compatibility
@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_conn, connection_record):
    """Set SQLite pragmas for better compatibility."""
    cursor = dbapi_conn.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()

# Handle updated_at for SQLite (server_onupdate doesn't work in SQLite)
from sqlalchemy import event as sa_event
from sqlalchemy.orm import Session
from sqlalchemy import inspect
from datetime import datetime

@sa_event.listens_for(Session, "before_flush")
def receive_before_flush(session, flush_context, instances):
    """Update updated_at timestamp before flush (SQLite compatibility)."""
    for instance in session.dirty:
        # Ensure created_at is never modified during updates
        # If created_at was somehow converted to string, restore it from history
        if hasattr(instance, 'created_at'):
            if not isinstance(instance.created_at, datetime):
                # Get the original value from SQLAlchemy's history using inspect
                insp = inspect(instance)
                history = insp.get_history('created_at', True)
                if history:
                    # Restore from unchanged or deleted history
                    if history.unchanged:
                        instance.created_at = history.unchanged[0]
                    elif history.deleted:
                        instance.created_at = history.deleted[0]
                    # If created_at was added (new object), it should be datetime
                    elif history.added and isinstance(history.added[0], datetime):
                        instance.created_at = history.added[0]

        # Update updated_at if it's a datetime object or None
        if hasattr(instance, 'updated_at'):
            # SQLite DateTime type only accepts Python datetime objects without timezone
            if isinstance(instance.updated_at, datetime) or instance.updated_at is None:
                instance.updated_at = datetime.now()
            elif not isinstance(instance.updated_at, datetime):
                # If updated_at was converted to string, restore from history
                insp = inspect(instance)
                history = insp.get_history('updated_at', True)
                if history and history.unchanged:
                    instance.updated_at = history.unchanged[0]
                elif history and history.deleted:
                    instance.updated_at = history.deleted[0]
                else:
                    # Fallback: set to now
                    instance.updated_at = datetime.now()

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def test_db():
    """Create a fresh database for each test."""
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(test_db):
    """Create a test client with database override."""
    def override_get_db():
        try:
            yield test_db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.fixture
def admin_user(test_db):
    """Create an admin user for testing."""
    user_repository = UserRepository(test_db)
    auth_service = AuthService(user_repository, TokenRepository(test_db))

    user = User(
        email="admin@test.com",
        hashed_password=auth_service.get_password_hash("admin123"),
        full_name="Admin User",
        role=UserRole.ADMIN.value,
        is_active=True
    )

    user = user_repository.create(user)
    test_db.commit()
    test_db.refresh(user)

    return user


@pytest.fixture
def regular_user(test_db):
    """Create a regular user for testing."""
    user_repository = UserRepository(test_db)
    auth_service = AuthService(user_repository, TokenRepository(test_db))

    user = User(
        email="user@test.com",
        hashed_password=auth_service.get_password_hash("user123"),
        full_name="Regular User",
        role=UserRole.USER.value,
        is_active=True
    )

    user = user_repository.create(user)
    test_db.commit()
    test_db.refresh(user)

    return user


@pytest.fixture
def admin_token(client, admin_user):
    """Get authentication token for admin user."""
    response = client.post(
        "/auth/login",
        json={"email": "admin@test.com", "password": "admin123"}
    )
    assert response.status_code == 200
    return response.json()["access_token"]


@pytest.fixture
def user_token(client, regular_user):
    """Get authentication token for regular user."""
    response = client.post(
        "/auth/login",
        json={"email": "user@test.com", "password": "user123"}
    )
    assert response.status_code == 200
    return response.json()["access_token"]

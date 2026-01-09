import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from unittest.mock import MagicMock
from app.shared.database.database import Base

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

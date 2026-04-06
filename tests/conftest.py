import os
import tempfile
import pytest

from app import create_app
from app.extensions import db
from app.models.user import User, UserRole

@pytest.fixture
def app():
    """Create and configure a new app instance for each test."""
    db_fd, db_path = tempfile.mkstemp()
    
    # We create an application with a testing config override
    class TestConfig:
        TESTING = True
        SQLALCHEMY_DATABASE_URI = f"sqlite:///{db_path}"
        SQLALCHEMY_TRACK_MODIFICATIONS = False
        SECRET_KEY = "test-secret"
        JWT_EXPIRY_HOURS = 1

    app = create_app("testing")
    app.config.from_object(TestConfig)

    with app.app_context():
        db.create_all()
        yield app

    os.close(db_fd)
    os.unlink(db_path)

@pytest.fixture
def client(app):
    """A test client for the app."""
    return app.test_client()

@pytest.fixture
def runner(app):
    """A test runner for the app's Click commands."""
    return app.test_cli_runner()

@pytest.fixture
def init_database(app):
    """Seed the database with test data."""
    with app.app_context():
        admin = User(email="admin@test.com", name="Admin", role=UserRole.ADMIN)
        admin.set_password("pass")
        
        viewer = User(email="viewer@test.com", name="Viewer", role=UserRole.VIEWER)
        viewer.set_password("pass")
        
        db.session.add_all([admin, viewer])
        db.session.commit()

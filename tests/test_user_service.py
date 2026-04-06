import pytest

from app.services.user_service import (
    create_user,
    get_user_by_id,
    update_user_role,
    delete_user,
    authenticate_user
)
from app.extensions import db
from app.models.user import User, UserRole, UserStatus
from app.utils.exceptions import (
    AuthenticationError,
    ConflictError,
    ValidationError,
    NotFoundError,
)

def test_create_user(app):
    """Test standard user creation."""
    with app.app_context():
        data = {
            "email": "new@test.com",
            "name": "New User",
            "password": "password",
            "role": UserRole.ANALYST.value
        }
        user = create_user(data)
        assert user["email"] == "new@test.com"
        assert user["role"] == UserRole.ANALYST.value
        assert user["name"] == "New User"

def test_create_duplicate_user(app, init_database):
    """Test duplicate email rejection."""
    with app.app_context():
        data = {
            "email": "admin@test.com",  # Already initialized in fixture
            "name": "Admin Two",
            "password": "password",
        }
        with pytest.raises(ConflictError):
            create_user(data)

def test_authenticate_user(app, init_database):
    """Test login functionality."""
    with app.app_context():
        result = authenticate_user("admin@test.com", "pass")
        assert "token" in result
        assert result["user"]["email"] == "admin@test.com"

def test_protect_last_admin_from_role_change(app, init_database):
    """Test business rule: last admin cannot be demoted."""
    with app.app_context():
        admin = User.query.filter_by(role=UserRole.ADMIN).first()
        
        with pytest.raises(ValidationError, match="this is the last active admin"):
            update_user_role(admin.id, UserRole.VIEWER.value)

def test_protect_last_admin_from_deletion(app, init_database):
    """Test business rule: last admin cannot be deleted."""
    with app.app_context():
        admin = User.query.filter_by(role=UserRole.ADMIN).first()
        
        with pytest.raises(ValidationError, match="this is the last active admin"):
            delete_user(admin.id)


def test_soft_deleted_user_cannot_authenticate(app, init_database):
    """Test deleted users are blocked from authentication."""
    with app.app_context():
        extra_admin = User(email="admin2@test.com", name="Admin 2", role=UserRole.ADMIN)
        extra_admin.set_password("pass")
        db.session.add(extra_admin)
        db.session.commit()

        delete_user(extra_admin.id)

        with pytest.raises(AuthenticationError):
            authenticate_user("admin2@test.com", "pass")


def test_inactive_user_cannot_authenticate(app, init_database):
    """Test inactive users cannot authenticate."""
    with app.app_context():
        viewer = User.query.filter_by(role=UserRole.VIEWER).first()
        viewer.status = UserStatus.INACTIVE
        db.session.commit()

        with pytest.raises(AuthenticationError):
            authenticate_user("viewer@test.com", "pass")
            
def test_get_nonexistent_user(app):
    """Test error handling for missing users."""
    with app.app_context():
        with pytest.raises(NotFoundError):
            get_user_by_id("non-existent-uuid")

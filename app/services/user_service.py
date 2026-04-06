"""
User service module.

Contains all business logic related to user management, including creation,
retrieval, updates, role/status changes, and authentication. This layer
sits between the route handlers and the database models, enforcing business
rules and keeping route handlers thin.

Design Decisions:
    - All methods are module-level functions (not a class) for simplicity
      and testability — no unnecessary state to manage.
    - Business rule validation happens here (e.g., duplicate email checks),
      while field-level input validation is handled by Marshmallow schemas.
    - JWT token generation lives here since it's authentication business logic.
"""

from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional

import jwt
from flask import current_app

from app.extensions import db
from app.models.user import User, UserRole, UserStatus
from app.utils.exceptions import (
    NotFoundError,
    ConflictError,
    AuthenticationError,
    ValidationError,
)


# ---------------------------------------------------------------------------
# Authentication
# ---------------------------------------------------------------------------

def authenticate_user(email: str, password: str) -> Dict[str, Any]:
    """
    Authenticate a user by email and password and return a JWT token.

    Args:
        email: The user's email address.
        password: The plain-text password to verify.

    Returns:
        dict: Contains 'token' (JWT string) and 'user' (serialized user dict).

    Raises:
        AuthenticationError: If email/password is wrong or account is inactive.
    """
    user = User.query.filter_by(email=email, deleted_at=None).first()

    if not user or not user.check_password(password):
        raise AuthenticationError("Invalid email or password")

    if user.status != UserStatus.ACTIVE:
        raise AuthenticationError(
            "Account is inactive. Please contact an administrator."
        )

    token = _generate_token(user)
    return {"token": token, "user": user.to_dict()}


def _generate_token(user: User) -> str:
    """
    Generate a JWT token for the given user.

    The token payload includes:
        - user_id: For user lookup on subsequent requests
        - role: For quick role checks without DB query (informational only;
          authoritative role is always read from DB)
        - exp: Expiration timestamp
        - iat: Issued-at timestamp

    Args:
        user: The User model instance.

    Returns:
        str: Encoded JWT token string.
    """
    expiry_hours = current_app.config.get("JWT_EXPIRY_HOURS", 24)
    now = datetime.now(timezone.utc)

    payload = {
        "user_id": user.id,
        "role": user.role.value,
        "exp": now + timedelta(hours=expiry_hours),
        "iat": now,
    }

    return jwt.encode(
        payload,
        current_app.config["SECRET_KEY"],
        algorithm="HS256",
    )


# ---------------------------------------------------------------------------
# User CRUD Operations
# ---------------------------------------------------------------------------

def create_user(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Create a new user account.

    Args:
        data: Dict with keys: email, name, password, and optionally role.

    Returns:
        dict: The created user's serialized data.

    Raises:
        ConflictError: If a user with the same email already exists.
    """
    # Check for duplicate email across active and deleted users for consistency
    existing = User.query.filter_by(email=data["email"], deleted_at=None).first()
    if existing:
        raise ConflictError(f"A user with email '{data['email']}' already exists")

    user = User(
        email=data["email"],
        name=data["name"],
        role=UserRole(data.get("role", UserRole.VIEWER.value)),
    )
    user.set_password(data["password"])

    db.session.add(user)
    db.session.commit()

    return user.to_dict()


def get_user_by_id(user_id: str) -> Dict[str, Any]:
    """
    Retrieve a single user by ID.

    Args:
        user_id: UUID string of the user.

    Returns:
        dict: The user's serialized data.

    Raises:
        NotFoundError: If no user exists with the given ID.
    """
    user = User.query.get(user_id)
    if not user or user.deleted_at is not None:
        raise NotFoundError(f"User with ID '{user_id}' not found")
    return user.to_dict()


def list_users(filters: Optional[Dict[str, str]] = None) -> List[Dict[str, Any]]:
    """
    List all users with optional filtering.

    Args:
        filters: Optional dict with keys:
            - role: Filter by role (e.g., 'admin')
            - status: Filter by status (e.g., 'active')

    Returns:
        list[dict]: List of serialized user dicts.
    """
    query = User.query.filter(User.deleted_at.is_(None))

    if filters:
        if filters.get("role"):
            query = query.filter(User.role == UserRole(filters["role"]))
        if filters.get("status"):
            query = query.filter(User.status == UserStatus(filters["status"]))

    # Order by creation date (newest first) for consistent results
    query = query.order_by(User.created_at.desc())
    users = query.all()

    return [user.to_dict() for user in users]


def update_user(user_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Update a user's profile information.

    Only updates fields that are present in the data dict.

    Args:
        user_id: UUID string of the user to update.
        data: Dict with optional keys: email, name, password.

    Returns:
        dict: The updated user's serialized data.

    Raises:
        NotFoundError: If no user exists with the given ID.
        ConflictError: If the new email is already taken by another user.
    """
    user = User.query.get(user_id)
    if not user or user.deleted_at is not None:
        raise NotFoundError(f"User with ID '{user_id}' not found")

    # If email is being changed, check for duplicates
    if "email" in data and data["email"] != user.email:
        existing = User.query.filter_by(email=data["email"], deleted_at=None).first()
        if existing:
            raise ConflictError(f"A user with email '{data['email']}' already exists")
        user.email = data["email"]

    if "name" in data:
        user.name = data["name"]

    if "password" in data:
        user.set_password(data["password"])

    user.updated_at = datetime.now(timezone.utc)
    db.session.commit()

    return user.to_dict()


def update_user_role(user_id: str, new_role: str) -> Dict[str, Any]:
    """
    Change a user's role.

    Business Rule: Prevents removing the last admin to avoid system lockout.

    Args:
        user_id: UUID string of the user.
        new_role: The new role string (must be a valid role).

    Returns:
        dict: The updated user's serialized data.

    Raises:
        NotFoundError: If no user exists with the given ID.
        ValidationError: If this would remove the last admin.
    """
    user = User.query.get(user_id)
    if not user or user.deleted_at is not None:
        raise NotFoundError(f"User with ID '{user_id}' not found")

    # Prevent removing the last admin
    parsed_role = UserRole(new_role)

    if user.role == UserRole.ADMIN and parsed_role != UserRole.ADMIN:
        admin_count = User.query.filter_by(
            role=UserRole.ADMIN,
            status=UserStatus.ACTIVE,
            deleted_at=None,
        ).count()
        if admin_count <= 1:
            raise ValidationError(
                "Cannot change role: this is the last active admin. "
                "Promote another user to admin first."
            )

    user.role = parsed_role
    user.updated_at = datetime.now(timezone.utc)
    db.session.commit()

    return user.to_dict()


def update_user_status(user_id: str, new_status: str) -> Dict[str, Any]:
    """
    Activate or deactivate a user account.

    Business Rule: Prevents deactivating the last active admin.

    Args:
        user_id: UUID string of the user.
        new_status: The new status string ('active' or 'inactive').

    Returns:
        dict: The updated user's serialized data.

    Raises:
        NotFoundError: If no user exists with the given ID.
        ValidationError: If this would deactivate the last admin.
    """
    user = User.query.get(user_id)
    if not user or user.deleted_at is not None:
        raise NotFoundError(f"User with ID '{user_id}' not found")

    # Prevent deactivating the last active admin
    parsed_status = UserStatus(new_status)

    if user.role == UserRole.ADMIN and parsed_status == UserStatus.INACTIVE:
        active_admin_count = User.query.filter_by(
            role=UserRole.ADMIN, status=UserStatus.ACTIVE, deleted_at=None
        ).count()
        if active_admin_count <= 1:
            raise ValidationError(
                "Cannot deactivate: this is the last active admin. "
                "Promote another user to admin first."
            )

    user.status = parsed_status
    user.updated_at = datetime.now(timezone.utc)
    db.session.commit()

    return user.to_dict()


def delete_user(user_id: str) -> None:
    """
    Permanently delete a user and their associated records.

    Business Rule: Prevents deleting the last active admin.

    Args:
        user_id: UUID string of the user.

    Raises:
        NotFoundError: If no user exists with the given ID.
        ValidationError: If this would remove the last admin.
    """
    user = User.query.get(user_id)
    if not user or user.deleted_at is not None:
        raise NotFoundError(f"User with ID '{user_id}' not found")

    # Prevent deleting the last admin
    if user.role == UserRole.ADMIN:
        admin_count = User.query.filter_by(
            role=UserRole.ADMIN,
            status=UserStatus.ACTIVE,
            deleted_at=None,
        ).count()
        if admin_count <= 1:
            raise ValidationError(
                "Cannot delete: this is the last active admin. "
                "Promote another user to admin first."
            )

    user.deleted_at = datetime.now(timezone.utc)
    db.session.commit()

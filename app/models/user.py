"""
User model definition.

Represents a system user with role-based access control. Supports three roles
(viewer, analyst, admin) and two statuses (active, inactive).

Security:
    - Passwords are stored as salted hashes using Werkzeug's security module
    - Plain-text passwords are never persisted
"""

import uuid
from datetime import datetime, timezone
from enum import Enum as PyEnum
from typing import Dict, Any

from werkzeug.security import generate_password_hash, check_password_hash

from app.extensions import db


class UserRole(str, PyEnum):
    VIEWER = "viewer"
    ANALYST = "analyst"
    ADMIN = "admin"

class UserStatus(str, PyEnum):
    ACTIVE = "active"
    INACTIVE = "inactive"


class User(db.Model):
    """
    User account model.

    Attributes:
        id: UUID primary key.
        email: Unique email address, used for login.
        name: Display name of the user.
        password_hash: Salted hash of the user's password.
        role: Access level — one of 'viewer', 'analyst', or 'admin'.
        status: Account status — 'active' or 'inactive'.
        created_at: Timestamp of account creation (UTC).
        updated_at: Timestamp of last update (UTC, auto-updated).
    """

    __tablename__ = "users"

    id = db.Column(
        db.String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    name = db.Column(db.String(100), nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.Enum(UserRole), nullable=False, default=UserRole.VIEWER)
    status = db.Column(db.Enum(UserStatus), nullable=False, default=UserStatus.ACTIVE)
    deleted_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(
        db.DateTime,
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    updated_at = db.Column(
        db.DateTime,
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # Relationship: a user can create many financial records
    records = db.relationship(
        "FinancialRecord",
        backref="creator",
        lazy="dynamic",
        cascade="all, delete-orphan",
    )

    def set_password(self, password: str) -> None:
        """Hash and store the user's password. Never stores plain text."""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        """Verify a plain-text password against the stored hash."""
        return check_password_hash(self.password_hash, password)

    def to_dict(self) -> Dict[str, Any]:
        """
        Serialize user to a dictionary for API responses.

        Note: password_hash is intentionally excluded for security.
        """
        return {
            "id": self.id,
            "email": self.email,
            "name": self.name,
            "role": self.role.value,
            "status": self.status.value,
            "created_at": self.created_at.isoformat() + "Z",
            "updated_at": self.updated_at.isoformat() + "Z",
        }

    def __repr__(self) -> str:
        return f"<User {self.email} ({self.role})>"

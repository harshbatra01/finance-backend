"""
User validation schemas.

Defines Marshmallow schemas for validating and deserializing user-related
API input. Each schema enforces field-level constraints and produces clear
error messages when validation fails.
"""

from typing import Optional

from marshmallow import Schema, fields, validate, validates, ValidationError

from app.models.user import UserRole, UserStatus


class UserRegistrationSchema(Schema):
    """
    Validates user registration input.

    Required fields: email, name, password.
    """

    email = fields.Email(
        required=True,
        error_messages={"required": "Email is required", "invalid": "Invalid email format"},
    )
    name = fields.String(
        required=True,
        validate=validate.Length(min=2, max=100),
        error_messages={"required": "Name is required"},
    )
    password = fields.String(
        required=True,
        validate=validate.Length(min=8, max=128),
        load_only=True,
        error_messages={"required": "Password is required"},
    )
    role = fields.String(
        load_default=UserRole.VIEWER.value,
        validate=validate.OneOf([e.value for e in UserRole]),
        error_messages={"invalid": f"Role must be one of: {', '.join([e.value for e in UserRole])}"},
    )

    @validates("name")
    def validate_name_not_blank(self, value: str) -> None:
        """Ensure name is not just whitespace."""
        if not value.strip():
            raise ValidationError("Name cannot be blank")


class UserUpdateSchema(Schema):
    """
    Validates user profile update input.

    All fields are optional — only provided fields are updated.
    """

    email = fields.Email(error_messages={"invalid": "Invalid email format"})
    name = fields.String(validate=validate.Length(min=2, max=100))
    password = fields.String(
        validate=validate.Length(min=8, max=128),
        load_only=True,
    )

    @validates("name")
    def validate_name_not_blank(self, value: Optional[str]) -> None:
        if value is not None and not value.strip():
            raise ValidationError("Name cannot be blank")


class RoleUpdateSchema(Schema):
    """Validates role change requests."""

    role = fields.String(
        required=True,
        validate=validate.OneOf([e.value for e in UserRole]),
        error_messages={
            "required": "Role is required",
            "invalid": f"Role must be one of: {', '.join([e.value for e in UserRole])}",
        },
    )


class StatusUpdateSchema(Schema):
    """Validates status change requests."""

    status = fields.String(
        required=True,
        validate=validate.OneOf([e.value for e in UserStatus]),
        error_messages={
            "required": "Status is required",
            "invalid": f"Status must be one of: {', '.join([e.value for e in UserStatus])}",
        },
    )


class LoginSchema(Schema):
    """Validates login credentials."""

    email = fields.Email(
        required=True,
        error_messages={"required": "Email is required", "invalid": "Invalid email format"},
    )
    password = fields.String(
        required=True,
        error_messages={"required": "Password is required"},
    )

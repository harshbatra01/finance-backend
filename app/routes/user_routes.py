"""
User management routes.

Admin-only endpoints for managing users, roles, and account statuses.
All routes require authentication and admin role.

Routes:
    GET    /api/users          — List all users (with optional filters)
    GET    /api/users/:id      — Get a specific user
    PUT    /api/users/:id      — Update user profile
    PATCH  /api/users/:id/role — Change user role
    PATCH  /api/users/:id/status — Change user status (active/inactive)
    DELETE /api/users/:id      — Delete a user
"""

from typing import Tuple, Union

from flask import Blueprint, request

from app.middleware.auth import require_auth
from app.middleware.rbac import require_role
from app.schemas.user import UserUpdateSchema, RoleUpdateSchema, StatusUpdateSchema
from app.services import user_service
from app.utils.exceptions import ValidationError
from app.utils.responses import success_response, no_content_response

user_bp = Blueprint("users", __name__, url_prefix="/api/users")

# Schema instances (reusable, thread-safe for loading)
_update_schema = UserUpdateSchema()
_role_schema = RoleUpdateSchema()
_status_schema = StatusUpdateSchema()


@user_bp.route("", methods=["GET"])
@require_auth
@require_role("admin")
def list_users() -> Tuple[dict, int]:
    """
    List all users with optional filtering.

    Query Parameters:
        role (optional): Filter by role (viewer, analyst, admin)
        status (optional): Filter by status (active, inactive)

    Returns:
        200: List of users

    ---
    tags:
      - Users
    summary: List users
    security:
      - bearerAuth: []
    parameters:
      - in: query
        name: role
        type: string
        enum: [viewer, analyst, admin]
      - in: query
        name: status
        type: string
        enum: [active, inactive]
    responses:
      200:
        description: Users retrieved
      403:
        description: Admin role required
    """
    filters = {
        "role": request.args.get("role"),
        "status": request.args.get("status"),
    }
    users = user_service.list_users(filters)
    return success_response(
        data=users,
        message=f"Retrieved {len(users)} users",
    )


@user_bp.route("/<user_id>", methods=["GET"])
@require_auth
@require_role("admin")
def get_user(user_id: str) -> Tuple[dict, int]:
    """
    Get a specific user by ID.

    Path Parameters:
        user_id: UUID of the user

    Returns:
        200: User data
        404: User not found

    ---
    tags:
      - Users
    summary: Get user by ID
    security:
      - bearerAuth: []
    parameters:
      - in: path
        name: user_id
        required: true
        type: string
    responses:
      200:
        description: User retrieved
      404:
        description: User not found
    """
    user = user_service.get_user_by_id(user_id)
    return success_response(data=user)


@user_bp.route("/<user_id>", methods=["PUT"])
@require_auth
@require_role("admin")
def update_user(user_id: str) -> Tuple[dict, int]:
    """
    Update a user's profile information.

    Path Parameters:
        user_id: UUID of the user

    Request Body (all fields optional):
        {
            "email": "new@example.com",
            "name": "New Name",
            "password": "newpassword123"
        }

    Returns:
        200: Updated user data
        400: Validation errors
        404: User not found
        409: Email already taken

    ---
    tags:
      - Users
    summary: Update user profile
    security:
      - bearerAuth: []
    consumes:
      - application/json
    parameters:
      - in: path
        name: user_id
        required: true
        type: string
      - in: body
        name: body
        schema:
          type: object
          properties:
            email: {type: string}
            name: {type: string}
            password: {type: string}
    responses:
      200:
        description: User updated
      400:
        description: Validation error
    """
    data = _update_schema.load(request.get_json(force=True))
    if not data:
        raise ValidationError("No valid fields provided for update")

    user = user_service.update_user(user_id, data)
    return success_response(data=user, message="User updated successfully")


@user_bp.route("/<user_id>/role", methods=["PATCH"])
@require_auth
@require_role("admin")
def update_role(user_id: str) -> Tuple[dict, int]:
    """
    Change a user's role.

    Path Parameters:
        user_id: UUID of the user

    Request Body:
        { "role": "analyst" }

    Returns:
        200: Updated user data
        400: Invalid role or last-admin protection
        404: User not found

    ---
    tags:
      - Users
    summary: Update user role
    security:
      - bearerAuth: []
    consumes:
      - application/json
    parameters:
      - in: path
        name: user_id
        required: true
        type: string
      - in: body
        name: body
        required: true
        schema:
          type: object
          required: [role]
          properties:
            role: {type: string, enum: [viewer, analyst, admin]}
    responses:
      200:
        description: User role updated
      400:
        description: Invalid request
    """
    data = _role_schema.load(request.get_json(force=True))
    user = user_service.update_user_role(user_id, data["role"])
    return success_response(data=user, message="User role updated successfully")


@user_bp.route("/<user_id>/status", methods=["PATCH"])
@require_auth
@require_role("admin")
def update_status(user_id: str) -> Tuple[dict, int]:
    """
    Activate or deactivate a user account.

    Path Parameters:
        user_id: UUID of the user

    Request Body:
        { "status": "inactive" }

    Returns:
        200: Updated user data
        400: Last-admin protection
        404: User not found

    ---
    tags:
      - Users
    summary: Update user status
    security:
      - bearerAuth: []
    consumes:
      - application/json
    parameters:
      - in: path
        name: user_id
        required: true
        type: string
      - in: body
        name: body
        required: true
        schema:
          type: object
          required: [status]
          properties:
            status: {type: string, enum: [active, inactive]}
    responses:
      200:
        description: User status updated
      400:
        description: Invalid request
    """
    data = _status_schema.load(request.get_json(force=True))
    user = user_service.update_user_status(user_id, data["status"])
    return success_response(data=user, message="User status updated successfully")


@user_bp.route("/<user_id>", methods=["DELETE"])
@require_auth
@require_role("admin")
def delete_user(user_id: str) -> Union[Tuple[str, int], Tuple[dict, int]]:
    """
    Delete a user and their associated records.

    Path Parameters:
        user_id: UUID of the user

    Returns:
        204: No content (successfully deleted)
        400: Last-admin protection
        404: User not found

    ---
    tags:
      - Users
    summary: Soft-delete a user
    security:
      - bearerAuth: []
    parameters:
      - in: path
        name: user_id
        required: true
        type: string
    responses:
      204:
        description: User deleted
      400:
        description: Invalid operation
      404:
        description: User not found
    """
    user_service.delete_user(user_id)
    return no_content_response()

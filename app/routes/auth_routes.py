"""
Authentication routes.

Handles user registration, login, and profile retrieval.
These endpoints are the entry point for users interacting with the system.

Routes:
    POST /api/auth/register  — Create a new user account
    POST /api/auth/login     — Authenticate and receive a JWT token
    GET  /api/auth/me        — Get the current authenticated user's profile
"""

from typing import Tuple

from flask import Blueprint, request, g

from app.middleware.auth import require_auth
from app.extensions import limiter
from app.schemas.user import UserRegistrationSchema, LoginSchema
from app.services import user_service
from app.utils.responses import success_response, created_response

auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")

# Schema instances (reusable, thread-safe for loading)
_registration_schema = UserRegistrationSchema()
_login_schema = LoginSchema()


@auth_bp.route("/register", methods=["POST"])
@limiter.limit("20 per hour")
def register() -> Tuple[dict, int]:
    """
    Register a new user account.

    Request Body:
        {
            "email": "user@example.com",      (required, valid email)
            "name": "John Doe",                (required, 2-100 chars)
            "password": "securepass123",        (required, min 8 chars)
            "role": "viewer"                    (optional, default: viewer)
        }

    Returns:
        201: Created user data with success message
        400: Validation errors
        409: Email already exists

    ---
    tags:
      - Auth
    summary: Register a new user
    consumes:
      - application/json
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          required: [email, name, password]
          properties:
            email: {type: string, example: user@example.com}
            name: {type: string, example: John Doe}
            password: {type: string, example: securepass123}
            role: {type: string, enum: [viewer, analyst, admin], example: viewer}
    responses:
      201:
        description: User registered successfully
      400:
        description: Validation error
      409:
        description: Email already exists
    """
    data = _registration_schema.load(request.get_json(force=True))
    user = user_service.create_user(data)
    return created_response(data=user, message="User registered successfully")


@auth_bp.route("/login", methods=["POST"])
@limiter.limit("10 per minute")
def login() -> Tuple[dict, int]:
    """
    Authenticate and receive a JWT token.

    Request Body:
        {
            "email": "user@example.com",    (required)
            "password": "securepass123"      (required)
        }

    Returns:
        200: JWT token and user data
        401: Invalid credentials or inactive account

    ---
    tags:
      - Auth
    summary: Login and get JWT
    consumes:
      - application/json
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          required: [email, password]
          properties:
            email: {type: string, example: user@example.com}
            password: {type: string, example: securepass123}
    responses:
      200:
        description: Login successful
      401:
        description: Invalid credentials
    """
    data = _login_schema.load(request.get_json(force=True))
    result = user_service.authenticate_user(data["email"], data["password"])
    return success_response(
        data=result,
        message="Login successful",
    )


@auth_bp.route("/me", methods=["GET"])
@require_auth
def get_profile() -> Tuple[dict, int]:
    """
    Get the current authenticated user's profile.

    Requires: Valid JWT token in Authorization header.

    Returns:
        200: Current user's data
        401: Invalid or missing token

    ---
    tags:
      - Auth
    summary: Get current user profile
    security:
      - bearerAuth: []
    responses:
      200:
        description: Profile retrieved successfully
      401:
        description: Missing or invalid token
    """
    return success_response(
        data=g.current_user.to_dict(),
        message="Profile retrieved successfully",
    )

"""
JWT authentication middleware.

Provides a decorator that validates JWT tokens from the Authorization header,
loads the corresponding user, and makes it available via Flask's `g` context.

Usage:
    @app.route('/protected')
    @require_auth
    def protected_endpoint():
        user = g.current_user  # authenticated user is available here
        ...

Security checks:
    1. Token presence in Authorization header (Bearer scheme)
    2. Token validity (signature, expiry)
    3. User existence in database
    4. User account is active (inactive users are rejected)
"""

from functools import wraps
from typing import Any, Callable, TypeVar, cast

import jwt
from flask import request, g, current_app

from app.extensions import db
from app.models.user import User, UserStatus
from app.utils.exceptions import AuthenticationError

RouteFunction = TypeVar("RouteFunction", bound=Callable[..., Any])

def require_auth(f: RouteFunction) -> RouteFunction:
    """
    Decorator that enforces JWT authentication on a route.

    Extracts the Bearer token from the Authorization header, decodes it,
    verifies the user exists and is active, then stores the user object
    in `g.current_user` for downstream handlers.

    Raises:
        AuthenticationError: If token is missing, invalid, expired, or
            if the user is not found or inactive.
    """

    @wraps(f)
    def decorated(*args: Any, **kwargs: Any) -> Any:
        # --- Extract token from header ---
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            raise AuthenticationError("Authorization header is required")

        parts = auth_header.split()
        if len(parts) != 2 or parts[0].lower() != "bearer":
            raise AuthenticationError(
                "Authorization header must use Bearer scheme (e.g., 'Bearer <token>')"
            )

        token = parts[1]

        # --- Decode and validate token ---
        try:
            payload = jwt.decode(
                token,
                current_app.config["SECRET_KEY"],
                algorithms=["HS256"],
            )
        except jwt.ExpiredSignatureError:
            raise AuthenticationError("Token has expired, please login again")
        except jwt.InvalidTokenError:
            raise AuthenticationError("Invalid token")

        # --- Load user from database ---
        user_id = payload.get("user_id")
        if not user_id:
            raise AuthenticationError("Invalid token payload")

        user = db.session.get(User, user_id)
        if not user or user.deleted_at is not None:
            raise AuthenticationError("User not found")

        # --- Check user is active ---
        if user.status != UserStatus.ACTIVE:
            raise AuthenticationError(
                "Account is inactive. Please contact an administrator."
            )

        # Store authenticated user for downstream use
        g.current_user = user
        return f(*args, **kwargs)

    return cast(RouteFunction, decorated)

"""
Role-based access control (RBAC) middleware.

Provides a decorator that restricts route access to users with specific roles.
Must be used AFTER @require_auth, which populates g.current_user.

Usage:
    @app.route('/admin-only')
    @require_auth
    @require_role('admin')
    def admin_endpoint():
        ...

    @app.route('/analyst-or-admin')
    @require_auth
    @require_role('analyst', 'admin')
    def analyst_endpoint():
        ...

Design Note:
    The decorator accepts multiple roles, making it easy to express permissions
    declaratively at the route level. This keeps authorization logic visible
    and co-located with the endpoint definition.
"""

from functools import wraps
from typing import Any, Callable, TypeVar, cast

from flask import g

from app.utils.exceptions import AuthorizationError

RouteFunction = TypeVar("RouteFunction", bound=Callable[..., Any])

def require_role(*allowed_roles: str) -> Callable[[RouteFunction], RouteFunction]:
    """
    Decorator factory that restricts access to users with specified roles.

    Args:
        *allowed_roles: One or more role strings (e.g., 'admin', 'analyst').
            The current user's role must match at least one.

    Raises:
        AuthorizationError: If the current user's role is not in the
            allowed roles list.

    Example:
        @require_role('admin')          # admin only
        @require_role('analyst', 'admin')  # analyst or admin
    """

    def decorator(f: RouteFunction) -> RouteFunction:
        @wraps(f)
        def decorated(*args: Any, **kwargs: Any) -> Any:
            current_user = g.get("current_user")
            if not current_user:
                raise AuthorizationError("Authentication required before authorization check")

            current_role = current_user.role.value
            if current_role not in allowed_roles:
                raise AuthorizationError(
                    f"This action requires one of the following roles: "
                    f"{', '.join(allowed_roles)}. Your role: {current_role}."
                )

            return f(*args, **kwargs)

        return cast(RouteFunction, decorated)

    return decorator

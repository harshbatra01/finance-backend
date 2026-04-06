from typing import Any, Optional

"""
Custom exception classes for the application.

Defines a hierarchy of application-specific exceptions that map to HTTP status
codes. These are caught by the global error handler and converted to
standardized JSON error responses.

Exception Hierarchy:
    AppException (base)
    ├── ValidationError (400)
    ├── AuthenticationError (401)
    ├── AuthorizationError (403)
    ├── NotFoundError (404)
    └── ConflictError (409)
"""


class AppException(Exception):
    """
    Base application exception.

    All custom exceptions inherit from this class, providing a consistent
    interface with an HTTP status code, error code string, and human-readable
    message.
    """

    status_code = 500
    error_code = "INTERNAL_ERROR"

    def __init__(
        self,
        message: str = "An unexpected error occurred",
        details: Optional[Any] = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.details = details


class ValidationError(AppException):
    """Raised when input data fails validation (400 Bad Request)."""

    status_code = 400
    error_code = "VALIDATION_ERROR"

    def __init__(
        self,
        message: str = "Invalid input data",
        details: Optional[Any] = None,
    ) -> None:
        super().__init__(message, details)


class AuthenticationError(AppException):
    """Raised when authentication fails (401 Unauthorized)."""

    status_code = 401
    error_code = "AUTHENTICATION_ERROR"

    def __init__(
        self,
        message: str = "Authentication required",
        details: Optional[Any] = None,
    ) -> None:
        super().__init__(message, details)


class AuthorizationError(AppException):
    """Raised when user lacks permission for an action (403 Forbidden)."""

    status_code = 403
    error_code = "AUTHORIZATION_ERROR"

    def __init__(
        self,
        message: str = "Insufficient permissions",
        details: Optional[Any] = None,
    ) -> None:
        super().__init__(message, details)


class NotFoundError(AppException):
    """Raised when a requested resource does not exist (404 Not Found)."""

    status_code = 404
    error_code = "NOT_FOUND"

    def __init__(
        self,
        message: str = "Resource not found",
        details: Optional[Any] = None,
    ) -> None:
        super().__init__(message, details)


class ConflictError(AppException):
    """Raised on resource conflicts like duplicate entries (409 Conflict)."""

    status_code = 409
    error_code = "CONFLICT"

    def __init__(
        self,
        message: str = "Resource conflict",
        details: Optional[Any] = None,
    ) -> None:
        super().__init__(message, details)

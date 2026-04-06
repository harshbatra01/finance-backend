"""
Global error handler registration.

Registers error handlers on the Flask app that catch both custom application
exceptions and standard HTTP errors, converting them all to the standardized
JSON error response format.

This ensures that no endpoint ever returns a raw HTML error page — every
error is a predictable JSON object that frontend consumers can parse.
"""

from typing import Any, Tuple

from flask import Flask
from marshmallow import ValidationError as MarshmallowValidationError
from werkzeug.exceptions import HTTPException

from app.utils.exceptions import AppException
from app.utils.responses import error_response


def register_error_handlers(app: Flask) -> None:
    """
    Register global error handlers on the Flask application.

    Handles three categories of errors:
    1. AppException subclasses — our custom business logic errors
    2. Marshmallow ValidationError — input validation failures
    3. Werkzeug HTTPException — standard HTTP errors (404, 405, etc.)
    4. Unhandled Exception — catches everything else as 500
    """

    @app.errorhandler(AppException)
    def handle_app_exception(error: AppException) -> Tuple[Any, int]:
        """Handle custom application exceptions with appropriate status codes."""
        return error_response(
            error_code=error.error_code,
            message=error.message,
            details=error.details,
            status_code=error.status_code,
        )

    @app.errorhandler(MarshmallowValidationError)
    def handle_marshmallow_validation_error(
        error: MarshmallowValidationError,
    ) -> Tuple[Any, int]:
        """
        Handle Marshmallow validation errors.

        Converts Marshmallow's error dict format into our standardized
        error response with field-level details.
        """
        return error_response(
            error_code="VALIDATION_ERROR",
            message="Invalid input data",
            details=error.messages,
            status_code=400,
        )

    @app.errorhandler(HTTPException)
    def handle_http_exception(error: HTTPException) -> Tuple[Any, int]:
        """
        Handle standard Werkzeug HTTP exceptions (404, 405, etc.).

        Ensures these return JSON instead of HTML error pages.
        """
        return error_response(
            error_code=error.name.upper().replace(" ", "_"),
            message=error.description,
            status_code=error.code,
        )

    @app.errorhandler(Exception)
    def handle_unexpected_exception(error: Exception) -> Tuple[Any, int]:
        """
        Catch-all handler for unhandled exceptions.

        Logs the error and returns a generic 500 response. In production,
        this prevents leaking internal details to the client.
        """
        app.logger.error(f"Unhandled exception: {error}", exc_info=True)
        return error_response(
            error_code="INTERNAL_ERROR",
            message="An unexpected error occurred. Please try again later.",
            status_code=500,
        )

"""
Flask application factory.

Uses the factory pattern to create and configure the Flask application.
This approach allows:
    - Multiple app instances (useful for testing with different configs)
    - Clean extension initialization
    - Blueprint registration in a single, organized location

The factory is the single source of truth for how the application is assembled.
"""

import os
from typing import Optional

from flask import Flask, request
from flask_cors import CORS
from flasgger import Swagger

from config import config_by_name
from app.extensions import db, limiter
from app.middleware.error_handler import register_error_handlers
from app.middleware.logging_middleware import register_request_logger
from app.utils.exceptions import ValidationError


def create_app(config_name: Optional[str] = None) -> Flask:
    """
    Create and configure the Flask application.

    Args:
        config_name: Environment name ('development', 'testing', 'production').
                     Defaults to the FLASK_ENV environment variable or 'development'.

    Returns:
        Flask: The configured application instance.
    """
    if config_name is None:
        config_name = os.getenv("FLASK_ENV", "development")

    app = Flask(__name__)
    app.config.from_object(config_by_name[config_name])

    # --- Initialize extensions ---
    db.init_app(app)
    limiter.init_app(app)
    CORS(app)  # Enable CORS for frontend integration
    
    # Initialize Swagger UI
    swagger_config = {
        "headers": [],
        "specs": [
            {
                "endpoint": "apispec",
                "route": "/apispec.json",
                "rule_filter": lambda rule: True,  # all in
                "model_filter": lambda tag: True,  # all in
            }
        ],
        "static_url_path": "/flasgger_static",
        "swagger_ui": True,
        "specs_route": "/api/docs"
    }
    Swagger(app, config=swagger_config, template={
        "info": {
            "title": "Finance Dashboard API",
            "description": "API documentation for the Finance Dashboard Backend",
            "version": "1.0.0"
        },
        "components": {
            "securitySchemes": {
                "bearerAuth": {
                    "type": "http",
                    "scheme": "bearer",
                    "bearerFormat": "JWT"
                }
            }
        },
        "security": [{"bearerAuth": []}]
    })

    @app.before_request
    def enforce_content_type():
        """Ensure body-bearing requests use application/json."""
        if request.method in ["POST", "PUT", "PATCH"] and request.content_length:
            if not request.is_json and request.content_length:
                raise ValidationError("Content-Type must be application/json")

    # --- Register global error handlers ---
    register_error_handlers(app)

    # --- Register request logger ---
    register_request_logger(app)

    # --- Register route blueprints ---
    _register_blueprints(app)

    # --- Create database tables ---
    with app.app_context():
        # Import models so SQLAlchemy knows about them
        from app.models import User, FinancialRecord  # noqa: F401
        db.create_all()

    # --- Register a health check endpoint ---
    @app.route("/api/health", methods=["GET"])
    def health_check():
        """
        Simple health check endpoint for monitoring.

        ---
        tags:
          - Health
        summary: Health check
        responses:
          200:
            description: Service is healthy
        """
        return {"status": "healthy", "service": "finance-backend"}, 200

    return app


def _register_blueprints(app: Flask) -> None:
    """
    Register all route blueprints with the application.

    Centralizing blueprint registration here makes it easy to see all
    available API modules at a glance.
    """
    from app.routes.auth_routes import auth_bp
    from app.routes.user_routes import user_bp
    from app.routes.record_routes import record_bp
    from app.routes.dashboard_routes import dashboard_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(user_bp)
    app.register_blueprint(record_bp)
    app.register_blueprint(dashboard_bp)

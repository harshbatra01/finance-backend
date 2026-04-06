"""
Request logging middleware.

Registers pre and post request handlers to log detailed information about
incoming API requests and outgoing responses, including duration and user.
This is critical for production debugging and audit trails.
"""

import logging
import time

from flask import request, g

# Configure module-level logger
logger = logging.getLogger("finance_api")
logger.setLevel(logging.INFO)

# Create console handler with formatting
if not logger.handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(
        logging.Formatter("[%(asctime)s] %(levelname)s in %(module)s: %(message)s")
    )
    logger.addHandler(handler)


def register_request_logger(app):
    """
    Register request logging hooks on the Flask application.

    Logs:
        - Method and Path path
        - Remote IP address
        - Current user ID (if authenticated)
        - Response status code
        - Request duration (ms)
    """

    @app.before_request
    def start_timer():
        """Record the start time of the request."""
        g.start_time = time.time()

    @app.after_request
    def log_request(response):
        """Log the request details after it has been processed."""
        # Calculate request duration in milliseconds
        if hasattr(g, "start_time"):
            duration = (time.time() - g.start_time) * 1000
        else:
            duration = 0

        # Attempt to get the user ID if they were authenticated during the request
        user_id = "anonymous"
        if hasattr(g, "current_user") and g.current_user:
            user_id = g.current_user.id

        # Skip logging for health check endpoints to reduce noise
        if request.path == "/api/health":
            return response

        message = (
            f"{request.remote_addr} - {request.method} {request.path} "
            f"- Status: {response.status_code} "
            f"- User: {user_id} "
            f"- Duration: {duration:.2f}ms"
        )

        if response.status_code >= 500:
            logger.error(message)
        elif response.status_code >= 400:
            logger.warning(message)
        else:
            logger.info(message)

        return response

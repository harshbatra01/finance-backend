"""
Application entry point.

Run this file to start the Flask development server:
    python run.py

The server binds to 0.0.0.0:5000 by default, making it accessible
from other devices on the same network during development.
"""

import os

from app import create_app

app = create_app()

if __name__ == "__main__":
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "5050"))
    app.run(
        host=host,
        port=port,
        debug=True,
    )

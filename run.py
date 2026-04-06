"""
Application entry point.

Run this file to start the Flask development server:
    python run.py

The server binds to 0.0.0.0:5000 by default, making it accessible
from other devices on the same network during development.
"""

from app import create_app

app = create_app()

if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True,
    )

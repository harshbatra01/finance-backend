"""
WSGI entrypoint for production servers (e.g., gunicorn).

Render "Start Command" can point to:
    gunicorn wsgi:app --bind 0.0.0.0:$PORT
"""

from app import create_app

app = create_app()


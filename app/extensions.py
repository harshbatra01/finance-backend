"""
Flask extensions.

Extensions are initialized here and bound to the app in the factory function.
This avoids circular imports between modules that need access to the database.
"""

from flask_sqlalchemy import SQLAlchemy
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

db = SQLAlchemy()
limiter = Limiter(key_func=get_remote_address)

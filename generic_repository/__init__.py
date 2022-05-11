# flake8: noqa F401

from .base import GenericBaseRepository
from .mapper import Mapper

try:
    from .database import DatabaseRepository
except ImportError:  # pragma nocover
    # maybe SQLAlchemy is not installed, we can safely ignore.
    pass

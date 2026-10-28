"""Database module for Nova Law AI Backend."""

from .database import Base, SessionLocal, get_db
from .models import User

__all__ = ["Base", "SessionLocal", "User", "get_db"]

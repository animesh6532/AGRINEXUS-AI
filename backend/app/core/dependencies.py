"""
Dependency injection providers for the AgriNexus-AI backend.
"""

from typing import Generator

from sqlalchemy.orm import Session

from .config import settings
from .logging import logger
from ..database import connection


def get_db() -> Generator[Session, None, None]:
    """
    Dependency provider for database sessions.

    Yields:
        Session: Database session
    """
    db = connection.SessionLocal()
    try:
        yield db
    except Exception as e:
        logger.error(f"Database session error: {e}")
        db.rollback()
        raise
    finally:
        db.close()
"""
Database connection and session management for the AgriNexus-AI backend.
"""

from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

from ..core.config import settings
from ..core.logging import logger


# Create SQLAlchemy engine
engine = create_engine(
    settings.DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in settings.DATABASE_URL else {},
    poolclass=StaticPool if "sqlite" in settings.DATABASE_URL else None,
    echo=settings.DEBUG,
)

# Create SessionLocal class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Session:
    """
    Dependency getter for database session.
    Yields a database session and ensures it's closed after use.

    Yields:
        Session: Database session
    """
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        logger.error(f"Database session error: {e}")
        db.rollback()
        raise
    finally:
        db.close()


def create_tables():
    """
    Create all database tables and perform lightweight schema auto-migrations
    for existing databases (adding missing columns).
    """
    try:
        from . import models  # Import here to avoid circular imports
        from sqlalchemy import inspect, text

        models.Base.metadata.create_all(bind=engine)

        # Inspect existing columns and auto-migrate missing ones (for SQLite/Postgres)
        inspector = inspect(engine)
        if "fields" in inspector.get_table_names():
            existing_cols = {c["name"] for c in inspector.get_columns("fields")}
            missing_cols = [
                ("boundary_geojson", "TEXT"),
                ("perimeter_m", "FLOAT"),
                ("centroid_lat", "FLOAT"),
                ("centroid_lng", "FLOAT"),
                ("geometry_source", "VARCHAR(30) DEFAULT 'MANUAL'"),
                ("geometry_updated_at", "DATETIME"),
            ]
            with engine.connect() as conn:
                for col_name, col_type in missing_cols:
                    if col_name not in existing_cols:
                        logger.info(f"Auto-migrating database: Adding column '{col_name}' to 'fields' table")
                        conn.execute(text(f"ALTER TABLE fields ADD COLUMN {col_name} {col_type}"))
                conn.commit()

        logger.info("Database tables created and verified successfully")
    except Exception as e:
        logger.error(f"Error creating/migrating database tables: {e}")
        raise


# Enable foreign key constraints for SQLite
@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    """Enable foreign key constraints for SQLite."""
    if "sqlite" in settings.DATABASE_URL:
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()


# Ensure tables exist on import
try:
    create_tables()
except Exception as _e:
    pass
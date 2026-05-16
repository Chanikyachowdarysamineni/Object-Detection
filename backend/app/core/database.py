from sqlalchemy import create_engine, event
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool, QueuePool
from typing import Generator
import logging

from app.core.config import settings

logger = logging.getLogger(__name__)

# Determine pool class based on environment
# Use NullPool for SQLite (testing), QueuePool for production
if "sqlite" in settings.DATABASE_URL:
    pool_class = NullPool
else:
    pool_class = QueuePool

try:
    # Create SQLAlchemy engine with production-ready settings
    if "sqlite" in settings.DATABASE_URL:
        engine = create_engine(
            settings.DATABASE_URL,
            echo=settings.DATABASE_ECHO,
            poolclass=NullPool,
        )
    else:
        # PostgreSQL configuration
        engine = create_engine(
            settings.DATABASE_URL,
            echo=settings.DATABASE_ECHO,
            pool_pre_ping=True,
            pool_recycle=3600,
            connect_args={"connect_timeout": 10},
        )
    logger.info(f"[OK] Database engine created: {settings.DATABASE_URL[:50]}...")
except Exception as e:
    logger.error(f"[ERROR] Failed to create database engine: {str(e)}")
    raise

# Create session factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)

# Base class for all models
Base = declarative_base()


@event.listens_for(engine, "connect")
def receive_connect(dbapi_conn, connection_record):
    """Event listener for database connections."""
    try:
        # Set connection timeout
        if hasattr(dbapi_conn, 'timeout'):
            dbapi_conn.timeout = 10
    except Exception as e:
        logger.debug(f"Could not set connection timeout: {str(e)}")


def get_db() -> Generator:
    """
    Dependency to get database session.
    Provides proper error handling and resource cleanup.
    """
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        logger.error(f"Database session error: {str(e)}")
        db.rollback()
        raise
    finally:
        try:
            db.close()
        except Exception as e:
            logger.error(f"Error closing database session: {str(e)}")


def test_db_connection() -> bool:
    """Test database connectivity."""
    try:
        with engine.connect() as conn:
            conn.execute("SELECT 1")
        logger.info("✅ Database connection test successful")
        return True
    except Exception as e:
        logger.error(f"❌ Database connection test failed: {str(e)}")
        return False

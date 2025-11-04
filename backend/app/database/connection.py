# connection.py
# Database connection and session management

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from ..config import get_settings

# Get application settings
settings = get_settings()

# Create database engine with connection pooling
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,     # Verify connections before use
    pool_recycle=300,       # Recycle connections every 5 minutes
    pool_size=20,           # Increase from default 5 to 20 connections
    max_overflow=40,        # Increase from default 10 to 40 overflow connections
    pool_timeout=30,        # Wait up to 30s for a connection before failing
    echo=settings.DEBUG     # Log SQL queries in debug mode
)

# Create sessionmaker factory for database sessions
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    """
    Dependency function to get database session.
    Used with FastAPI dependency injection.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
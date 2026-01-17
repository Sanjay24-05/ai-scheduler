"""Database configuration and setup for SQLAlchemy."""
import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get database URL from environment or use default
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./scheduler.db")

# Create SQLAlchemy engine
# For SQLite, we need to enable check_same_thread=False for FastAPI
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(DATABASE_URL, connect_args=connect_args, echo=False)

# Create SessionLocal class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create Base class for models
Base = declarative_base()


def get_db():
    """
    Dependency function to get database session.
    Yields a database session and ensures it's closed after use.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Initialize database by creating all tables."""
    # Import all models here to ensure they're registered with Base
    from models import user, task, schedule, preferences, time_guideline
    
    # Create all tables
    Base.metadata.create_all(bind=engine)
    print("Database initialized successfully!")


def drop_db():
    """Drop all database tables. Use with caution!"""
    Base.metadata.drop_all(bind=engine)
    print("Database tables dropped!")

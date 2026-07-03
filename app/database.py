"""
SQLAlchemy database engine, session factory, and declarative base.
"""
import logging
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base, Session

from app.config import settings

logger = logging.getLogger(__name__)

connect_args = {"check_same_thread": False} if settings.DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(settings.DATABASE_URL, connect_args=connect_args, future=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine, future=True)

Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency that yields a database session and closes it afterwards."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """Create all database tables. Safe to call multiple times."""
    from app import models  # noqa: F401  (ensures models are registered on Base)

    Base.metadata.create_all(bind=engine)
    logger.info("Database initialized at %s", settings.DATABASE_URL)

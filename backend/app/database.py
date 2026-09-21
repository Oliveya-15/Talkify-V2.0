"""
SQLAlchemy engine and session management.

Talkify defaults to SQLite for zero-setup local development. Pointing
DATABASE_URL (in .env) at a postgresql+psycopg:// URL switches the whole
app to Postgres with no code changes — SQLAlchemy abstracts the dialect,
and Alembic migrations (see backend/alembic/) work against either.
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from app.config import settings

connect_args = {"check_same_thread": False} if settings.DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(settings.DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """FastAPI dependency: yields a DB session per-request and always closes it."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

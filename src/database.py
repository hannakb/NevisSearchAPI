from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session, DeclarativeBase
import os

_engine = None
_SessionLocal = None


def get_engine():
    global _engine, _SessionLocal

    if _engine is None:
        database_url = os.getenv("DATABASE_URL")
        if not database_url:
            raise RuntimeError("DATABASE_URL must be set at runtime")

        _engine = create_engine(
            database_url,
            echo=False,
            pool_pre_ping=True,
        )

        _SessionLocal = sessionmaker(
            _engine,
            expire_on_commit=False,
        )

    return _engine, _SessionLocal


class Base(DeclarativeBase):
    pass


def get_db() -> Session:
    _, SessionLocal = get_engine()
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

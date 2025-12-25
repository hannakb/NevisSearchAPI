from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session, DeclarativeBase
import os
import logging

logger = logging.getLogger(__name__)

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
        
        # Initialize pgvector extension
        _init_pgvector(_engine)
    
    return _engine, _SessionLocal


def _init_pgvector(engine):
    """Initialize pgvector extension (must run before creating tables)"""
    try:
        with engine.connect() as conn:
            logger.info("Attempting to enable pgvector extension...")
            conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
            conn.commit()
            logger.info("✓ pgvector extension enabled successfully")
    except Exception as e:
        logger.error(f"✗ Failed to enable pgvector extension: {e}")
        logger.error(
            "\n" + "="*60 + "\n"
            "PGVECTOR EXTENSION ERROR\n"
            "="*60 + "\n"
            "The 'vector' extension is not available in your PostgreSQL database.\n\n"
            "To fix this on Railway:\n"
            "1. Go to your PostgreSQL service in Railway dashboard\n"
            "2. Click 'Data' tab\n"
            "3. Run this SQL command:\n"
            "   CREATE EXTENSION vector;\n\n"
            "Alternative: Use a database with pgvector pre-installed:\n"
            "  - Supabase (free tier): https://supabase.com\n"
            "  - Neon (free tier): https://neon.tech\n"
            "="*60
        )
        raise RuntimeError(
            "pgvector extension is required but not available. "
            "Please enable it in your PostgreSQL database."
        ) from e


class Base(DeclarativeBase):
    pass


def get_db() -> Session:
    _, SessionLocal = get_engine()
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Create all database tables"""
    engine, _ = get_engine()
    Base.metadata.create_all(bind=engine)
    logger.info("✓ Database tables created")
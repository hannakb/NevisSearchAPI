from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session, DeclarativeBase
import os
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

_engine = None
_SessionLocal = None


def get_engine():
    global _engine, _SessionLocal
    if _engine is None:
        database_url = os.getenv("DATABASE_URL")
        if not database_url:
            raise RuntimeError("DATABASE_URL must be set at runtime")
        
        # Fix Railway's postgres:// to postgresql://
        if database_url.startswith("postgres://"):
            database_url = database_url.replace("postgres://", "postgresql://", 1)
        
        logger.info("🔌 Connecting to database...")
        
        _engine = create_engine(
            database_url,
            echo=False,
            pool_pre_ping=True,
        )
        _SessionLocal = sessionmaker(
            _engine,
            expire_on_commit=False,
        )
        
        logger.info("✓ Database connection established")
        
        # Initialize pgvector extension
        _init_pgvector(_engine)
    
    return _engine, _SessionLocal


def _init_pgvector(engine):
    """Initialize pgvector extension (must run before creating tables)"""
    try:
        with engine.connect() as conn:
            logger.info("🔧 Attempting to enable pgvector extension...")
            conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
            conn.commit()
            logger.info("✓ pgvector extension enabled")
    except Exception as e:
        logger.error(f"✗ Failed to enable pgvector: {e}")
        raise RuntimeError(f"pgvector extension is required: {e}") from e


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
    logger.info("=" * 60)
    logger.info("🚀 INITIALIZING DATABASE")
    logger.info("=" * 60)
    
    # Get engine (this will also init pgvector)
    engine, _ = get_engine()
    
    # Import models to register them with Base
    logger.info("📦 Importing models...")
    from . import models  # noqa: F401
    
    # Check what tables will be created
    logger.info(f"📋 Tables to create: {list(Base.metadata.tables.keys())}")
    
    # Create all tables
    logger.info("🔨 Creating database tables...")
    Base.metadata.create_all(bind=engine)
    
    # Verify tables were created
    with engine.connect() as conn:
        result = conn.execute(text(
            "SELECT tablename FROM pg_tables WHERE schemaname = 'public'"
        ))
        existing_tables = [row[0] for row in result]
        logger.info(f"✓ Tables in database: {existing_tables}")
    
    logger.info("=" * 60)
    logger.info("✓ DATABASE INITIALIZATION COMPLETE")
    logger.info("=" * 60)

import logging
import os
from typing import Generator

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

logger = logging.getLogger(__name__)


class Base(DeclarativeBase):
    pass


class Database:

    def __init__(self) -> None:
        """Initialize the database manager (lazy initialization)."""
        self._engine: Engine | None = None
        self._session_local: sessionmaker[Session] | None = None

    @staticmethod
    def _normalize_database_url(url: str) -> str:
        """
        Normalize database URL format.
        
        Some platforms (like Railway) use postgres:// instead of postgresql://.
        SQLAlchemy requires postgresql:// format.
        """
        if url.startswith("postgres://"):
            return url.replace("postgres://", "postgresql://", 1)
        return url

    @staticmethod
    def _get_database_url() -> str:
        """Get and validate DATABASE_URL environment variable."""
        database_url = os.getenv("DATABASE_URL")
        if not database_url:
            raise RuntimeError("DATABASE_URL environment variable must be set")
        return Database._normalize_database_url(database_url)

    @staticmethod
    def _init_pgvector_extension(engine: Engine) -> None:
        """
        Initialize pgvector extension in the database.
        
        This must be called before creating tables that use vector columns.
        Uses autocommit mode to execute DDL statement.
        """
        try:
            logger.info("Initializing pgvector extension...")
            with engine.begin() as conn:  # begin() uses autocommit for DDL
                conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
            logger.info("pgvector extension initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize pgvector extension: {e}")
            raise RuntimeError(
                f"pgvector extension is required but could not be initialized: {e}"
            ) from e

    def _create_engine(self) -> Engine:
        """Create and configure SQLAlchemy engine."""
        database_url = Database._get_database_url()

        logger.info("Creating database engine...")
        engine = create_engine(
            database_url,
            echo=False,
            pool_pre_ping=True,  # Verify connections before using
        )
        logger.info("Database engine created successfully")

        # Initialize pgvector extension
        Database._init_pgvector_extension(engine)

        return engine

    def get_engine(self) -> Engine:
        """
        Get the database engine (lazy initialization).
        
        Creates the engine on first call, reuses on subsequent calls.
        """
        if self._engine is None:
            self._engine = self._create_engine()
        return self._engine

    def get_session_local(self) -> sessionmaker[Session]:
        """
        Get the session factory (lazy initialization).
        
        Creates the sessionmaker on first call, reuses on subsequent calls.
        """
        if self._session_local is None:
            engine = self.get_engine()
            self._session_local = sessionmaker(
                bind=engine,
                expire_on_commit=False,
            )
        return self._session_local

    def get_db(self) -> Generator[Session, None, None]:
        """
        Dependency injection function for FastAPI route handlers.
        
        Yields a database session and ensures it's closed after use.
        """
        SessionLocal = self.get_session_local()
        db = SessionLocal()
        try:
            yield db
        finally:
            db.close()

    def init_db(self) -> None:
        """
        Initialize the database by creating all tables.
        
        This function:
        1. Creates the engine (which initializes pgvector)
        2. Imports all models to register them with Base
        3. Creates all tables defined in the models
        4. Verifies that tables were created successfully
        """
        logger.info("=" * 60)
        logger.info("Initializing database")
        logger.info("=" * 60)

        # Get engine (this will also initialize pgvector)
        engine = self.get_engine()

        # Import models to register them with Base.metadata
        from . import models  # noqa: F401

        # Log tables that will be created
        table_names = list(Base.metadata.tables.keys())
        if table_names:
            logger.info(f"Tables to create: {', '.join(table_names)}")
        else:
            logger.warning("No tables found in metadata")

        # Create all tables
        logger.info("Creating database tables...")
        Base.metadata.create_all(bind=engine)

        # Verify tables were created
        with engine.connect() as conn:
            result = conn.execute(
                text("SELECT tablename FROM pg_tables WHERE schemaname = 'public'")
            )
            existing_tables = [row[0] for row in result]
            logger.info(f"Tables in database: {', '.join(existing_tables)}")

        logger.info("=" * 60)
        logger.info("Database initialization complete")
        logger.info("=" * 60)


_db = Database()


# Public API functions that delegate to the module-level instance
def get_engine() -> Engine:
    """Get the database engine."""
    return _db.get_engine()


def get_session_local() -> sessionmaker[Session]:
    """Get the session factory."""
    return _db.get_session_local()


def get_db() -> Generator[Session, None, None]:
    """
    Dependency injection function for FastAPI route handlers.
    
    Yields a database session and ensures it's closed after use.
    """
    yield from _db.get_db()


def init_db() -> None:
    """Initialize the database by creating all tables."""
    _db.init_db()

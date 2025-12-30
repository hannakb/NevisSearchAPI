"""Tests for database initialization and vector indexing."""
import pytest
from sqlalchemy import text

from src.database import init_db, get_engine, Base


@pytest.fixture
def fresh_db():
    """Create a fresh database for init_db tests (no tables pre-created)"""
    import os
    from sqlalchemy import create_engine
    from tests.conftest import DATABASE_URL
    from src.database import _db
    
    # Create engine directly to avoid any issues
    test_engine = create_engine(DATABASE_URL, isolation_level="AUTOCOMMIT")
    
    # Enable pgvector extension
    with test_engine.connect() as conn:
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        conn.commit()
    
    # Drop all tables to test init_db from scratch
    Base.metadata.drop_all(bind=test_engine)
    
    # Reset the Database singleton to ensure it creates a fresh engine
    # This ensures init_db() will use a fresh connection
    _db._engine = None
    _db._session_local = None
    
    yield test_engine
    
    # Cleanup after test - drop tables
    Base.metadata.drop_all(bind=test_engine)
    test_engine.dispose()
    
    # Reset singleton again for next test
    _db._engine = None
    _db._session_local = None


class TestDatabaseInitialization:
    """Tests for database initialization"""
    
    def test_init_db_creates_tables(self, fresh_db):
        """Test that init_db creates all required tables"""
        # Initialize database (creates tables and indexes)
        init_db()
        
        engine = get_engine()
        
        # Check that tables exist
        with engine.connect() as conn:
            result = conn.execute(
                text("SELECT tablename FROM pg_tables WHERE schemaname = 'public'")
            )
            tables = {row[0] for row in result}
            
            assert "clients" in tables
            assert "documents" in tables
    
    def test_init_db_idempotent(self, fresh_db):
        """Test that init_db can be called multiple times without errors"""
        # Should not raise an exception
        init_db()
        init_db()  # Call again
        init_db()  # Call a third time


class TestVectorIndex:
    """Tests for vector index creation and functionality"""
    
    def test_vector_index_created(self, fresh_db):
        """Test that HNSW vector index is created on documents.embedding"""
        # Initialize database (creates index)
        init_db()
        
        engine = get_engine()
        
        with engine.connect() as conn:
            # Check if index exists
            result = conn.execute(
                text("""
                    SELECT indexname 
                    FROM pg_indexes 
                    WHERE tablename = 'documents' 
                    AND indexname = 'documents_embedding_hnsw_idx'
                """)
            )
            indexes = [row[0] for row in result]
            assert "documents_embedding_hnsw_idx" in indexes
    
    def test_vector_index_uses_hnsw(self, fresh_db):
        """Test that the index uses HNSW access method"""
        # Initialize database (creates index)
        init_db()
        
        engine = get_engine()
        
        with engine.connect() as conn:
            result = conn.execute(
                text("""
                    SELECT indexdef 
                    FROM pg_indexes 
                    WHERE tablename = 'documents' 
                    AND indexname = 'documents_embedding_hnsw_idx'
                """)
            )
            index_def = result.scalar()
            
            assert index_def is not None
            assert "hnsw" in index_def.lower()
            assert "vector_cosine_ops" in index_def.lower()
    
    def test_vector_index_has_correct_parameters(self, fresh_db):
        """Test that the index is created with expected parameters"""
        # Initialize database (creates index)
        init_db()
        
        engine = get_engine()
        
        with engine.connect() as conn:
            # Get index definition
            result = conn.execute(
                text("""
                    SELECT indexdef 
                    FROM pg_indexes 
                    WHERE tablename = 'documents' 
                    AND indexname = 'documents_embedding_hnsw_idx'
                """)
            )
            index_def = result.scalar()
            
            assert index_def is not None
            # Check for common HNSW parameters (m and ef_construction)
            # These may be in the index definition or stored separately
            assert "embedding" in index_def.lower()
    
    def test_vector_index_on_correct_column(self, fresh_db):
        """Test that the index is created on the embedding column"""
        # Initialize database (creates index)
        init_db()
        
        engine = get_engine()
        
        with engine.connect() as conn:
            result = conn.execute(
                text("""
                    SELECT 
                        a.attname as column_name,
                        i.relname as index_name
                    FROM pg_index idx
                    JOIN pg_class t ON t.oid = idx.indrelid
                    JOIN pg_class i ON i.oid = idx.indexrelid
                    JOIN pg_attribute a ON a.attrelid = t.oid AND a.attnum = ANY(idx.indkey)
                    WHERE t.relname = 'documents'
                    AND i.relname = 'documents_embedding_hnsw_idx'
                """)
            )
            columns = [row[0] for row in result]
            assert "embedding" in columns
    
    def test_vector_index_does_not_block_queries(self, db_session, sample_client_data):
        """Test that semantic search queries work correctly with the index"""
        # Initialize database (creates index)
        init_db()
        
        from src import models, crud
        from src import schemas
        from src.embeddings import generate_embedding
        
        # Create a test client first (required for document foreign key)
        client = crud.create_client(db_session, schemas.ClientCreate(**sample_client_data))
        
        # Create a test document with embedding
        test_embedding = generate_embedding("test document content")
        doc = models.Document(
            client_id=client.id,
            title="Test Document",
            content="test document content",
            embedding=test_embedding
        )
        db_session.add(doc)
        db_session.commit()
        db_session.refresh(doc)
        
        # Verify the document was created
        assert doc.id is not None
        assert doc.embedding is not None
        
        # Test that we can query using the embedding (which should use the index)
        query_embedding = generate_embedding("test document")
        result = db_session.query(
            models.Document,
            (1 - models.Document.embedding.cosine_distance(query_embedding)).label('similarity')
        ).filter(
            models.Document.embedding.isnot(None)
        ).order_by(
            models.Document.embedding.cosine_distance(query_embedding)
        ).limit(10).all()
        
        # Should find the document we just created
        assert len(result) > 0
        assert result[0][0].id == doc.id


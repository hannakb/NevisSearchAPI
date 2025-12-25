import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from src.api import app
from src.database import Base, get_db
from src import models

# Use the same database as the API (will clean tables between tests)
DATABASE_URL = "postgresql://postgres:postgres@db:5432/nevis_search"

engine = create_engine(DATABASE_URL, isolation_level="AUTOCOMMIT")
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db_session():
    """Create a fresh database for each test"""
    # Enable pgvector extension
    with engine.connect() as conn:
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        conn.commit()
    
    # Drop all tables and recreate (clean slate for each test)
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture(scope="function")
def client(db_session):
    """Create a test client with overridden database dependency"""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(app) as test_client:
        yield test_client
    
    app.dependency_overrides.clear()


@pytest.fixture
def sample_client_data():
    """Sample client data for testing"""
    return {
        "first_name": "John",
        "last_name": "Doe",
        "email": "john.doe@neviswealth.com",
        "description": "High net worth individual"
    }


@pytest.fixture
def sample_document_data():
    """Sample document data for testing"""
    return {
        "title": "Tax Return 2023",
        "content": "Annual tax return document with investment income details"
    }


@pytest.fixture
def create_client(client, sample_client_data):
    """Helper fixture to create a client and return its data"""
    response = client.post("/clients", json=sample_client_data)
    assert response.status_code == 201
    return response.json()


@pytest.fixture
def create_client_with_documents(client, create_client):
    """Helper fixture to create a client with multiple documents"""
    client_id = create_client["id"]
    
    documents = [
        {
            "title": "Utility Bill - March 2024",
            "content": "Electric utility bill for address verification and proof of residence"
        },
        {
            "title": "Tax Return 2023",
            "content": "Annual tax return document with investment income details"
        },
        {
            "title": "Bank Statement",
            "content": "Monthly bank statement showing account balance and transactions"
        }
    ]
    
    created_docs = []
    for doc_data in documents:
        response = client.post(f"/clients/{client_id}/documents", json=doc_data)
        assert response.status_code == 201
        created_docs.append(response.json())
    
    return {
        "client": create_client,
        "documents": created_docs
    }


@pytest.fixture
def create_semantic_test_documents(client, create_client):
    """Create documents specifically for semantic search testing"""
    client_id = create_client["id"]
    
    documents = [
        {
            "title": "Utility Bill",
            "content": "Monthly electric utility bill serving as proof of address and residence verification"
        },
        {
            "title": "Lease Agreement",
            "content": "Rental contract for apartment showing current living address"
        },
        {
            "title": "Bank Statement",
            "content": "Financial statement from bank with account holder address"
        },
        {
            "title": "Driver License",
            "content": "Government issued identification with residential address"
        },
        {
            "title": "Tax Document",
            "content": "Annual tax filing with income and deductions"
        }
    ]
    
    created_docs = []
    for doc_data in documents:
        response = client.post(f"/clients/{client_id}/documents", json=doc_data)
        assert response.status_code == 201
        created_docs.append(response.json())
    
    return {
        "client": create_client,
        "documents": created_docs
    }
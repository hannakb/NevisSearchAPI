import pytest

class TestCreateDocument:
    """Tests for creating documents"""
    
    def test_create_document_success(self, client, create_client, sample_document_data):
        """Test successful document creation"""
        client_id = create_client["id"]
        response = client.post(f"/clients/{client_id}/documents", json=sample_document_data)
        
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == sample_document_data["title"]
        assert data["content"] == sample_document_data["content"]
        assert data["client_id"] == client_id
        assert "id" in data
        assert "created_at" in data
    
    def test_create_document_client_not_found(self, client, sample_document_data):
        """Test creating document for non-existent client fails"""
        response = client.post("/clients/non-existent-id/documents", json=sample_document_data)
        assert response.status_code == 404
    
    def test_create_document_missing_required_fields(self, client, create_client):
        """Test creating document without required fields fails"""
        client_id = create_client["id"]
        invalid_data = {"title": "Only Title"}  # Missing content
        response = client.post(f"/clients/{client_id}/documents", json=invalid_data)
        assert response.status_code == 422
    
    def test_create_multiple_documents_same_client(self, client, create_client):
        """Test creating multiple documents for same client"""
        client_id = create_client["id"]
        
        doc1 = {"title": "Doc 1", "content": "Content 1"}
        doc2 = {"title": "Doc 2", "content": "Content 2"}
        
        response1 = client.post(f"/clients/{client_id}/documents", json=doc1)
        response2 = client.post(f"/clients/{client_id}/documents", json=doc2)
        
        assert response1.status_code == 201
        assert response2.status_code == 201
        assert response1.json()["id"] != response2.json()["id"]


class TestGetClientDocuments:
    """Tests for retrieving client documents"""
    
    def test_get_documents_success(self, client, create_client_with_documents):
        """Test retrieving all documents for a client"""
        client_id = create_client_with_documents["client"]["id"]
        response = client.get(f"/clients/{client_id}/documents")
        
        assert response.status_code == 200
        documents = response.json()
        assert len(documents) == 3
        assert all(doc["client_id"] == client_id for doc in documents)
    
    def test_get_documents_empty_list(self, client, create_client):
        """Test retrieving documents for client with no documents"""
        client_id = create_client["id"]
        response = client.get(f"/clients/{client_id}/documents")
        
        assert response.status_code == 200
        assert response.json() == []
    
    def test_get_documents_client_not_found(self, client):
        """Test retrieving documents for non-existent client"""
        response = client.get("/clients/non-existent-id/documents")
        assert response.status_code == 404
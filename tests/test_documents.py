import pytest

class TestCreateDocument:
    """Tests for creating documents"""
    
    def test_create_document_success(self, client, create_client, sample_document_data):
        """Test successful document creation"""
        client_id = create_client["id"]
        response = client.post(f"/clients/{client_id}/documents", json=sample_document_data)
        
        assert response.status_code == 201
        data = response.json()
        # Check that all input fields match the response
        for key, value in sample_document_data.items():
            assert data[key] == value
        assert data["client_id"] == client_id
        # Check that server-generated fields are present
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


class TestCreateDocumentsBatch:
    """Tests for batch document creation"""
    
    def test_create_documents_batch_success(self, client, create_client, sample_document_data):
        """Test successful batch document creation"""
        client_id = create_client["id"]
        
        batch_data = {
            "documents": [
                {"title": "Doc 1", "content": "Content 1"},
                {"title": "Doc 2", "content": "Content 2"},
                {"title": "Doc 3", "content": "Content 3"}
            ]
        }
        
        response = client.post(f"/clients/{client_id}/documents/batch", json=batch_data)
        
        assert response.status_code == 201
        data = response.json()
        
        # Should return list of documents
        assert isinstance(data, list)
        assert len(data) == 3
        
        # Verify all documents were created correctly
        for i, doc in enumerate(data):
            assert "id" in doc
            assert "client_id" in doc
            assert doc["client_id"] == client_id
            assert doc["title"] == batch_data["documents"][i]["title"]
            assert doc["content"] == batch_data["documents"][i]["content"]
            assert "created_at" in doc
            
            # Verify all IDs are unique
            assert len(set(d["id"] for d in data)) == 3
    
    def test_create_documents_batch_single_document(self, client, create_client):
        """Test batch creation with single document"""
        client_id = create_client["id"]
        
        batch_data = {
            "documents": [
                {"title": "Single Doc", "content": "Single content"}
            ]
        }
        
        response = client.post(f"/clients/{client_id}/documents/batch", json=batch_data)
        
        assert response.status_code == 201
        data = response.json()
        assert len(data) == 1
        assert data[0]["title"] == "Single Doc"
    
    def test_create_documents_batch_client_not_found(self, client):
        """Test batch creation for non-existent client fails"""
        batch_data = {
            "documents": [
                {"title": "Doc 1", "content": "Content 1"}
            ]
        }
        
        response = client.post("/clients/non-existent-id/documents/batch", json=batch_data)
        assert response.status_code == 404
    
    def test_create_documents_batch_empty_list(self, client, create_client):
        """Test batch creation with empty documents list fails"""
        client_id = create_client["id"]
        
        batch_data = {"documents": []}
        
        response = client.post(f"/clients/{client_id}/documents/batch", json=batch_data)
        assert response.status_code == 422  # Validation error
    
    def test_create_documents_batch_too_many(self, client, create_client):
        """Test batch creation with more than max documents fails"""
        client_id = create_client["id"]
        
        # Create 101 documents (exceeds max of 100)
        batch_data = {
            "documents": [
                {"title": f"Doc {i}", "content": f"Content {i}"}
                for i in range(101)
            ]
        }
        
        response = client.post(f"/clients/{client_id}/documents/batch", json=batch_data)
        # Pydantic validation catches this first (422) before our API code (400)
        assert response.status_code == 422
    
    def test_create_documents_batch_max_allowed(self, client, create_client):
        """Test batch creation with exactly max documents succeeds"""
        client_id = create_client["id"]
        
        # Create exactly 100 documents (max allowed)
        batch_data = {
            "documents": [
                {"title": f"Doc {i}", "content": f"Content {i}"}
                for i in range(100)
            ]
        }
        
        response = client.post(f"/clients/{client_id}/documents/batch", json=batch_data)
        assert response.status_code == 201
        data = response.json()
        assert len(data) == 100
    
    def test_create_documents_batch_invalid_document(self, client, create_client):
        """Test batch creation with invalid document data fails"""
        client_id = create_client["id"]
        
        batch_data = {
            "documents": [
                {"title": "Valid Doc", "content": "Valid content"},
                {"title": "Invalid Doc"}  # Missing content
            ]
        }
        
        response = client.post(f"/clients/{client_id}/documents/batch", json=batch_data)
        assert response.status_code == 422  # Validation error
    
    def test_create_documents_batch_all_have_embeddings(self, client, create_client):
        """Test that all documents in batch have embeddings created"""
        client_id = create_client["id"]
        
        batch_data = {
            "documents": [
                {"title": "Doc 1", "content": "Content about machine learning"},
                {"title": "Doc 2", "content": "Content about artificial intelligence"},
                {"title": "Doc 3", "content": "Content about neural networks"}
            ]
        }
        
        response = client.post(f"/clients/{client_id}/documents/batch", json=batch_data)
        assert response.status_code == 201
        documents = response.json()
        
        # Verify we can search using semantic search (which requires embeddings)
        search_response = client.get(f"/search?q=machine learning&type=documents")
        assert search_response.status_code == 200
        search_results = search_response.json()["documents"]
        
        # At least one of our documents should be found
        doc_ids = [doc["id"] for doc in documents]
        found_ids = [result["id"] for result in search_results]
        assert any(doc_id in found_ids for doc_id in doc_ids)
    
    def test_create_documents_batch_isolated_per_client(self, client, sample_client_data):
        """Test that batch documents are isolated per client"""
        # Create two clients
        client1_response = client.post("/clients", json=sample_client_data)
        client1_id = client1_response.json()["id"]
        
        client2_data = {**sample_client_data, "email": "client2@example.com"}
        client2_response = client.post("/clients", json=client2_data)
        client2_id = client2_response.json()["id"]
        
        # Create batch for client 1
        batch1 = {
            "documents": [
                {"title": "Client1 Doc", "content": "Client1 content"}
            ]
        }
        response1 = client.post(f"/clients/{client1_id}/documents/batch", json=batch1)
        assert response1.status_code == 201
        doc1_id = response1.json()[0]["id"]
        
        # Create batch for client 2
        batch2 = {
            "documents": [
                {"title": "Client2 Doc", "content": "Client2 content"}
            ]
        }
        response2 = client.post(f"/clients/{client2_id}/documents/batch", json=batch2)
        assert response2.status_code == 201
        doc2_id = response2.json()[0]["id"]
        
        # Verify documents belong to correct clients
        assert response1.json()[0]["client_id"] == client1_id
        assert response2.json()[0]["client_id"] == client2_id
        
        # Verify clients can only see their own documents
        docs1 = client.get(f"/clients/{client1_id}/documents").json()["items"]
        docs2 = client.get(f"/clients/{client2_id}/documents").json()["items"]
        
        assert len(docs1) == 1
        assert len(docs2) == 1
        assert docs1[0]["id"] == doc1_id
        assert docs2[0]["id"] == doc2_id


class TestGetClientDocuments:
    """Tests for retrieving client documents"""
    
    def test_get_documents_success(self, client, create_client_with_documents):
        """Test retrieving all documents for a client"""
        client_id = create_client_with_documents["client"]["id"]
        response = client.get(f"/clients/{client_id}/documents")
        
        assert response.status_code == 200
        data = response.json()
        # Verify paginated response structure
        assert "items" in data
        assert "total" in data
        assert "offset" in data
        assert "limit" in data
        documents = data["items"]
        assert len(documents) == 3
        assert data["total"] == 3
        assert all(doc["client_id"] == client_id for doc in documents)
    
    def test_get_documents_empty_list(self, client, create_client):
        """Test retrieving documents for client with no documents"""
        client_id = create_client["id"]
        response = client.get(f"/clients/{client_id}/documents")
        
        assert response.status_code == 200
        data = response.json()
        # Verify paginated response structure
        assert "items" in data
        assert "total" in data
        assert data["total"] == 0
        assert len(data["items"]) == 0
    
    def test_get_documents_client_not_found(self, client):
        """Test retrieving documents for non-existent client"""
        response = client.get("/clients/non-existent-id/documents")
        assert response.status_code == 404
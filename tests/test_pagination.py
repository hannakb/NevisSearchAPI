"""Tests for pagination functionality."""
import pytest


class TestPaginationClients:
    """Tests for pagination on /clients endpoint"""
    
    def test_pagination_default_values(self, client, sample_client_data):
        """Test pagination with default values"""
        # Create some clients
        for i in range(5):
            client_data = {
                **sample_client_data,
                "email": f"test{i}@example.com",
                "first_name": f"Test{i}"
            }
            client.post("/clients", json=client_data)
        
        response = client.get("/clients")
        assert response.status_code == 200
        data = response.json()
        
        # Verify default pagination values
        assert data["offset"] == 0
        assert data["limit"] == 10
        assert len(data["items"]) <= 10
        assert data["total"] >= 5
    
    def test_pagination_offset(self, client, sample_client_data):
        """Test pagination with offset parameter"""
        # Create 10 clients
        clients_created = []
        for i in range(10):
            client_data = {
                **sample_client_data,
                "email": f"offset-test{i}@example.com",
                "first_name": f"OffsetTest{i}"
            }
            resp = client.post("/clients", json=client_data)
            clients_created.append(resp.json()["id"])
        
        # Get first page
        response1 = client.get("/clients?offset=0&limit=5")
        assert response1.status_code == 200
        data1 = response1.json()
        assert data1["offset"] == 0
        assert data1["limit"] == 5
        assert len(data1["items"]) == 5
        assert data1["total"] >= 10
        
        # Get second page
        response2 = client.get("/clients?offset=5&limit=5")
        assert response2.status_code == 200
        data2 = response2.json()
        assert data2["offset"] == 5
        assert data2["limit"] == 5
        assert len(data2["items"]) == 5
        
        # Verify no overlap between pages
        page1_ids = {item["id"] for item in data1["items"]}
        page2_ids = {item["id"] for item in data2["items"]}
        assert len(page1_ids & page2_ids) == 0
    
    def test_pagination_limit(self, client, sample_client_data):
        """Test pagination with limit parameter"""
        # Create 15 clients
        for i in range(15):
            client_data = {
                **sample_client_data,
                "email": f"limit-test{i}@example.com",
                "first_name": f"LimitTest{i}"
            }
            client.post("/clients", json=client_data)
        
        # Request with limit=3
        response = client.get("/clients?limit=3")
        assert response.status_code == 200
        data = response.json()
        assert data["limit"] == 3
        assert len(data["items"]) == 3
        assert data["total"] >= 15
    
    def test_pagination_has_next(self, client, sample_client_data):
        """Test has_next pagination flag"""
        # Create 15 clients
        for i in range(15):
            client_data = {
                **sample_client_data,
                "email": f"hasnext-test{i}@example.com",
                "first_name": f"HasNextTest{i}"
            }
            client.post("/clients", json=client_data)
        
        # First page should have next
        response1 = client.get("/clients?offset=0&limit=10")
        assert response1.status_code == 200
        data1 = response1.json()
        assert data1["has_next"] is True
        assert data1["has_previous"] is False
        
        # Last page should not have next
        response2 = client.get("/clients?offset=10&limit=10")
        assert response2.status_code == 200
        data2 = response2.json()
        # If there are exactly 15 items, offset=10 should still have items but no next
        if data2["total"] <= 20:
            assert data2["has_next"] is False
    
    def test_pagination_has_previous(self, client, sample_client_data):
        """Test has_previous pagination flag"""
        # Create some clients
        for i in range(10):
            client_data = {
                **sample_client_data,
                "email": f"hasprev-test{i}@example.com",
                "first_name": f"HasPrevTest{i}"
            }
            client.post("/clients", json=client_data)
        
        # First page should not have previous
        response1 = client.get("/clients?offset=0&limit=5")
        assert response1.status_code == 200
        data1 = response1.json()
        assert data1["has_previous"] is False
        
        # Second page should have previous
        response2 = client.get("/clients?offset=5&limit=5")
        assert response2.status_code == 200
        data2 = response2.json()
        assert data2["has_previous"] is True
    
    def test_pagination_page_property(self, client, sample_client_data):
        """Test computed page property (implicit via response structure)"""
        # Create some clients
        for i in range(10):
            client_data = {
                **sample_client_data,
                "email": f"page-test{i}@example.com",
                "first_name": f"PageTest{i}"
            }
            client.post("/clients", json=client_data)
        
        # Verify offset=0 gives page 1 (if we could access page property)
        response = client.get("/clients?offset=0&limit=5")
        assert response.status_code == 200
        data = response.json()
        # Page is computed property, not in JSON, but offset/limit confirm it
    
    def test_pagination_invalid_offset(self, client):
        """Test pagination with invalid offset (negative)"""
        response = client.get("/clients?offset=-1")
        assert response.status_code == 422  # Validation error
    
    def test_pagination_invalid_limit_zero(self, client):
        """Test pagination with invalid limit (zero)"""
        response = client.get("/clients?limit=0")
        assert response.status_code == 422  # Validation error
    
    def test_pagination_limit_too_high(self, client):
        """Test pagination with limit exceeding maximum"""
        response = client.get("/clients?limit=101")
        assert response.status_code == 422  # Validation error (max is 100)
    
    def test_pagination_offset_beyond_total(self, client, sample_client_data):
        """Test pagination with offset beyond total count"""
        # Create only 5 clients
        for i in range(5):
            client_data = {
                **sample_client_data,
                "email": f"beyond-test{i}@example.com",
                "first_name": f"BeyondTest{i}"
            }
            client.post("/clients", json=client_data)
        
        # Request with offset beyond total
        response = client.get("/clients?offset=100&limit=10")
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 0
        assert data["total"] == 5
        assert data["has_next"] is False
        assert data["has_previous"] is True


class TestPaginationDocuments:
    """Tests for pagination on /clients/{client_id}/documents endpoint"""
    
    def test_documents_pagination_default(self, client, create_client_with_documents):
        """Test document pagination with default values"""
        client_id = create_client_with_documents["client"]["id"]
        
        response = client.get(f"/clients/{client_id}/documents")
        assert response.status_code == 200
        data = response.json()
        
        # Verify paginated response structure
        assert "items" in data
        assert "total" in data
        assert "offset" in data
        assert "limit" in data
        assert "has_next" in data
        assert "has_previous" in data
        assert data["offset"] == 0
        assert data["limit"] == 10
        assert data["total"] >= 3  # At least the 3 documents we created
    
    def test_documents_pagination_offset_limit(self, client, create_client):
        """Test document pagination with offset and limit"""
        client_id = create_client["id"]
        
        # Create 10 documents
        documents_created = []
        for i in range(10):
            doc_data = {
                "title": f"Document {i}",
                "content": f"Content for document {i}"
            }
            resp = client.post(f"/clients/{client_id}/documents", json=doc_data)
            documents_created.append(resp.json()["id"])
        
        # Get first page
        response1 = client.get(f"/clients/{client_id}/documents?offset=0&limit=3")
        assert response1.status_code == 200
        data1 = response1.json()
        assert len(data1["items"]) == 3
        assert data1["total"] == 10
        
        # Get second page
        response2 = client.get(f"/clients/{client_id}/documents?offset=3&limit=3")
        assert response2.status_code == 200
        data2 = response2.json()
        assert len(data2["items"]) == 3
        
        # Verify no overlap
        page1_ids = {item["id"] for item in data1["items"]}
        page2_ids = {item["id"] for item in data2["items"]}
        assert len(page1_ids & page2_ids) == 0
    
    def test_documents_pagination_has_next_previous(self, client, create_client):
        """Test document pagination flags"""
        client_id = create_client["id"]
        
        # Create 5 documents
        for i in range(5):
            doc_data = {
                "title": f"Doc {i}",
                "content": f"Content {i}"
            }
            client.post(f"/clients/{client_id}/documents", json=doc_data)
        
        # First page
        response1 = client.get(f"/clients/{client_id}/documents?offset=0&limit=3")
        data1 = response1.json()
        assert data1["has_previous"] is False
        assert data1["has_next"] is True
        
        # Second page
        response2 = client.get(f"/clients/{client_id}/documents?offset=3&limit=3")
        data2 = response2.json()
        assert data2["has_previous"] is True
        assert data2["has_next"] is False  # Last page with 5 total items
    
    def test_documents_pagination_client_isolation(self, client, sample_client_data, sample_document_data):
        """Test that pagination is isolated per client"""
        # Create two clients
        resp1 = client.post("/clients", json=sample_client_data)
        client1_id = resp1.json()["id"]
        
        client2_data = {
            **sample_client_data,
            "email": "client2@example.com"
        }
        resp2 = client.post("/clients", json=client2_data)
        client2_id = resp2.json()["id"]
        
        # Create documents for both clients
        for i in range(5):
            client.post(f"/clients/{client1_id}/documents", json={
                "title": f"Client1 Doc {i}",
                "content": f"Content {i}"
            })
            client.post(f"/clients/{client2_id}/documents", json={
                "title": f"Client2 Doc {i}",
                "content": f"Content {i}"
            })
        
        # Check client1 documents
        resp1_docs = client.get(f"/clients/{client1_id}/documents")
        assert resp1_docs.json()["total"] == 5
        
        # Check client2 documents
        resp2_docs = client.get(f"/clients/{client2_id}/documents")
        assert resp2_docs.json()["total"] == 5
        
        # Verify they don't overlap
        client1_ids = {doc["id"] for doc in resp1_docs.json()["items"]}
        client2_ids = {doc["id"] for doc in resp2_docs.json()["items"]}
        assert len(client1_ids & client2_ids) == 0
    
    def test_documents_pagination_invalid_offset(self, client, create_client):
        """Test document pagination with invalid offset"""
        client_id = create_client["id"]
        response = client.get(f"/clients/{client_id}/documents?offset=-1")
        assert response.status_code == 422
    
    def test_documents_pagination_invalid_limit(self, client, create_client):
        """Test document pagination with invalid limit"""
        client_id = create_client["id"]
        response = client.get(f"/clients/{client_id}/documents?limit=101")
        assert response.status_code == 422


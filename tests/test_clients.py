import pytest

class TestCreateClient:
    """Tests for creating clients"""
    
    def test_create_client_success(self, client, sample_client_data):
        """Test successful client creation"""
        response = client.post("/clients", json=sample_client_data)
        
        assert response.status_code == 201
        data = response.json()
        assert data["first_name"] == sample_client_data["first_name"]
        assert data["last_name"] == sample_client_data["last_name"]
        assert data["email"] == sample_client_data["email"]
        assert data["description"] == sample_client_data["description"]
        assert "id" in data
        assert "created_at" in data
    
    def test_create_client_duplicate_email(self, client, sample_client_data):
        """Test creating client with duplicate email fails"""
        # Create first client
        response1 = client.post("/clients", json=sample_client_data)
        assert response1.status_code == 201
        
        # Try to create second client with same email
        response2 = client.post("/clients", json=sample_client_data)
        assert response2.status_code == 400
        assert "already exists" in response2.json()["detail"].lower()
    
    def test_create_client_missing_required_fields(self, client):
        """Test creating client without required fields fails"""
        invalid_data = {"first_name": "John"}  # Missing last_name and email
        response = client.post("/clients", json=invalid_data)
        assert response.status_code == 422  # Validation error
    
    def test_create_client_invalid_email(self, client):
        """Test creating client with invalid email fails"""
        invalid_data = {
            "first_name": "John",
            "last_name": "Doe",
            "email": "not-an-email"
        }
        response = client.post("/clients", json=invalid_data)
        assert response.status_code == 422
    
    def test_create_client_without_description(self, client):
        """Test creating client without optional description"""
        data = {
            "first_name": "Jane",
            "last_name": "Smith",
            "email": "jane.smith@example.com"
        }
        response = client.post("/clients", json=data)
        assert response.status_code == 201
        assert response.json()["description"] is None


class TestGetClient:
    """Tests for retrieving clients"""
    
    def test_get_client_success(self, client, create_client):
        """Test successful client retrieval with all fields"""
        client_id = create_client["id"]
        response = client.get(f"/clients/{client_id}")
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify all required fields are present
        assert "id" in data
        assert "first_name" in data
        assert "last_name" in data
        assert "email" in data
        assert "description" in data
        assert "created_at" in data
        
        # Verify field values match the created client
        assert data["id"] == client_id
        assert data["first_name"] == create_client["first_name"]
        assert data["last_name"] == create_client["last_name"]
        assert data["email"] == create_client["email"]
        assert data["description"] == create_client["description"]
        
        # Verify created_at is a valid datetime string (Pydantic serializes to ISO format)
        assert isinstance(data["created_at"], str)
        assert len(data["created_at"]) > 0
        # Optionally verify it can be parsed as datetime
        from datetime import datetime
        try:
            datetime.fromisoformat(data["created_at"].replace('Z', '+00:00'))
        except ValueError:
            # If parsing fails, at least verify it looks like a datetime string
            assert 'T' in data["created_at"] or ' ' in data["created_at"]
        
        # Verify ID format (should start with "client-")
        assert data["id"].startswith("client-")
    
    def test_get_client_with_none_description(self, client):
        """Test retrieving client with None description"""
        # Create client without description
        client_data = {
            "first_name": "Jane",
            "last_name": "Smith",
            "email": "jane.smith@example.com"
        }
        create_response = client.post("/clients", json=client_data)
        assert create_response.status_code == 201
        
        client_id = create_response.json()["id"]
        response = client.get(f"/clients/{client_id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["description"] is None
        assert data["first_name"] == "Jane"
        assert data["last_name"] == "Smith"
    
    def test_get_client_not_found(self, client):
        """Test retrieving non-existent client"""
        response = client.get("/clients/non-existent-id")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()
    
    def test_get_client_invalid_id_format(self, client):
        """Test retrieving client with invalid ID format"""
        # Test with non-existent but valid-format ID
        fake_id = "client-00000000-0000-0000-0000-000000000000"
        response = client.get(f"/clients/{fake_id}")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()
        
        # Test with very long ID
        long_id = "client-" + "a" * 100
        response = client.get(f"/clients/{long_id}")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()
        
        # Test with invalid format (not starting with "client-")
        invalid_id = "invalid-format-id"
        response = client.get(f"/clients/{invalid_id}")
        assert response.status_code == 404


class TestListClients:
    """Tests for listing clients"""
    
    def test_list_clients_success(self, client, create_client):
        """Test successful client listing"""
        response = client.get("/clients")
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify response is a list
        assert isinstance(data, list)
        assert len(data) > 0
        
        # Verify the created client is in the list
        client_ids = [c["id"] for c in data]
        assert create_client["id"] in client_ids
        
        # Verify all items have required fields
        for client_item in data:
            assert "id" in client_item
            assert "first_name" in client_item
            assert "last_name" in client_item
            assert "email" in client_item
            assert "description" in client_item
            assert "created_at" in client_item
    
    def test_list_clients_empty(self, client):
        """Test listing clients when database is empty"""
        response = client.get("/clients")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        # May be empty or contain clients from other tests depending on test isolation
    
    def test_list_clients_multiple(self, client, sample_client_data):
        """Test listing multiple clients"""
        # Create multiple clients
        clients_created = []
        for i in range(3):
            client_data = {
                **sample_client_data,
                "email": f"client{i}@example.com",
                "first_name": f"Client{i}"
            }
            response = client.post("/clients", json=client_data)
            assert response.status_code == 201
            clients_created.append(response.json())
        
        # List all clients
        response = client.get("/clients")
        assert response.status_code == 200
        data = response.json()
        
        # Verify all created clients are in the list
        client_ids = [c["id"] for c in data]
        for created_client in clients_created:
            assert created_client["id"] in client_ids
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
        """Test successful client retrieval"""
        client_id = create_client["id"]
        response = client.get(f"/clients/{client_id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == client_id
        assert data["email"] == create_client["email"]
    
    def test_get_client_not_found(self, client):
        """Test retrieving non-existent client"""
        response = client.get("/clients/non-existent-id")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()
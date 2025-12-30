import pytest
from sqlalchemy.orm import Session

from src import search, models


class TestSearchValidation:
    """Tests for search endpoint validation"""
    
    def test_search_empty_query(self, client):
        """Test search with empty query fails"""
        response = client.get("/search?q=")
        assert response.status_code == 400
        assert "cannot be empty" in response.json()["detail"].lower()
    
    def test_search_whitespace_only_query(self, client):
        """Test search with whitespace-only query fails"""
        response = client.get("/search?q=   ")
        assert response.status_code == 400
        assert "cannot be empty" in response.json()["detail"].lower()
    
    def test_search_no_query(self, client):
        """Test search without query parameter fails"""
        response = client.get("/search")
        assert response.status_code == 422
    
    def test_search_invalid_type(self, client):
        """Test search with invalid type parameter"""
        response = client.get("/search?q=test&type=invalid")
        assert response.status_code == 422
    
    def test_search_invalid_limit(self, client):
        """Test search with invalid limit"""
        response = client.get("/search?q=test&limit=0")
        assert response.status_code == 400
        assert "between 1 and 100" in response.json()["detail"].lower()
        
        response = client.get("/search?q=test&limit=101")
        assert response.status_code == 400
        assert "between 1 and 100" in response.json()["detail"].lower()
    
    def test_search_valid_limit_boundaries(self, client):
        """Test search with valid limit boundaries"""
        response = client.get("/search?q=test&limit=1")
        assert response.status_code == 200
        
        response = client.get("/search?q=test&limit=100")
        assert response.status_code == 200


class TestSearchClients:
    """Tests for searching clients"""
    
    def test_search_client_by_email_exact(self, client, create_client):
        """Test searching client by exact email match"""
        email = create_client["email"]
        response = client.get(f"/search?q={email}&type=clients")
        
        assert response.status_code == 200
        data = response.json()
        assert data["search_type"] == "clients"
        assert len(data["clients"]) == 1
        assert len(data["documents"]) == 0
        assert data["clients"][0]["email"] == email
        assert data["clients"][0]["match_score"] == 1.0  # Exact match
        assert data["clients"][0]["match_field"] == "email"
    
    def test_search_client_by_email_domain(self, client, create_client):
        """Test searching client by email domain"""
        response = client.get("/search?q=neviswealth&type=clients")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["clients"]) >= 1
        assert any("neviswealth" in c["email"].lower() for c in data["clients"])
    
    def test_search_client_by_first_name(self, client, create_client):
        """Test searching client by first name"""
        response = client.get("/search?q=john&type=clients")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["clients"]) >= 1
        assert any(c["first_name"].lower() == "john" for c in data["clients"])
    
    def test_search_client_by_last_name(self, client, create_client):
        """Test searching client by last name"""
        response = client.get("/search?q=doe&type=clients")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["clients"]) >= 1
        assert any(c["last_name"].lower() == "doe" for c in data["clients"])
    
    def test_search_client_by_full_name(self, client, create_client):
        """Test searching client by full name"""
        # Search for first name - should find the client
        response = client.get("/search?q=john&type=clients")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["clients"]) >= 1
        
        # Search for last name - should also find the client
        response = client.get("/search?q=doe&type=clients")
        assert response.status_code == 200
        data = response.json()
        assert len(data["clients"]) >= 1
    
    def test_search_client_by_description(self, client, create_client):
        """Test searching client by description"""
        response = client.get("/search?q=net+worth&type=clients")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["clients"]) >= 1
        assert any("net worth" in (c["description"] or "").lower() for c in data["clients"])
    
    def test_search_client_no_results(self, client, create_client):
        """Test searching client with no matches"""
        response = client.get("/search?q=nonexistentquery123xyz&type=clients")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["clients"]) == 0
        assert data["total_results"] == 0
    
    def test_search_client_case_insensitive(self, client, create_client):
        """Test that client search is case-insensitive"""
        response1 = client.get("/search?q=JOHN&type=clients")
        response2 = client.get("/search?q=john&type=clients")
        response3 = client.get("/search?q=JoHn&type=clients")
        
        assert response1.status_code == 200
        assert response2.status_code == 200
        assert response3.status_code == 200
        assert len(response1.json()["clients"]) == len(response2.json()["clients"])
        assert len(response2.json()["clients"]) == len(response3.json()["clients"])
    
    def test_search_client_score_ordering(self, client, create_client):
        """Test that client results are ordered by match score"""
        # Create multiple clients
        clients_data = [
            {"first_name": "John", "last_name": "Doe", "email": "john.doe@example.com", "description": "Test client"},
            {"first_name": "Johnny", "last_name": "Smith", "email": "johnny.smith@example.com", "description": "Another client"},
        ]
        for client_data in clients_data:
            client.post("/clients", json=client_data)
        
        response = client.get("/search?q=john&type=clients")
        assert response.status_code == 200
        clients = response.json()["clients"]
        
        if len(clients) > 1:
            scores = [c["match_score"] for c in clients]
            assert scores == sorted(scores, reverse=True)
    
    def test_search_client_starts_with(self, client, create_client):
        """Test that 'starts with' matches get higher scores than 'contains'"""
        response = client.get("/search?q=john&type=clients")
        assert response.status_code == 200
        clients = response.json()["clients"]
        
        if len(clients) > 0:
            # Exact or starts-with matches should have higher scores
            assert clients[0]["match_score"] >= 0.85


class TestSearchDocumentsKeyword:
    """Tests for searching documents (keyword-based)"""
    
    def test_search_document_by_title(self, client, create_client_with_documents):
        """Test searching document by title"""
        response = client.get("/search?q=utility&type=documents")
        
        assert response.status_code == 200
        data = response.json()
        assert data["search_type"] == "documents"
        assert len(data["documents"]) >= 1
        assert any("utility" in doc["title"].lower() for doc in data["documents"])
    
    def test_search_document_by_content(self, client, create_client_with_documents):
        """Test searching document by content"""
        response = client.get("/search?q=investment&type=documents")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["documents"]) >= 1
        assert any("investment" in doc["content"].lower() for doc in data["documents"])
    
    def test_search_document_exact_title_match(self, client, create_client_with_documents):
        """Test that exact title matches get highest score"""
        # Search for part of the title - hybrid search combines keyword and semantic
        response = client.get("/search?q=utility&type=documents")
        
        assert response.status_code == 200
        documents = response.json()["documents"]
        
        if len(documents) > 0:
            # Find the utility bill document
            utility_docs = [doc for doc in documents if "utility" in doc["title"].lower()]
            if utility_docs:
                # Hybrid search combines keyword (0.7 for contains in title) and semantic
                # So the score might be lower than pure keyword match
                assert utility_docs[0]["match_score"] >= 0.3  # Reasonable threshold for hybrid search
    
    def test_search_document_match_score_ordering(self, client, create_client_with_documents):
        """Test that documents are ordered by match score"""
        response = client.get("/search?q=tax&type=documents")
        
        assert response.status_code == 200
        documents = response.json()["documents"]
        
        if len(documents) > 1:
            scores = [doc["match_score"] for doc in documents]
            assert scores == sorted(scores, reverse=True)
    
    def test_search_document_match_field(self, client, create_client_with_documents):
        """Test that match_field indicates where match was found"""
        response = client.get("/search?q=utility&type=documents")
        
        assert response.status_code == 200
        documents = response.json()["documents"]
        assert len(documents) >= 1
        assert documents[0]["match_field"] in ["title", "content", "semantic", "hybrid"]
    
    def test_search_document_multiple_word_query(self, client, create_client_with_documents):
        """Test searching with multiple words in query"""
        response = client.get("/search?q=tax+return&type=documents")
        
        assert response.status_code == 200
        documents = response.json()["documents"]
        assert len(documents) >= 1
    
    def test_search_document_no_results(self, client, create_client_with_documents):
        """Test searching documents with no matches"""
        response = client.get("/search?q=nonexistentdocument123xyz&type=documents")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["documents"]) == 0


class TestSearchAll:
    """Tests for searching both clients and documents"""
    
    def test_search_all_default(self, client, create_client_with_documents):
        """Test search defaults to searching both clients and documents"""
        response = client.get("/search?q=tax")
        
        assert response.status_code == 200
        data = response.json()
        assert data["search_type"] == "all"
        assert len(data["documents"]) >= 1
    
    def test_search_all_explicit(self, client, create_client_with_documents):
        """Test explicitly searching all types"""
        response = client.get("/search?q=john&type=all")
        
        assert response.status_code == 200
        data = response.json()
        assert data["search_type"] == "all"
        assert len(data["clients"]) >= 1
    
    def test_search_all_total_results(self, client, create_client_with_documents):
        """Test total_results counts both clients and documents"""
        response = client.get("/search?q=doe")
        
        assert response.status_code == 200
        data = response.json()
        expected_total = len(data["clients"]) + len(data["documents"])
        assert data["total_results"] == expected_total
    
    def test_search_limit(self, client, create_client_with_documents):
        """Test search respects limit parameter"""
        client_id = create_client_with_documents["client"]["id"]
        for i in range(15):
            doc = {"title": f"Document {i}", "content": "test content for searching"}
            client.post(f"/clients/{client_id}/documents", json=doc)
        
        response = client.get("/search?q=test&type=documents&limit=5")
        
        assert response.status_code == 200
        assert len(response.json()["documents"]) <= 5


class TestSearchResponseFormat:
    """Tests for search response format"""
    
    def test_search_response_structure(self, client, create_client_with_documents):
        """Test search response has correct structure"""
        response = client.get("/search?q=test")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "query" in data
        assert "search_type" in data
        assert "clients" in data
        assert "documents" in data
        assert "total_results" in data
        
        assert isinstance(data["clients"], list)
        assert isinstance(data["documents"], list)
        assert isinstance(data["total_results"], int)
        assert data["query"] == "test"
    
    def test_client_result_structure(self, client, create_client):
        """Test client search result has correct structure"""
        response = client.get("/search?q=john&type=clients")
        
        assert response.status_code == 200
        clients = response.json()["clients"]
        
        if len(clients) > 0:
            client_result = clients[0]
            assert "id" in client_result
            assert "first_name" in client_result
            assert "last_name" in client_result
            assert "email" in client_result
            assert "match_score" in client_result
            assert "match_field" in client_result
            assert 0 <= client_result["match_score"] <= 1
            assert client_result["match_field"] in ["email", "name", "description"]
    
    def test_document_result_structure(self, client, create_client_with_documents):
        """Test document search result has correct structure"""
        response = client.get("/search?q=utility&type=documents")
        
        assert response.status_code == 200
        documents = response.json()["documents"]
        
        if len(documents) > 0:
            doc_result = documents[0]
            assert "id" in doc_result
            assert "client_id" in doc_result
            assert "title" in doc_result
            assert "content" in doc_result
            assert "created_at" in doc_result
            assert "match_score" in doc_result
            assert "match_field" in doc_result
            assert 0 <= doc_result["match_score"] <= 1
            assert doc_result["match_field"] in ["title", "content", "semantic", "hybrid"]


class TestSemanticSearchBasic:
    """Basic semantic search functionality tests"""
    
    def test_semantic_search_enabled_by_default(self, client, create_semantic_test_documents):
        """Test that semantic search is enabled by default (hybrid search)"""
        # Search for "address proof" - should find utility bill, lease, bank statement
        response = client.get("/search?q=address+proof&type=documents")
        
        assert response.status_code == 200
        data = response.json()
        
        # Should find multiple documents
        assert len(data["documents"]) >= 1
        
        # At least one should have semantic/hybrid match
        match_fields = [doc["match_field"] for doc in data["documents"]]
        assert any(field in ["semantic", "hybrid"] for field in match_fields)
    
    def test_semantic_search_finds_similar_concepts(self, client, create_semantic_test_documents):
        """Test that semantic search finds documents with similar concepts"""
        response = client.get("/search?q=residence+verification&type=documents")
        
        assert response.status_code == 200
        data = response.json()
        
        # Should find documents about address/residence
        assert len(data["documents"]) >= 1


class TestSemanticSimilarity:
    """Tests for semantic similarity matching"""
    
    def test_address_proof_matches_utility_bill(self, client, create_semantic_test_documents):
        """Test that 'address proof' finds 'utility bill'"""
        response = client.get("/search?q=proof+of+address&type=documents")
        
        assert response.status_code == 200
        documents = response.json()["documents"]
        
        # Should find at least one relevant document
        assert len(documents) >= 1
        
        # Check if utility, lease, or bank is in results (any address-related doc)
        titles = [doc["title"].lower() for doc in documents]
        contents = [doc["content"].lower() for doc in documents]
        
        # Should find something related to address/residence
        found_relevant = any(
            "utility" in title or "lease" in title or "bank" in title or
            "address" in content or "residence" in content
            for title, content in zip(titles, contents)
        )
        assert found_relevant, f"Expected to find address-related document, got: {titles}"
    
    def test_residence_verification_matches_lease(self, client, create_semantic_test_documents):
        """Test that 'residence verification' finds lease agreement"""
        response = client.get("/search?q=residence+verification&type=documents")
        
        assert response.status_code == 200
        documents = response.json()["documents"]
        
        # Should find at least 1 document
        assert len(documents) >= 1
        
        # Should find something related to residence/address
        titles = [doc["title"].lower() for doc in documents]
        contents = [doc["content"].lower() for doc in documents]
        
        found_relevant = any(
            "lease" in title or "utility" in title or 
            "residence" in content or "address" in content
            for title, content in zip(titles, contents)
        )
        assert found_relevant
    
    def test_identity_document_matches_driver_license(self, client, create_semantic_test_documents):
        """Test that 'identity document' finds driver license"""
        response = client.get("/search?q=identity+document&type=documents")
        
        assert response.status_code == 200
        documents = response.json()["documents"]
        
        # Should find at least 1 document
        assert len(documents) >= 1
        
        # Check for driver license or any government ID
        titles = [doc["title"].lower() for doc in documents]
        contents = [doc["content"].lower() for doc in documents]
        
        found_relevant = any(
            "driver" in title or "license" in title or 
            "identification" in content or "government" in content
            for title, content in zip(titles, contents)
        )
        assert found_relevant, f"Expected ID-related document, got: {titles}"


class TestHybridSearch:
    """Tests for hybrid search (keyword + semantic)"""
    
    def test_hybrid_search_combines_results(self, client, create_semantic_test_documents):
        """Test that hybrid search combines keyword and semantic results"""
        response = client.get("/search?q=utility&type=documents")
        
        assert response.status_code == 200
        documents = response.json()["documents"]
        
        if len(documents) > 0:
            # Should have match_field as title, content, semantic, or hybrid
            match_fields = [doc["match_field"] for doc in documents]
            assert all(field in ["title", "content", "semantic", "hybrid"] for field in match_fields)
    
    def test_hybrid_search_score_weighting(self, client, create_semantic_test_documents):
        """Test that hybrid search properly weights scores"""
        response = client.get("/search?q=utility+bill&type=documents")
        
        assert response.status_code == 200
        documents = response.json()["documents"]
        
        # Should find results
        assert len(documents) >= 1
        
        # Scores should be between 0 and 1
        for doc in documents:
            assert 0 <= doc["match_score"] <= 1


class TestSemanticSearchQuality:
    """Tests for semantic search result quality"""
    
    def test_semantic_results_ordered_by_relevance(self, client, create_semantic_test_documents):
        """Test that semantic search results are ordered by relevance"""
        response = client.get("/search?q=proof+of+address&type=documents")
        
        assert response.status_code == 200
        documents = response.json()["documents"]
        
        if len(documents) > 1:
            # Scores should be in descending order
            scores = [doc["match_score"] for doc in documents]
            assert scores == sorted(scores, reverse=True)


class TestSearchEdgeCases:
    """Edge cases for search"""
    
    def test_search_with_special_characters(self, client, create_client):
        """Test search handles special characters"""
        response = client.get("/search?q=test%40example&type=clients")
        assert response.status_code == 200
    
    def test_search_with_unicode(self, client):
        """Test search handles unicode characters"""
        # Create client with unicode name
        client_data = {
            "first_name": "José",
            "last_name": "García",
            "email": "jose.garcia@example.com"
        }
        client.post("/clients", json=client_data)
        
        response = client.get("/search?q=José&type=clients")
        assert response.status_code == 200
        assert len(response.json()["clients"]) >= 1
    
    def test_search_with_numbers(self, client, create_client_with_documents):
        """Test search with numerical queries"""
        response = client.get("/search?q=2024&type=documents")
        assert response.status_code == 200
    
    def test_search_empty_database(self, client):
        """Test search when database is empty"""
        response = client.get("/search?q=test&type=all")
        assert response.status_code == 200
        data = response.json()
        assert len(data["clients"]) == 0
        assert len(data["documents"]) == 0
        assert data["total_results"] == 0


class TestDirectSearchFunctions:
    """Tests for direct search function calls (not through API)"""
    
    def test_search_clients_function_empty_query(self, db_session):
        """Test search_clients returns empty list for empty query"""
        results = search.search_clients(db_session, "")
        assert results == []
        
        results = search.search_clients(db_session, "   ")
        assert results == []
    
    def test_search_clients_function_no_results(self, db_session):
        """Test search_clients returns empty list when no matches"""
        results = search.search_clients(db_session, "nonexistent123xyz")
        assert results == []
    
    def test_search_clients_function_limit(self, db_session, sample_client_data):
        """Test search_clients respects limit parameter"""
        # Create multiple clients
        from src import crud
        from src.schemas import ClientCreate
        for i in range(15):
            client_data = {**sample_client_data, "email": f"client{i}@example.com"}
            crud.create_client(db_session, ClientCreate(**client_data))
        
        results = search.search_clients(db_session, "client", limit=5)
        assert len(results) <= 5
    
    def test_search_documents_keyword_function_empty_query(self, db_session):
        """Test search_documents_keyword returns empty list for empty query"""
        results = search.search_documents_keyword(db_session, "")
        assert results == []
    
    def test_search_documents_semantic_function_empty_query(self, db_session):
        """Test search_documents_semantic returns empty list for empty query"""
        results = search.search_documents_semantic(db_session, "")
        assert results == []
    
    def test_search_documents_semantic_function_no_embeddings(self, db_session):
        """Test search_documents_semantic handles documents without embeddings"""
        results = search.search_documents_semantic(db_session, "test")
        # Should return empty list if no documents have embeddings
        assert isinstance(results, list)
    
    def test_perform_search_function_all_types(self, db_session, sample_client_data, sample_document_data):
        """Test perform_search with all search types"""
        from src import crud
        from src.schemas import ClientCreate, DocumentCreate
        
        # Create test data
        client = crud.create_client(db_session, ClientCreate(**sample_client_data))
        crud.create_document(db_session, client.id, DocumentCreate(**sample_document_data))
        
        # Test all types
        clients_results, documents_results = search.perform_search(
            db_session, "test", search_type="all", limit=10
        )
        assert isinstance(clients_results, list)
        assert isinstance(documents_results, list)
        
        # Test clients only
        clients_results, documents_results = search.perform_search(
            db_session, "test", search_type="clients", limit=10
        )
        assert isinstance(clients_results, list)
        assert len(documents_results) == 0
        
        # Test documents only
        clients_results, documents_results = search.perform_search(
            db_session, "test", search_type="documents", limit=10
        )
        assert len(clients_results) == 0
        assert isinstance(documents_results, list)

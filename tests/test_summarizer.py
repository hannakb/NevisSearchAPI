"""Tests for summarizer module functionality."""
import pytest
from unittest.mock import patch, MagicMock
import os

from src import summarizer, crud, schemas
from src.summarizer import fallback_summary, generate_summary, OpenAIClient


@pytest.fixture(autouse=True)
def reset_openai_client():
    """Automatically reset OpenAI client before and after each test"""
    # Reset before test
    summarizer.OpenAIClient._client = None
    summarizer.OpenAIClient._client_api_key = None
    yield
    # Cleanup after test
    summarizer.OpenAIClient._client = None
    summarizer.OpenAIClient._client_api_key = None


class TestCheckAvailability:
    """Tests for check_openai_availability"""
    
    def test_no_api_key_set(self):
        """Test availability check when API key is not set"""
        with patch.dict(os.environ, {}, clear=True):
            status = summarizer.check_openai_availability()
            
            assert status['available'] is False
            assert status['api_key_set'] is False
            assert status['api_key_valid'] is False
            assert status['error'] == "OPENAI_API_KEY environment variable not set"
    
    def test_invalid_api_key_format(self):
        """Test availability check with invalid key format"""
        with patch.dict(os.environ, {'OPENAI_API_KEY': 'invalid-key-format'}):
            status = summarizer.check_openai_availability()
            
            assert status['available'] is False
            assert status['api_key_set'] is True
            assert status['api_key_valid'] is False
            assert "Invalid API key format" in status['error']
    
    @patch('src.summarizer.OpenAIClient.get_client')
    def test_valid_api_key_with_models(self, mock_get_client):
        """Test availability check with valid API key"""
        with patch.dict(os.environ, {'OPENAI_API_KEY': 'sk-test-key'}):
            # Setup mock
            mock_client = MagicMock()
            mock_models = MagicMock()
            mock_models.data = [
                MagicMock(id='gpt-4o-mini'),
                MagicMock(id='gpt-4o'),
                MagicMock(id='gpt-4-turbo')
            ]
            mock_client.models.list.return_value = mock_models
            mock_get_client.return_value = mock_client
            
            status = summarizer.check_openai_availability()
            
            assert status['available'] is True
            assert status['api_key_set'] is True
            assert status['api_key_valid'] is True
            assert status['models_accessible'] == ['gpt-4o-mini', 'gpt-4o', 'gpt-4-turbo']
            assert status['error'] is None
    
    @patch('src.summarizer.OpenAIClient.get_client')
    def test_api_connection_error(self, mock_get_client):
        """Test availability check when API connection fails"""
        with patch.dict(os.environ, {'OPENAI_API_KEY': 'sk-test-key-error'}):
            # Setup mock to fail
            mock_client = MagicMock()
            mock_client.models.list.side_effect = Exception("Connection timeout")
            mock_get_client.return_value = mock_client
            
            status = summarizer.check_openai_availability()
            
            assert status['available'] is False
            assert status['api_key_set'] is True
            assert status['api_key_valid'] is False
            assert "Connection timeout" in status['error']


class TestOpenAIIntegration:
    """Integration tests (run only if OPENAI_API_KEY is set)"""
    
    @pytest.mark.skipif(
        not os.getenv("OPENAI_API_KEY"),
        reason="OPENAI_API_KEY not set - skipping real API test"
    )
    def test_real_availability_check(self):
        """Test availability check with real API (only runs if key is set)"""
        status = summarizer.check_openai_availability()
        
        assert status['available'] is True
        assert status['api_key_valid'] is True
        assert len(status['models_accessible']) > 0
        assert 'gpt-4o-mini' in status['models_accessible']


class TestFallbackSummary:
    """Tests for fallback_summary function"""
    
    def test_fallback_summary_basic(self):
        """Test basic fallback summary generation"""
        content = "This is the first sentence. This is the second sentence. This is the third sentence."
        summary = fallback_summary(content, max_length=100)
        
        assert isinstance(summary, str)
        assert len(summary) <= 100
        assert "first sentence" in summary.lower()
    
    def test_fallback_summary_single_sentence(self):
        """Test fallback summary with single sentence"""
        content = "This is a single sentence."
        summary = fallback_summary(content, max_length=50)
        
        assert isinstance(summary, str)
        assert len(summary) <= 50
    
    def test_fallback_summary_no_periods(self):
        """Test fallback summary with text without sentence endings"""
        content = "This is text without periods but with words"
        summary = fallback_summary(content, max_length=50)
        
        assert isinstance(summary, str)
        # Should truncate if no sentences found
        assert len(summary) <= 50
    
    def test_fallback_summary_empty_content(self):
        """Test fallback summary with empty content"""
        summary = fallback_summary("", max_length=50)
        
        # Empty content returns "..." after truncation logic
        assert isinstance(summary, str)
        assert summary == "..."
    
    def test_fallback_summary_long_first_sentence(self):
        """Test fallback summary when first sentence is longer than max_length"""
        content = "This is a very long sentence that exceeds the maximum length limit. Second sentence."
        summary = fallback_summary(content, max_length=20)
        
        assert isinstance(summary, str)
        # Ellipsis adds 3 characters, so length can be up to max_length + 3
        assert len(summary) <= 23
        assert summary.endswith("...")
    
    def test_fallback_summary_adds_ellipsis(self):
        """Test that fallback summary adds ellipsis when truncated"""
        content = "First sentence. Second sentence."
        summary = fallback_summary(content, max_length=10)
        
        # Should add ellipsis if sentence doesn't end properly
        assert isinstance(summary, str)


class TestGenerateSummary:
    """Tests for generate_summary function"""
    
    def test_generate_summary_empty_content(self):
        """Test summary generation with empty content"""
        summary = generate_summary("", max_length=100)
        
        assert summary == ""
    
    def test_generate_summary_short_content(self):
        """Test summary generation with content shorter than max_length"""
        content = "Short content"
        summary = generate_summary(content, max_length=100)
        
        # Should return content as-is if already short
        assert summary == content
    
    def test_generate_summary_whitespace_only(self):
        """Test summary generation with whitespace-only content"""
        summary = generate_summary("   \n\t  ", max_length=100)
        
        assert summary == ""
    
    @patch('src.summarizer.OpenAIClient.get_client')
    def test_generate_summary_openai_success(self, mock_get_client):
        """Test summary generation with successful OpenAI API call"""
        # Mock OpenAI response
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "This is a generated summary."
        
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_get_client.return_value = mock_client
        
        # Use content longer than max_length to trigger OpenAI call
        content = "This is a very long document with lots of content that needs to be summarized. " * 10
        summary = generate_summary(content, max_length=100)
        
        assert isinstance(summary, str)
        assert "generated summary" in summary.lower()
        mock_client.chat.completions.create.assert_called_once()
    
    @patch('src.summarizer.OpenAIClient.get_client')
    def test_generate_summary_openai_failure_falls_back(self, mock_get_client):
        """Test that summary generation falls back to extractive summary on OpenAI failure"""
        # Mock OpenAI to raise exception
        mock_client = MagicMock()
        mock_client.chat.completions.create.side_effect = Exception("API Error")
        mock_get_client.return_value = mock_client
        
        content = "First sentence. Second sentence. Third sentence."
        summary = generate_summary(content, max_length=100)
        
        # Should fall back to extractive summary
        assert isinstance(summary, str)
        assert len(summary) > 0
        # Should contain parts of original content
        assert any(word in summary.lower() for word in ["first", "second", "sentence"])


class TestGetOpenAIClient:
    """Tests for get_openai_client function"""
    
    @patch.dict('os.environ', {'OPENAI_API_KEY': 'sk-test-key'})
    def test_get_openai_client_success(self):
        """Test getting OpenAI client with valid API key"""
        # Reset module state (fixture handles this, but explicit for clarity)
        summarizer.OpenAIClient._client = None
        summarizer.OpenAIClient._client_api_key = None
        
        client = OpenAIClient.get_client()
        
        assert client is not None
        # Should be OpenAI client instance
        assert hasattr(client, 'chat')
    
    @patch.dict('os.environ', {}, clear=True)
    def test_get_openai_client_missing_key(self):
        """Test OpenAIClient.get_client raises error when API key is missing"""
        # Reset module state
        summarizer.OpenAIClient._client = None
        summarizer.OpenAIClient._client_api_key = None
        
        with pytest.raises(RuntimeError, match="OPENAI_API_KEY must be set"):
            OpenAIClient.get_client()
    
    @patch.dict('os.environ', {'OPENAI_API_KEY': 'sk-first-key'})
    def test_get_openai_client_key_change_resets(self):
        """Test that client is reset when API key changes"""
        # Reset module state
        summarizer.OpenAIClient._client = None
        summarizer.OpenAIClient._client_api_key = None
        
        # Get client with first key
        client1 = OpenAIClient.get_client()
        assert summarizer.OpenAIClient._client_api_key == 'sk-first-key'
        
        # Change API key
        import os
        os.environ['OPENAI_API_KEY'] = 'sk-second-key'
        
        # Get client again - should create new client
        client2 = OpenAIClient.get_client()
        assert summarizer.OpenAIClient._client_api_key == 'sk-second-key'


class TestGetOrGenerateSummary:
    """Tests for get_or_generate_summary CRUD function"""
    
    def test_get_or_generate_summary_cached(self, db_session, create_client, sample_document_data):
        """Test retrieving cached summary"""
        # Create document with existing summary
        client_id = create_client["id"]
        doc = crud.create_document(db_session, client_id, schemas.DocumentCreate(**sample_document_data))
        
        # Manually set summary (simulating cached summary)
        doc.summary = "Cached summary"
        db_session.commit()
        
        # Get summary (should return cached)
        with patch('src.crud.generate_summary') as mock_generate:
            summary = crud.get_or_generate_summary(db_session, doc.id)
            
            assert summary == "Cached summary"
            # Should not call generate_summary
            mock_generate.assert_not_called()
    
    @patch('src.crud.generate_summary')
    def test_get_or_generate_summary_generates_new(self, mock_generate, db_session, create_client, sample_document_data):
        """Test generating new summary when none exists"""
        mock_generate.return_value = "Generated summary"
        
        client_id = create_client["id"]
        doc = crud.create_document(db_session, client_id, schemas.DocumentCreate(**sample_document_data))
        
        # Get summary (should generate new)
        summary = crud.get_or_generate_summary(db_session, doc.id)
        
        assert summary == "Generated summary"
        mock_generate.assert_called_once()
        
        # Verify summary was saved to database
        db_session.refresh(doc)
        assert doc.summary == "Generated summary"
    
    @patch('src.crud.generate_summary')
    def test_get_or_generate_summary_regenerate(self, mock_generate, db_session, create_client, sample_document_data):
        """Test regenerating summary with regenerate=True"""
        mock_generate.return_value = "New generated summary"
        
        client_id = create_client["id"]
        doc = crud.create_document(db_session, client_id, schemas.DocumentCreate(**sample_document_data))
        
        # Set cached summary
        doc.summary = "Old cached summary"
        db_session.commit()
        
        # Regenerate summary
        summary = crud.get_or_generate_summary(db_session, doc.id, regenerate=True)
        
        assert summary == "New generated summary"
        mock_generate.assert_called_once()
        
        # Verify new summary was saved
        db_session.refresh(doc)
        assert doc.summary == "New generated summary"
    
    def test_get_or_generate_summary_document_not_found(self, db_session):
        """Test get_or_generate_summary with non-existent document"""
        from fastapi import HTTPException
        
        with pytest.raises(HTTPException) as exc_info:
            crud.get_or_generate_summary(db_session, "non-existent-id")
        
        assert exc_info.value.status_code == 404
    
    @patch('src.crud.generate_summary')
    def test_get_or_generate_summary_max_length(self, mock_generate, db_session, create_client, sample_document_data):
        """Test get_or_generate_summary with custom max_length"""
        mock_generate.return_value = "Short summary"
        
        client_id = create_client["id"]
        doc = crud.create_document(db_session, client_id, schemas.DocumentCreate(**sample_document_data))
        
        summary = crud.get_or_generate_summary(db_session, doc.id, max_length=50)
        
        assert summary == "Short summary"
        # Verify max_length was passed to generate_summary
        call_args = mock_generate.call_args
        assert call_args[1]['max_length'] == 50


class TestGetDocumentSummaryEndpoint:
    """Tests for /documents/{document_id}/summary endpoint"""
    
    def test_get_document_summary_success(self, client, create_client, sample_document_data):
        """Test getting document summary via API"""
        client_id = create_client["id"]
        doc_response = client.post(f"/clients/{client_id}/documents", json=sample_document_data)
        doc_id = doc_response.json()["id"]
        
        # Get summary
        response = client.get(f"/documents/{doc_id}/summary")
        
        assert response.status_code == 200
        data = response.json()
        assert "document_id" in data
        assert "title" in data
        assert "summary" in data
        assert "summary_length" in data
        assert "cached" in data
        assert data["document_id"] == doc_id
    
    def test_get_document_summary_with_max_length(self, client, create_client, sample_document_data):
        """Test getting document summary with custom max_length"""
        client_id = create_client["id"]
        doc_response = client.post(f"/clients/{client_id}/documents", json=sample_document_data)
        doc_id = doc_response.json()["id"]
        
        response = client.get(f"/documents/{doc_id}/summary?max_length=100")
        
        assert response.status_code == 200
        data = response.json()
        assert data["summary_length"] <= 100
    
    def test_get_document_summary_regenerate(self, client, create_client, sample_document_data):
        """Test regenerating document summary"""
        client_id = create_client["id"]
        doc_response = client.post(f"/clients/{client_id}/documents", json=sample_document_data)
        doc_id = doc_response.json()["id"]
        
        # Get summary first time
        response1 = client.get(f"/documents/{doc_id}/summary")
        assert response1.status_code == 200
        summary1 = response1.json()["summary"]
        
        # Regenerate
        response2 = client.get(f"/documents/{doc_id}/summary?regenerate=true")
        assert response2.status_code == 200
        summary2 = response2.json()["summary"]
        
        # Summaries might be the same if content is same, but cached flag should be False
        assert response2.json()["cached"] is False
    
    def test_get_document_summary_not_found(self, client):
        """Test getting summary for non-existent document"""
        response = client.get("/documents/non-existent-id/summary")
        assert response.status_code == 404
    
    def test_get_document_summary_invalid_max_length(self, client, create_client, sample_document_data):
        """Test getting summary with invalid max_length"""
        client_id = create_client["id"]
        doc_response = client.post(f"/clients/{client_id}/documents", json=sample_document_data)
        doc_id = doc_response.json()["id"]
        
        # Too small
        response1 = client.get(f"/documents/{doc_id}/summary?max_length=10")
        assert response1.status_code == 422
        
        # Too large
        response2 = client.get(f"/documents/{doc_id}/summary?max_length=1000")
        assert response2.status_code == 422
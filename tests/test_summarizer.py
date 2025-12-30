import pytest
from unittest.mock import patch, MagicMock
import os

import src.summarizer


@pytest.fixture(autouse=True)
def reset_openai_client():
    """Automatically reset OpenAI client before and after each test"""
    # Reset before test
    src.summarizer._client = None
    src.summarizer._client_api_key = None
    yield
    # Cleanup after test
    src.summarizer._client = None
    src.summarizer._client_api_key = None


class TestCheckAvailability:
    """Tests for check_openai_availability"""
    
    def test_no_api_key_set(self):
        """Test availability check when API key is not set"""
        with patch.dict(os.environ, {}, clear=True):
            status = src.summarizer.check_openai_availability()
            
            assert status['available'] is False
            assert status['api_key_set'] is False
            assert status['api_key_valid'] is False
            assert status['error'] == "OPENAI_API_KEY environment variable not set"
    
    def test_invalid_api_key_format(self):
        """Test availability check with invalid key format"""
        with patch.dict(os.environ, {'OPENAI_API_KEY': 'invalid-key-format'}):
            status = src.summarizer.check_openai_availability()
            
            assert status['available'] is False
            assert status['api_key_set'] is True
            assert status['api_key_valid'] is False
            assert "Invalid API key format" in status['error']
    
    @patch('src.summarizer.get_openai_client')
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
            
            status = src.summarizer.check_openai_availability()
            
            assert status['available'] is True
            assert status['api_key_set'] is True
            assert status['api_key_valid'] is True
            assert status['models_accessible'] == ['gpt-4o-mini', 'gpt-4o', 'gpt-4-turbo']
            assert status['error'] is None
    
    @patch('src.summarizer.get_openai_client')
    def test_api_connection_error(self, mock_get_client):
        """Test availability check when API connection fails"""
        with patch.dict(os.environ, {'OPENAI_API_KEY': 'sk-test-key-error'}):
            # Setup mock to fail
            mock_client = MagicMock()
            mock_client.models.list.side_effect = Exception("Connection timeout")
            mock_get_client.return_value = mock_client
            
            status = src.summarizer.check_openai_availability()
            
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
        status = src.summarizer.check_openai_availability()
        
        assert status['available'] is True
        assert status['api_key_valid'] is True
        assert len(status['models_accessible']) > 0
        assert 'gpt-4o-mini' in status['models_accessible']
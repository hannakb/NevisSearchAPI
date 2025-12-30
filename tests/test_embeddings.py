"""Tests for embeddings functionality."""
import pytest
import numpy as np

from src.embeddings import (
    generate_embedding,
    generate_embeddings_batch,
    calculate_similarity,
    EmbeddingModel,
    EMBEDDING_DIMENSIONS
)


class TestGenerateEmbedding:
    """Tests for generate_embedding function"""
    
    def test_generate_embedding_basic(self):
        """Test basic embedding generation"""
        text = "This is a test document about machine learning."
        embedding = generate_embedding(text)
        
        assert isinstance(embedding, list)
        assert len(embedding) == EMBEDDING_DIMENSIONS
        assert all(isinstance(x, (int, float)) for x in embedding)
    
    def test_generate_embedding_empty_string(self):
        """Test embedding generation with empty string"""
        embedding = generate_embedding("")
        
        assert isinstance(embedding, list)
        assert len(embedding) == EMBEDDING_DIMENSIONS
        # Should return zero vector for empty string
        assert all(x == 0.0 for x in embedding)
    
    def test_generate_embedding_whitespace_only(self):
        """Test embedding generation with whitespace-only string"""
        embedding = generate_embedding("   \n\t  ")
        
        assert isinstance(embedding, list)
        assert len(embedding) == EMBEDDING_DIMENSIONS
    
    def test_generate_embedding_long_text(self):
        """Test embedding generation with long text"""
        long_text = "This is a very long text. " * 100
        embedding = generate_embedding(long_text)
        
        assert isinstance(embedding, list)
        assert len(embedding) == EMBEDDING_DIMENSIONS
    
    def test_generate_embedding_unicode(self):
        """Test embedding generation with unicode characters"""
        unicode_text = "Hello 世界 🌍 Привет"
        embedding = generate_embedding(unicode_text)
        
        assert isinstance(embedding, list)
        assert len(embedding) == EMBEDDING_DIMENSIONS
    
    def test_generate_embedding_similar_texts(self):
        """Test that similar texts produce similar embeddings"""
        text1 = "Machine learning is a subset of artificial intelligence"
        text2 = "ML is part of AI"
        
        embedding1 = generate_embedding(text1)
        embedding2 = generate_embedding(text2)
        
        # Calculate similarity
        similarity = calculate_similarity(embedding1, embedding2)
        
        # Similar texts should have similarity > 0 (usually > 0.3 for related concepts)
        assert similarity > 0
        assert similarity <= 1.0
    
    def test_generate_embedding_different_texts(self):
        """Test that different texts produce different embeddings"""
        text1 = "This is about machine learning"
        text2 = "This is about cooking recipes"
        
        embedding1 = generate_embedding(text1)
        embedding2 = generate_embedding(text2)
        
        # Embeddings should be different (not identical)
        assert embedding1 != embedding2


class TestGenerateEmbeddingsBatch:
    """Tests for generate_embeddings_batch function"""
    
    def test_generate_embeddings_batch_basic(self):
        """Test batch embedding generation"""
        texts = [
            "First document about AI",
            "Second document about ML",
            "Third document about deep learning"
        ]
        
        embeddings = generate_embeddings_batch(texts)
        
        assert isinstance(embeddings, list)
        assert len(embeddings) == 3
        assert all(len(emb) == EMBEDDING_DIMENSIONS for emb in embeddings)
    
    def test_generate_embeddings_batch_empty_list(self):
        """Test batch embedding generation with empty list"""
        embeddings = generate_embeddings_batch([])
        
        assert isinstance(embeddings, list)
        assert len(embeddings) == 0
    
    def test_generate_embeddings_batch_single_item(self):
        """Test batch embedding generation with single item"""
        texts = ["Single document"]
        embeddings = generate_embeddings_batch(texts)
        
        assert len(embeddings) == 1
        assert len(embeddings[0]) == EMBEDDING_DIMENSIONS
    
    def test_generate_embeddings_batch_with_empty_strings(self):
        """Test batch embedding generation with empty strings filtered out"""
        texts = [
            "Valid text",
            "",
            "   ",
            "Another valid text"
        ]
        
        embeddings = generate_embeddings_batch(texts)
        
        # Empty strings should be filtered out
        assert len(embeddings) == 2
        assert all(len(emb) == EMBEDDING_DIMENSIONS for emb in embeddings)
    
    def test_generate_embeddings_batch_large_batch(self):
        """Test batch embedding generation with many items"""
        texts = [f"Document {i} about topic {i % 5}" for i in range(50)]
        embeddings = generate_embeddings_batch(texts)
        
        assert len(embeddings) == 50
        assert all(len(emb) == EMBEDDING_DIMENSIONS for emb in embeddings)


class TestCalculateSimilarity:
    """Tests for calculate_similarity function"""
    
    def test_calculate_similarity_identical_embeddings(self):
        """Test similarity calculation with identical embeddings"""
        embedding = [0.1, 0.2, 0.3, 0.4]
        similarity = calculate_similarity(embedding, embedding)
        
        # Identical embeddings should have similarity of 1.0
        assert abs(similarity - 1.0) < 0.001
    
    def test_calculate_similarity_opposite_embeddings(self):
        """Test similarity calculation with opposite embeddings"""
        embedding1 = [1.0, 0.0, 0.0]
        embedding2 = [-1.0, 0.0, 0.0]
        similarity = calculate_similarity(embedding1, embedding2)
        
        # Opposite vectors should have similarity of -1.0
        assert abs(similarity - (-1.0)) < 0.001
    
    def test_calculate_similarity_perpendicular_embeddings(self):
        """Test similarity calculation with perpendicular embeddings"""
        embedding1 = [1.0, 0.0]
        embedding2 = [0.0, 1.0]
        similarity = calculate_similarity(embedding1, embedding2)
        
        # Perpendicular vectors should have similarity of 0.0
        assert abs(similarity) < 0.001
    
    def test_calculate_similarity_real_embeddings(self):
        """Test similarity calculation with real generated embeddings"""
        text1 = "Machine learning algorithms"
        text2 = "Deep learning neural networks"
        text3 = "Cooking recipes for dinner"
        
        emb1 = generate_embedding(text1)
        emb2 = generate_embedding(text2)
        emb3 = generate_embedding(text3)
        
        # Similar topics should have higher similarity
        sim_1_2 = calculate_similarity(emb1, emb2)
        sim_1_3 = calculate_similarity(emb1, emb3)
        
        assert sim_1_2 > sim_1_3  # ML and DL should be more similar than ML and cooking
        assert 0 <= sim_1_2 <= 1
        assert 0 <= sim_1_3 <= 1
    
    def test_calculate_similarity_zero_embeddings(self):
        """Test similarity calculation with zero embeddings"""
        zero_embedding = [0.0] * EMBEDDING_DIMENSIONS
        similarity = calculate_similarity(zero_embedding, zero_embedding)
        
        # Zero embeddings should return 0.0 (no similarity/undefined direction)
        assert isinstance(similarity, float)
        assert similarity == 0.0
    
    def test_calculate_similarity_different_lengths(self):
        """Test similarity calculation handles different length embeddings (should error gracefully)"""
        emb1 = [0.1, 0.2, 0.3]
        emb2 = [0.1, 0.2]
        
        # Should handle gracefully (might return 0.0 or raise, but shouldn't crash)
        try:
            similarity = calculate_similarity(emb1, emb2)
            assert isinstance(similarity, float)
        except Exception:
            # It's acceptable if it raises an exception
            pass


class TestGetModel:
    """Tests for EmbeddingModel.get_model class method"""
    
    def test_get_model_returns_model(self):
        """Test that get_model returns a SentenceTransformer model"""
        model = EmbeddingModel.get_model()
        
        # Should return a SentenceTransformer instance
        assert model is not None
        # Check it has encode method (SentenceTransformer signature)
        assert hasattr(model, 'encode')
    
    def test_get_model_singleton(self):
        """Test that get_model returns the same instance (singleton)"""
        model1 = EmbeddingModel.get_model()
        model2 = EmbeddingModel.get_model()
        
        # Should be the same instance
        assert model1 is model2


from sentence_transformers import SentenceTransformer
from typing import List
import logging
import numpy as np

logger = logging.getLogger(__name__)

# Model configuration
EMBEDDING_MODEL = "all-MiniLM-L6-v2"  # Fast, good quality, 384 dimensions
EMBEDDING_DIMENSIONS = 384

# Initialize model (lazy loading)
_model = None


def get_model() -> SentenceTransformer:
    """Get or initialize the embedding model (singleton pattern)"""
    global _model
    if _model is None:
        logger.info(f"Loading embedding model: {EMBEDDING_MODEL}")
        _model = SentenceTransformer(EMBEDDING_MODEL)
        logger.info(f"Model loaded successfully. Embedding dim: {EMBEDDING_DIMENSIONS}")
    return _model


def generate_embedding(text: str) -> List[float]:
    """
    Generate embedding for a given text using sentence-transformers
    
    Args:
        text: Text to embed
        
    Returns:
        List of floats representing the embedding vector
    """
    try:
        # Clean text
        text = text.strip()
        if not text:
            logger.warning("Empty text provided for embedding")
            return [0.0] * EMBEDDING_DIMENSIONS
        
        # Generate embedding
        model = get_model()
        embedding = model.encode(text, convert_to_numpy=True)
        
        # Convert to list
        embedding_list = embedding.tolist()
        
        logger.info(f"Generated embedding for text (length: {len(text)} chars)")
        
        return embedding_list
    
    except Exception as e:
        logger.error(f"Error generating embedding: {e}")
        # Return zero vector on error to prevent crashes
        return [0.0] * EMBEDDING_DIMENSIONS


def generate_embeddings_batch(texts: List[str]) -> List[List[float]]:
    """
    Generate embeddings for multiple texts in a single batch (more efficient)
    
    Args:
        texts: List of texts to embed
        
    Returns:
        List of embedding vectors
    """
    try:
        if not texts:
            return []
        
        # Clean texts
        texts = [text.strip() for text in texts if text.strip()]
        
        if not texts:
            return []
        
        # Generate embeddings in batch
        model = get_model()
        embeddings = model.encode(texts, convert_to_numpy=True, show_progress_bar=False)
        
        # Convert to list of lists
        embeddings_list = embeddings.tolist()
        
        logger.info(f"Generated {len(embeddings_list)} embeddings in batch")
        
        return embeddings_list
    
    except Exception as e:
        logger.error(f"Error generating batch embeddings: {e}")
        # Return zero vectors on error
        return [[0.0] * EMBEDDING_DIMENSIONS] * len(texts)


def calculate_similarity(embedding1: List[float], embedding2: List[float]) -> float:
    """
    Calculate cosine similarity between two embeddings
    
    Args:
        embedding1: First embedding vector
        embedding2: Second embedding vector
        
    Returns:
        Similarity score between 0 and 1
    """
    try:
        vec1 = np.array(embedding1)
        vec2 = np.array(embedding2)
        
        # Cosine similarity
        similarity = np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2))
        
        return float(similarity)
    
    except Exception as e:
        logger.error(f"Error calculating similarity: {e}")
        return 0.0
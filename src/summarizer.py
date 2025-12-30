import os
from openai import OpenAI
import logging
import re
from typing import Optional

logger = logging.getLogger(__name__)


# OpenAI configuration constants
class OpenAIConfig:
    """OpenAI API configuration constants"""
    MODEL = "gpt-4o-mini"
    MAX_TOKENS = 100
    TEMPERATURE = 0.3
    API_KEY_PREFIX = "sk-"
    CHARS_PER_WORD = 5  # Average characters per word for estimation


_client: Optional[OpenAI] = None
_client_api_key: Optional[str] = None  # Track which API key the client was created with


def get_openai_client() -> OpenAI:
    """Get or create OpenAI client (singleton)"""
    global _client, _client_api_key
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY must be set at runtime")
    
    # Reset client if API key changed
    if _client is not None and _client_api_key != api_key:
        _client = None
        _client_api_key = None
    
    if _client is None:
        _client = OpenAI(api_key=api_key)
        _client_api_key = api_key
    return _client


def check_openai_availability() -> dict:
    """
    Check OpenAI API availability and return detailed status.
    
    Returns:
        dict with status information:
        {
            'available': bool,
            'api_key_set': bool,
            'api_key_valid': bool,
            'models_accessible': list or None,
            'error': str or None
        }
    """
    status = {
        'available': False,
        'api_key_set': False,
        'api_key_valid': False,
        'models_accessible': None,
        'error': None
    }
    
    # Check if API key is set
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        status['error'] = "OPENAI_API_KEY environment variable not set"
        return status
    
    status['api_key_set'] = True
    
    # Validate API key format
    if not api_key.startswith(OpenAIConfig.API_KEY_PREFIX):
        status['error'] = f"Invalid API key format (should start with '{OpenAIConfig.API_KEY_PREFIX}')"
        return status
    
    # Try to connect to API
    try:
        client = get_openai_client()
        
        # List models (free API call that doesn't consume tokens)
        models_response = client.models.list()
        models = [model.id for model in models_response.data]
        
        status['api_key_valid'] = True
        status['models_accessible'] = models
        status['available'] = True
        
        logger.info(f"OpenAI API available. Found {len(models)} models.")
        
    except Exception as e:
        status['error'] = str(e)
        logger.error(f"OpenAI API validation failed: {e}")
    
    return status


def validate_openai_api_key() -> bool:
    """
    Validate that OpenAI API key is valid by making a free API call.
    
    Uses the /v1/models endpoint which:
    - Doesn't consume tokens (free)
    - Verifies API key is valid
    - Checks network connectivity
    
    Returns:
        True if API key is valid, False otherwise
    """
    status = check_openai_availability()
    return status['available']


def generate_summary(content: str, max_length: int = 200) -> str:
    """
    Generate a concise, informative summary using OpenAI GPT-4o-mini
    
    Args:
        content: Document content to summarize
        max_length: Approximate maximum summary length in characters (default: 200)
    
    Returns:
        AI-generated summary string
    """
    if not content or not content.strip():
        return ""
    
    content = content.strip()
    
    # If content is already short, return as-is
    if len(content) <= max_length:
        return content
    
    try:
        # Calculate approximate word limit
        word_limit = max_length // OpenAIConfig.CHARS_PER_WORD
        
        # Call OpenAI API for summarization
        client = get_openai_client()
        response = client.chat.completions.create(
            model=OpenAIConfig.MODEL,
            messages=[
                {
                    "role": "system",
                    "content": (
                        f"You are a professional document summarizer. Create concise, "
                        f"informative summaries of approximately {word_limit} words. "
                        f"Focus on the key information, purpose, and important details "
                        f"of the document. Write in a clear, professional tone."
                    )
                },
                {
                    "role": "user",
                    "content": f"Summarize this document:\n\n{content}"
                }
            ],
            max_tokens=OpenAIConfig.MAX_TOKENS,
            temperature=OpenAIConfig.TEMPERATURE
        )
        
        summary = response.choices[0].message.content.strip()
        
        # Remove any quotation marks that the model might add
        summary = summary.strip('"\'')
        
        logger.info(
            f"Generated OpenAI summary: {len(summary)} chars "
            f"from {len(content)} chars of content"
        )
        
        return summary
    
    except Exception as e:
        logger.error(f"Error generating summary with OpenAI: {e}")
        
        # Fallback to simple extractive summary if API fails
        logger.warning("Falling back to extractive summary")
        return fallback_summary(content, max_length)


def fallback_summary(content: str, max_length: int = 200) -> str:
    """
    Simple extractive fallback summary (first sentences)
    Used if OpenAI API fails or is unavailable
    
    Args:
        content: Document content
        max_length: Maximum length in characters
    
    Returns:
        Extractive summary
    """
    # Split into sentences
    sentences = re.split(r'(?<=[.!?])\s+', content)
    sentences = [s.strip() for s in sentences if s.strip()]
    
    if not sentences:
        # No sentences found, just truncate
        return content[:max_length].rsplit(' ', 1)[0] + "..."
    
    # Build summary from first 2 sentences
    summary = ""
    for sentence in sentences[:2]:
        test_summary = summary + " " + sentence if summary else sentence
        
        if len(test_summary) > max_length:
            if not summary:
                # First sentence is too long, truncate it
                summary = sentence[:max_length].rsplit(' ', 1)[0] + "..."
            break
        
        summary = test_summary
    
    if summary and not summary[-1] in '.!?':
        summary += "..."
    
    return summary.strip()

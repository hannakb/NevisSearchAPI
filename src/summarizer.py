import os
from openai import OpenAI
import logging
import re

logger = logging.getLogger(__name__)

_client = None

def get_openai_client() -> OpenAI:
    global _client
    if _client is None:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise RuntimeError("OPENAI_API_KEY must be set at runtime")
        _client = OpenAI(api_key=api_key)
    return _client


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
        # Calculate approximate word limit (avg 5 chars per word)
        word_limit = max_length // 5
        
        # Call OpenAI API for summarization
        client = get_openai_client()
        response = client.chat.completions.create(
            model="gpt-4o-mini",  # Fast, cheap, good quality
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
            max_tokens=100,  # Limit response length
            temperature=0.3  # Lower temperature for more focused, consistent summaries
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


# Alias for backwards compatibility
generate_summary_smart = generate_summary

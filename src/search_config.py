"""Search configuration constants and enums."""
from enum import IntEnum
from dataclasses import dataclass


class SearchScore(IntEnum):
    """Search relevance scores - easily adjustable for fine-tuning search quality."""
    # Exact matches (highest priority)
    EXACT_EMAIL = 1000
    EXACT_NAME = 950
    EXACT_FULL_NAME = 950
    
    # Starts with matches
    STARTS_WITH_EMAIL = 900
    STARTS_WITH_NAME = 850
    
    # Contains matches
    CONTAINS_EMAIL = 700
    CONTAINS_NAME = 650
    CONTAINS_DESCRIPTION = 500


@dataclass
class HybridSearchWeights:
    """Weights for hybrid search combination (keyword + semantic)."""
    KEYWORD_WEIGHT: float = 0.4
    SEMANTIC_WEIGHT: float = 0.6


# Semantic search configuration
SEMANTIC_SIMILARITY_THRESHOLD = 0.3  # Minimum similarity score to include in results

# Search limits
SEARCH_DEFAULT_LIMIT = 10
SEARCH_MAX_LIMIT = 100
SEARCH_MIN_LIMIT = 1

# Score normalization
SCORE_NORMALIZATION_FACTOR = 1000.0  # Divide raw scores by this to get 0-1 range


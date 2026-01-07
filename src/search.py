from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from sqlalchemy import or_, func, case, and_
from typing import List, Tuple
from fastapi import HTTPException, status

from . import models
from .embeddings import generate_embedding
from .search_config import (
    SearchScore,
    HybridSearchWeights,
    SEMANTIC_SIMILARITY_THRESHOLD,
    SCORE_NORMALIZATION_FACTOR,
    SEARCH_DEFAULT_LIMIT
)

def search_clients(
    db: Session, 
    query: str, 
    limit: int = SEARCH_DEFAULT_LIMIT
) -> List[Tuple[models.Client, float, str]]:
    """
    Search clients by email, name, or description with database-level scoring
    Returns list of (client, score, match_field) tuples
    """
    if not query or not query.strip():
        return []
    
    query_lower = query.lower().strip()
    
    # Build relevance score using CASE with SearchScore enum
    relevance_score = case(
        # Exact matches
        (func.lower(models.Client.email) == query_lower, SearchScore.EXACT_EMAIL),
        (func.lower(models.Client.first_name) == query_lower, SearchScore.EXACT_NAME),
        (func.lower(models.Client.last_name) == query_lower, SearchScore.EXACT_NAME),
        (func.lower(func.concat(
            models.Client.first_name, ' ', models.Client.last_name
        )) == query_lower, SearchScore.EXACT_FULL_NAME),
        
        # Starts with matches
        (func.lower(models.Client.email).startswith(query_lower), SearchScore.STARTS_WITH_EMAIL),
        (func.lower(models.Client.first_name).startswith(query_lower), SearchScore.STARTS_WITH_NAME),
        (func.lower(models.Client.last_name).startswith(query_lower), SearchScore.STARTS_WITH_NAME),
        
        # Contains in email
        (func.lower(models.Client.email).like(f'%{query_lower}%'), SearchScore.CONTAINS_EMAIL),
        
        # Contains in name
        (func.lower(models.Client.first_name).like(f'%{query_lower}%'), SearchScore.CONTAINS_NAME),
        (func.lower(models.Client.last_name).like(f'%{query_lower}%'), SearchScore.CONTAINS_NAME),
        
        # Contains in description
        (func.lower(models.Client.description).like(f'%{query_lower}%'), SearchScore.CONTAINS_DESCRIPTION),
        
        else_=0
    ).label('relevance')
    
    # Query with scoring and ordering
    results = db.query(
        models.Client,
        relevance_score
    ).filter(
        or_(
            func.lower(models.Client.email).like(f'%{query_lower}%'),
            func.lower(models.Client.first_name).like(f'%{query_lower}%'),
            func.lower(models.Client.last_name).like(f'%{query_lower}%'),
            func.lower(models.Client.description).like(f'%{query_lower}%')
        )
    ).order_by(
        relevance_score.desc()
    ).limit(limit).all()
    
    # Format results
    formatted_results = []
    for client, relevance in results:
        # Determine match field
        email_lower = client.email.lower()
        first_name_lower = client.first_name.lower()
        last_name_lower = client.last_name.lower()
        description_lower = (client.description or "").lower()
        
        if query_lower in email_lower:
            match_field = "email"
        elif query_lower in first_name_lower or query_lower in last_name_lower:
            match_field = "name"
        else:
            match_field = "description"
        
        # Normalize score to 0-1
        normalized_score = relevance / SCORE_NORMALIZATION_FACTOR
        
        formatted_results.append((client, normalized_score, match_field))
    
    return formatted_results


def search_documents_keyword(
    db: Session, 
    query: str, 
    limit: int = SEARCH_DEFAULT_LIMIT
) -> List[Tuple[models.Document, float, str]]:
    """
    Search documents by title or content with database-level scoring.
    Supports both phrase matching and word-level matching for better recall.
    
    Returns list of (document, score, match_field) tuples
    """
    if not query or not query.strip():
        return []
    
    query_lower = query.lower().strip()
    query_words = [w.strip() for w in query_lower.split() if w.strip()]
    
    # Build filter conditions: match if ANY word appears (for better recall)
    # This covers both phrase matches (documents with all words) and partial matches
    filter_conditions = []
    for word in query_words:
        filter_conditions.extend([
            func.lower(models.Document.title).like(f'%{word}%'),
            func.lower(models.Document.content).like(f'%{word}%')
        ])
    
    # Build relevance score using SearchScore enum
    # Prioritize phrase matches, then word matches
    relevance_score = case(
        # Exact phrase matches (highest priority)
        (func.lower(models.Document.title) == query_lower, SearchScore.EXACT_EMAIL),
        (func.lower(models.Document.title).startswith(query_lower), SearchScore.STARTS_WITH_EMAIL),
        (func.lower(models.Document.title).like(f'%{query_lower}%'), SearchScore.CONTAINS_EMAIL),
        (func.lower(models.Document.content).like(f'%{query_lower}%'), SearchScore.CONTAINS_DESCRIPTION),
        else_=0
    ).label('relevance')
    
    # Query with scoring and ordering
    results = db.query(
        models.Document,
        relevance_score
    ).filter(
        or_(*filter_conditions)
    ).order_by(
        relevance_score.desc()
    ).limit(limit * 3).all()  # Get more results for word-level scoring
    
    # Format results with word-level scoring
    formatted_results = []
    for doc, relevance in results:
        title_lower = doc.title.lower()
        content_lower = doc.content.lower()
        
        score = float(relevance) if relevance else 0.0
        match_field = ""
        
        # Phrase match scoring (already done in SQL)
        if score > 0:
            if query_lower in title_lower:
                match_field = "title"
            else:
                match_field = "content"
        else:
            # Word-level matching: score based on how many query words appear
            words_in_title = sum(1 for word in query_words if word in title_lower)
            words_in_content = sum(1 for word in query_words if word in content_lower)
            
            if words_in_title > 0 or words_in_content > 0:
                # Calculate score based on word matches
                # More words matched = higher score
                total_words = len(query_words)
                matched_words = max(words_in_title, words_in_content)
                
                # Score based on percentage of words matched
                word_match_ratio = matched_words / total_words if total_words > 0 else 0
                # Use a lower score for word matches than phrase matches
                score = word_match_ratio * SearchScore.CONTAINS_DESCRIPTION * 0.8  # 80% of CONTAINS_DESCRIPTION
                
                if words_in_title > words_in_content:
                    match_field = "title"
                else:
                    match_field = "content"
            else:
                continue  # Skip documents with no matches
        
        # Normalize score to 0-1
        normalized_score = min(score / SCORE_NORMALIZATION_FACTOR, 1.0)
        
        formatted_results.append((doc, normalized_score, match_field))
    
    # Sort by score and limit
    formatted_results.sort(key=lambda x: x[1], reverse=True)
    return formatted_results[:limit]


def search_documents_semantic(
    db: Session, 
    query: str, 
    limit: int = SEARCH_DEFAULT_LIMIT,
    similarity_threshold: float = SEMANTIC_SIMILARITY_THRESHOLD
) -> List[Tuple[models.Document, float, str]]:
    """
    Search documents using semantic similarity (embeddings)
    
    Args:
        db: Database session
        query: Search query
        limit: Maximum results
    
    Returns:
        List of (document, similarity_score, match_field) tuples
    """
    if not query or not query.strip():
        return []
    
    # Generate embedding for the query
    query_embedding = generate_embedding(query)
    
    # Search using cosine similarity (1 - cosine_distance)
    # pgvector's <=> operator returns cosine distance, so we do (1 - distance) for similarity
    results = db.query(
        models.Document,
        (1 - models.Document.embedding.cosine_distance(query_embedding)).label('similarity')
    ).filter(
        models.Document.embedding.isnot(None)  # Only search documents with embeddings
    ).order_by(
        models.Document.embedding.cosine_distance(query_embedding)  # Closest first
    ).limit(limit).all()
    
    # Filter by threshold and format results
    semantic_results = [
        (doc, float(similarity), "semantic") 
        for doc, similarity in results 
        if float(similarity) > similarity_threshold
    ]
    
    return semantic_results


def search_documents_hybrid(
    db: Session, 
    query: str, 
    limit: int = SEARCH_DEFAULT_LIMIT,
    weights: HybridSearchWeights = None
) -> List[Tuple[models.Document, float, str]]:
    """
    Hybrid search: Combine keyword search and semantic search
    
    Args:
        db: Database session
        query: Search query
        limit: Maximum results
        weights: Hybrid search weights (default: 40% keyword, 60% semantic)
    
    Returns:
        List of (document, combined_score, match_field) tuples
    """
    if weights is None:
        weights = HybridSearchWeights()
    
    # Get keyword results
    keyword_results = search_documents_keyword(db, query, limit)
    
    # Get semantic results
    semantic_results = search_documents_semantic(db, query, limit)
    
    # Combine results with weighted scores
    combined = {}
    
    # Add keyword results
    for doc, score, match_field in keyword_results:
        combined[doc.id] = {
            'doc': doc,
            'score': score * weights.KEYWORD_WEIGHT,
            'match_field': match_field
        }
    
    # Add/merge semantic results
    for doc, score, match_field in semantic_results:
        if doc.id in combined:
            combined[doc.id]['score'] += score * weights.SEMANTIC_WEIGHT
            combined[doc.id]['match_field'] = 'hybrid'
        else:
            combined[doc.id] = {
                'doc': doc,
                'score': score * weights.SEMANTIC_WEIGHT,
                'match_field': 'semantic'
            }
    
    # Convert back to list and sort by combined score
    results = [
        (item['doc'], item['score'], item['match_field'])
        for item in combined.values()
    ]
    results.sort(key=lambda x: x[1], reverse=True)
    
    return results[:limit]


def perform_search(
    db: Session, 
    query: str, 
    search_type: str = "all",
    limit: int = SEARCH_DEFAULT_LIMIT,
) -> Tuple[List[Tuple[models.Client, float, str]], List[Tuple[models.Document, float, str]]]:
    """
    Perform search with optional semantic search
    
    Args:
        db: Database session
        query: Search query
        search_type: 'all', 'clients', or 'documents'
        limit: Max results per type
    
    Returns:
        (clients_results, documents_results)
    """
    clients_results = []
    documents_results = []
    
    # Search clients (always keyword-based)
    if search_type in ["all", "clients"]:
        clients_results = search_clients(db, query, limit)
    
    # Search documents (keyword or hybrid)
    if search_type in ["all", "documents"]:
        documents_results = search_documents_hybrid(db, query, limit)
    
    return clients_results, documents_results


from sqlalchemy.orm import Session
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException, status
from . import models, schemas
from sqlalchemy import or_, func, text
from typing import List, Tuple
from .embeddings import generate_embedding
from .summarizer import generate_summary

# -------- Clients --------
def create_client(
    session: Session,
    client: schemas.ClientCreate,
) -> models.Client:
    db_client = models.Client(**client.model_dump())

    try:
        session.add(db_client)
        session.commit()
        session.refresh(db_client)
        return db_client
    except IntegrityError:
        session.rollback()
        raise HTTPException(
            status_code=400,
            detail="Client with this email already exists",
        )

def get_client(
    session: Session,
    client_id: str,
) -> models.Client:
    client = session.scalar(
        select(models.Client).where(models.Client.id == client_id)
    )

    if not client:
        raise HTTPException(status_code=404, detail="Client not found")

    return client

def list_clients(
    session: Session
) -> List[models.Client]:
    client = session.query(models.Client).all()
    return client


# -------- Documents --------
def create_document(
    session: Session,
    client_id: str,
    document: schemas.DocumentCreate,
) -> models.Document:
    get_client(session, client_id)  # Verify client exists
    embedding = generate_embedding(document.content)

    db_document = models.Document(
        client_id=client_id,
        title=document.title,
        content=document.content,
        summary=None,
        embedding=embedding
    )

    session.add(db_document)
    session.commit()
    session.refresh(db_document)

    return db_document

def get_document(db: Session, document_id: str) -> models.Document:
    """Get document by ID"""
    document = db.query(models.Document).filter(models.Document.id == document_id).first()
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    return document

def get_client_documents(
    session: Session,
    client_id: str,
) -> list[models.Document]:
    get_client(session, client_id)  # Verify client exists

    result = session.scalars(
        select(models.Document).where(
            models.Document.client_id == client_id
        )
    )
    return list(result.all())

def search_clients(db: Session, query: str, limit: int = 10) -> List[Tuple[models.Client, float, str]]:
    """
    Search clients by email, name, or description
    Returns list of (client, score, match_field) tuples
    """
    if not query or not query.strip():
        return []
    
    query_lower = query.lower().strip()
    results = []
    
    # Search in database
    clients = db.query(models.Client).filter(
        or_(
            func.lower(models.Client.email).contains(query_lower),
            func.lower(models.Client.first_name).contains(query_lower),
            func.lower(models.Client.last_name).contains(query_lower),
            func.lower(models.Client.description).contains(query_lower)
        )
    ).limit(limit * 2).all()  # Get more than needed for scoring
    
    # Score each result
    for client in clients:
        score = 0.0
        match_field = ""
        
        email_lower = client.email.lower()
        first_name_lower = client.first_name.lower()
        last_name_lower = client.last_name.lower()
        full_name_lower = f"{first_name_lower} {last_name_lower}"
        description_lower = (client.description or "").lower()
        
        # Exact matches get highest score
        if query_lower == email_lower:
            score = 1.0
            match_field = "email"
        elif query_lower == first_name_lower or query_lower == last_name_lower:
            score = 0.95
            match_field = "name"
        elif query_lower == full_name_lower:
            score = 0.95
            match_field = "name"
        # Starts with gets high score
        elif email_lower.startswith(query_lower):
            score = 0.9
            match_field = "email"
        elif first_name_lower.startswith(query_lower) or last_name_lower.startswith(query_lower):
            score = 0.85
            match_field = "name"
        # Contains in email (like domain match)
        elif query_lower in email_lower:
            score = 0.7
            match_field = "email"
        # Contains in name
        elif query_lower in full_name_lower:
            score = 0.65
            match_field = "name"
        # Contains in description
        elif query_lower in description_lower:
            score = 0.5
            match_field = "description"
        
        if score > 0:
            results.append((client, score, match_field))
    
    # Sort by score descending and limit
    results.sort(key=lambda x: x[1], reverse=True)
    return results[:limit]


def search_documents(db: Session, query: str, limit: int = 10) -> List[Tuple[models.Document, float, str]]:
    """
    Search documents by title or content
    Returns list of (document, score, match_field) tuples
    """
    if not query or not query.strip():
        return []
    
    query_lower = query.lower().strip()
    results = []
    
    # Search in database
    documents = db.query(models.Document).filter(
        or_(
            func.lower(models.Document.title).contains(query_lower),
            func.lower(models.Document.content).contains(query_lower)
        )
    ).limit(limit * 2).all()
    
    # Score each result
    for doc in documents:
        score = 0.0
        match_field = ""
        
        title_lower = doc.title.lower()
        content_lower = doc.content.lower()
        
        # Exact match in title
        if query_lower == title_lower:
            score = 1.0
            match_field = "title"
        # Starts with in title
        elif title_lower.startswith(query_lower):
            score = 0.9
            match_field = "title"
        # Contains in title
        elif query_lower in title_lower:
            score = 0.7
            match_field = "title"
        # Contains in content
        elif query_lower in content_lower:
            # Calculate word-based score
            words = query_lower.split()
            content_words = content_lower.split()
            
            # More word matches = higher score
            if len(words) == 1:
                score = 0.5
            else:
                matches = sum(1 for word in words if word in content_words)
                score = 0.3 + (matches / len(words)) * 0.4  # 0.3 to 0.7
            
            match_field = "content"
        
        if score > 0:
            results.append((doc, score, match_field))
    
    # Sort by score descending and limit
    results.sort(key=lambda x: x[1], reverse=True)
    return results[:limit]


def perform_search(
    db: Session, 
    query: str, 
    search_type: str = "all",
    limit: int = 10
) -> Tuple[List[Tuple[models.Client, float, str]], List[Tuple[models.Document, float, str]]]:
    """
    Perform search based on type
    Returns (clients_results, documents_results)
    """
    clients_results = []
    documents_results = []
    
    if search_type in ["all", "clients"]:
        clients_results = search_clients(db, query, limit)
    
    if search_type in ["all", "documents"]:
        documents_results = search_documents(db, query, limit)
    
    return clients_results, documents_results

def search_documents_semantic(
    db: Session, 
    query: str, 
    limit: int = 10,
    similarity_threshold: float = 0.3
) -> List[Tuple[models.Document, float, str]]:
    """
    Search documents using semantic similarity (embeddings)
    
    Args:
        db: Database session
        query: Search query
        limit: Maximum results
        similarity_threshold: Minimum cosine similarity (0-1)
    
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
    semantic_results = []
    for doc, similarity in results:
        if similarity >= similarity_threshold:
            semantic_results.append((doc, float(similarity), "semantic"))
    
    return semantic_results


def search_documents_hybrid(
    db: Session, 
    query: str, 
    limit: int = 10
) -> List[Tuple[models.Document, float, str]]:
    """
    Hybrid search: Combine keyword search and semantic search
    
    Weights: 40% keyword match + 60% semantic similarity
    """
    # Get keyword results
    keyword_results = search_documents(db, query, limit)
    
    # Get semantic results
    semantic_results = search_documents_semantic(db, query, limit, similarity_threshold=0.3)
    
    # Combine results with weighted scores
    combined = {}
    
    # Add keyword results (40% weight)
    for doc, score, match_field in keyword_results:
        combined[doc.id] = {
            'doc': doc,
            'score': score * 0.4,
            'match_field': match_field
        }
    
    # Add/merge semantic results (60% weight)
    for doc, score, match_field in semantic_results:
        if doc.id in combined:
            # Document found in both - combine scores
            combined[doc.id]['score'] += score * 0.6
            combined[doc.id]['match_field'] = 'hybrid'
        else:
            # Only in semantic results
            combined[doc.id] = {
                'doc': doc,
                'score': score * 0.6,
                'match_field': 'semantic'
            }
    
    # Convert back to list and sort by combined score
    results = [
        (item['doc'], item['score'], item['match_field'])
        for item in combined.values()
    ]
    results.sort(key=lambda x: x[1], reverse=True)
    
    return results[:limit]


def perform_search_semantic(
    db: Session, 
    query: str, 
    search_type: str = "all",
    limit: int = 10,
    use_semantic: bool = True
) -> Tuple[List[Tuple[models.Client, float, str]], List[Tuple[models.Document, float, str]]]:
    """
    Perform search with optional semantic search
    
    Args:
        db: Database session
        query: Search query
        search_type: 'all', 'clients', or 'documents'
        limit: Max results per type
        use_semantic: If True, use hybrid search for documents
    
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
        if use_semantic:
            documents_results = search_documents_hybrid(db, query, limit)
        else:
            documents_results = search_documents(db, query, limit)
    
    return clients_results, documents_results


def get_or_generate_summary(
    db: Session, 
    document_id: str,
    max_length: int = 200,
    regenerate: bool = False
) -> str:
    """
    Get cached summary or generate a new one
    
    Args:
        db: Database session
        document_id: Document ID
        max_length: Maximum summary length
        regenerate: If True, regenerate even if cached summary exists
    
    Returns:
        Document summary
    """
    # Get document
    document = get_document(db, document_id)
    
    # Return cached summary if exists and not forcing regeneration
    if document.summary and not regenerate:
        return document.summary
    
    # Generate new summary
    summary = generate_summary(document.content, max_length=max_length)
    
    # Cache it in database
    document.summary = summary
    db.commit()
    db.refresh(document)
    
    return summary
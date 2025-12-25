from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import List, Optional
from .database import get_db
from . import schemas, crud


app = FastAPI(
    title="Nevis Search API",
    description="WealthTech search API for clients and documents",
    version="1.0.0",
)


@app.get("/")
def root():
    return {
        "message": "Nevis Search API",
        "version": "1.0.0",
    }

@app.get("/health", tags=["Health"])
def health_check(db: Session = Depends(get_db)):
    """Health check endpoint"""
    try:
        # Test database connection
        db.execute(text("SELECT 1"))  # ← Use text() wrapper
        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"status": "unhealthy", "database": "disconnected", "error": str(e)}
        )

# -------- Clients --------
@app.post(
    "/clients",
    response_model=schemas.ClientResponse,
    status_code=201,
)
def create_client(
    client: schemas.ClientCreate,
    db: Session = Depends(get_db),
):
    return crud.create_client(db, client)


@app.get(
    "/clients/{client_id}",
    response_model=schemas.ClientResponse,
)
def get_client(
    client_id: str,
    db: Session = Depends(get_db),
):
    return crud.get_client(db, client_id)


# -------- Documents --------
@app.post(
    "/clients/{client_id}/documents",
    response_model=schemas.DocumentResponse,
    status_code=201,
)
def create_document(
    client_id: str,
    document: schemas.DocumentCreate,
    db: Session = Depends(get_db),
):
    return crud.create_document(db, client_id, document)

@app.get(
    "/documents/{document_id}",
    response_model=schemas.DocumentResponse,
    tags=["Documents"]
)
def get_document(document_id: str, db: Session = Depends(get_db)):
    """Get a specific document by ID"""
    return crud.get_document(db, document_id)


@app.get(
    "/clients/{client_id}/documents",
    response_model=List[schemas.DocumentResponse],
)
def get_client_documents(
    client_id: str,
    db: Session = Depends(get_db),
):
    return crud.get_client_documents(db, client_id)


@app.get(
    "/documents/{document_id}/summary",
    response_model=schemas.DocumentSummaryResponse,
    tags=["Documents"]
)
def get_document_summary(
    document_id: str,
    max_length: int = Query(200, ge=50, le=500, description="Maximum summary length in characters"),
    regenerate: bool = Query(False, description="Force regenerate summary even if cached"),
    db: Session = Depends(get_db)
):
    """
    Get or generate a summary for a document
    
    - **document_id**: The document ID to summarize
    - **max_length**: Maximum summary length (50-500 characters, default: 200)
    - **regenerate**: If true, regenerate summary even if cached (default: false)
    
    GET /documents/doc-123/summary?regenerate=true&max_length=300
    """
    # Get the document first to check if it exists
    document = crud.get_document(db, document_id)
    
    # Check if summary was already cached
    was_cached = document.summary is not None and not regenerate
    
    # Get or generate summary
    summary = crud.get_or_generate_summary(
        db, 
        document_id, 
        max_length=max_length,
        regenerate=regenerate
    )
    
    return schemas.DocumentSummaryResponse(
        document_id=document.id,
        title=document.title,
        summary=summary,
        summary_length=len(summary),
        cached=was_cached
    )


# Search Endpoint
@app.get(
    "/search",
    response_model=schemas.SearchResponse,
    tags=["Search"]
)
def search(
    q: str,
    type: schemas.SearchType = schemas.SearchType.ALL,
    limit: int = 10,
    semantic: bool = True,  # ← Add this parameter
    db: Session = Depends(get_db)
):
    """
    Search across clients and/or documents
    
    - **q**: Search query string
    - **type**: Search type - 'all', 'clients', or 'documents' (default: all)
    - **limit**: Maximum number of results per type (default: 10)
    - **semantic**: Use semantic search for documents (default: True)
    """
    if not q or not q.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Search query cannot be empty"
        )
    
    if limit < 1 or limit > 100:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Limit must be between 1 and 100"
        )
    
    # Perform search with semantic option
    clients_results, documents_results = crud.perform_search_semantic(
        db, q, type.value, limit, use_semantic=semantic
    )
    
    # Format client results
    clients = [
        schemas.ClientSearchResult(
            id=client.id,
            first_name=client.first_name,
            last_name=client.last_name,
            email=client.email,
            description=client.description,
            match_score=score,
            match_field=match_field
        )
        for client, score, match_field in clients_results
    ]
    
    # Format document results
    documents = [
        schemas.DocumentSearchResult(
            id=doc.id,
            client_id=doc.client_id,
            title=doc.title,
            content=doc.content,
            created_at=doc.created_at,
            match_score=score,
            match_field=match_field
        )
        for doc, score, match_field in documents_results
    ]
    
    return schemas.SearchResponse(
        query=q,
        search_type=type,
        clients=clients,
        documents=documents,
        total_results=len(clients) + len(documents)
    )
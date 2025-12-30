import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, HTTPException, status, Query
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import List, Optional

from .database import get_db, init_db
from . import schemas, crud
from . import search as search_module
from .summarizer import check_openai_availability
from .search_config import SEARCH_MIN_LIMIT, SEARCH_MAX_LIMIT, SEARCH_DEFAULT_LIMIT


# API configuration constants
class APILimits:
    """API validation limits"""
    SEARCH_LIMIT_MIN = SEARCH_MIN_LIMIT
    SEARCH_LIMIT_MAX = SEARCH_MAX_LIMIT
    SUMMARY_LENGTH_MIN = 50
    SUMMARY_LENGTH_DEFAULT = 200
    SUMMARY_LENGTH_MAX = 500
    PAGINATION_DEFAULT_LIMIT = 10
    PAGINATION_MIN_LIMIT = 1
    PAGINATION_MAX_LIMIT = 100
    BATCH_DOCUMENTS_MAX = 100
    BATCH_DOCUMENTS_MIN = 1

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        logger.info("Starting application initialization...")
        init_db()
        openai_status = check_openai_availability()
        if openai_status['available']:
            logger.info("OpenAI API key validated")
        else:
            logger.warning("OpenAI API key validation failed - summaries will use fallback")
        
        logger.info("Application startup complete")
    except Exception as e:
        logger.error(f"Application startup failed: {e}")
        raise
    
    yield
    
    logger.info("Application shutdown")

app = FastAPI(
    lifespan = lifespan,
    title="Nevis Search API",
    description="""
    WealthTech search API for clients and documents with semantic search capabilities.
    
    ## Features
    
    - Client and document management
    - Hybrid search (keyword + semantic similarity)
    - Document summarization with OpenAI
    - Vector embeddings for semantic search
    - Pagination support
    
    ## Interactive Documentation
    
    - **Swagger UI:** `/docs` - Interactive API explorer
    - **ReDoc:** `/redoc` - Alternative documentation interface
    
    ## Additional Documentation
    
    - **API Examples:** See `API_EXAMPLES.md` for detailed request/response examples
    - **Full Documentation:** See `API_DOCUMENTATION.md` for complete API reference
    """,
    version="1.0.0",
    contact={
        "name": "Nevis Search API",
    },
)

@app.get("/")
def root():
    return {
        "message": "Nevis Search API",
        "version": "1.0.0",
    }

@app.get("/health/db", tags=["Health"])
def health_check(db: Session = Depends(get_db)):
    """Health check endpoint"""
    try:
        # Test database connection
        db.execute(text("SELECT 1")) 
        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"status": "unhealthy", "database": "disconnected", "error": str(e)}
        )

@app.get("/health/openai", tags=["Health"])
def openai_health_check():
    """
    Check OpenAI API availability
    
    Returns detailed status about OpenAI integration
    """
    
    openai_status = check_openai_availability()
    
    if openai_status['available']:
        return {
            "status": "healthy",
            "openai_api": "connected",
            "api_key": "valid",
            "models_count": len(openai_status['models_accessible']) if openai_status['models_accessible'] else 0,
            "sample_models": openai_status['models_accessible'][:5] if openai_status['models_accessible'] else []
        }
    else:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "status": "unhealthy",
                "openai_api": "disconnected",
                "api_key": "valid" if openai_status['api_key_valid'] else "invalid",
                "error": openai_status['error']
            }
        )

# -------- Clients --------
@app.get(
    "/clients",
    response_model=schemas.PaginatedResponse[schemas.ClientResponse],
)
def list_clients(
    offset: int = Query(0, ge=0, description="Number of clients to skip"),
    limit: int = Query(
        APILimits.PAGINATION_DEFAULT_LIMIT,
        ge=APILimits.PAGINATION_MIN_LIMIT,
        le=APILimits.PAGINATION_MAX_LIMIT,
        description="Maximum number of clients to return"
    ),
    db: Session = Depends(get_db),
):
    """
    List existing clients with pagination
    
    - **offset**: Number of clients to skip (default: 0)
    - **limit**: Maximum number of clients to return (default: 10, max: 100)
    """
    clients, total = crud.list_clients(db, offset=offset, limit=limit)
    
    return schemas.PaginatedResponse(
        items=[schemas.ClientResponse.model_validate(client) for client in clients],
        total=total,
        offset=offset,
        limit=limit,
        has_next=(offset + limit) < total,
        has_previous=offset > 0
    )

@app.get(
    "/clients/{client_id}",
    response_model=schemas.ClientResponse,
)
def get_client(
    client_id: str,
    db: Session = Depends(get_db),
):
    """Get client information by client_id"""
    return crud.get_client(db, client_id)

@app.post(
    "/clients",
    response_model=schemas.ClientResponse,
    status_code=201,
)
def create_client(
    client: schemas.ClientCreate,
    db: Session = Depends(get_db),
):
    """Create new client"""
    return crud.create_client(db, client)


# -------- Documents --------
@app.get(
    "/documents/{document_id}",
    response_model=schemas.DocumentResponse,
    tags=["Documents"]
)
def get_document(document_id: str, db: Session = Depends(get_db)):
    """Get a document by document_id"""
    return crud.get_document(db, document_id)


@app.get(
    "/clients/{client_id}/documents",
    response_model=schemas.PaginatedResponse[schemas.DocumentResponse],
)
def get_client_documents(
    client_id: str,
    offset: int = Query(0, ge=0, description="Number of documents to skip"),
    limit: int = Query(
        APILimits.PAGINATION_DEFAULT_LIMIT,
        ge=APILimits.PAGINATION_MIN_LIMIT,
        le=APILimits.PAGINATION_MAX_LIMIT,
        description="Maximum number of documents to return"
    ),
    db: Session = Depends(get_db),
):
    """
    Get documents of one client by client_id with pagination
    
    - **client_id**: The client ID
    - **offset**: Number of documents to skip (default: 0)
    - **limit**: Maximum number of documents to return (default: 10, max: 100)
    """
    documents, total = crud.get_client_documents(db, client_id, offset=offset, limit=limit)
    
    return schemas.PaginatedResponse(
        items=[schemas.DocumentResponse.model_validate(doc) for doc in documents],
        total=total,
        offset=offset,
        limit=limit,
        has_next=(offset + limit) < total,
        has_previous=offset > 0
    )

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
    """Create document for a client by client_id"""
    return crud.create_document(db, client_id, document)


@app.post(
    "/clients/{client_id}/documents/batch",
    response_model=List[schemas.DocumentResponse],
    status_code=201,
    tags=["Documents"]
)
def create_documents_batch(
    client_id: str,
    batch: schemas.BatchDocumentCreate,
    db: Session = Depends(get_db),
):
    """
    Create multiple documents for a client in a single batch operation.
    
    More efficient than creating documents one by one, especially for large datasets,
    as it uses batch embedding generation.
    
    - **client_id**: The client ID
    - **documents**: List of documents to create (1-100 documents per batch)
    """
    if len(batch.documents) > APILimits.BATCH_DOCUMENTS_MAX:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Maximum {APILimits.BATCH_DOCUMENTS_MAX} documents allowed per batch"
        )
    
    created_documents = crud.create_documents_batch(db, client_id, batch.documents)
    return [schemas.DocumentResponse.model_validate(doc) for doc in created_documents]

# -------- Summary --------
@app.get(
    "/documents/{document_id}/summary",
    response_model=schemas.DocumentSummaryResponse,
    tags=["Documents"]
)
def get_document_summary(
    document_id: str,
    max_length: int = Query(
        APILimits.SUMMARY_LENGTH_DEFAULT, 
        ge=APILimits.SUMMARY_LENGTH_MIN, 
        le=APILimits.SUMMARY_LENGTH_MAX, 
        description="Maximum summary length in characters"
    ),
    regenerate: bool = Query(False, description="Force regenerate summary even if cached"),
    db: Session = Depends(get_db)
):
    """
    Get or generate a summary for a document
    
    - **document_id**: The document ID to summarize
    - **max_length**: Maximum summary length (50-500 characters, default: 200)
    - **regenerate**: If true, regenerate summary even if cached (default: false)
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


# -------- Search --------
@app.get(
    "/search",
    response_model=schemas.SearchResponse,
    tags=["Search"]
)
def search(
    q: str,
    type: schemas.SearchType = schemas.SearchType.ALL,
    limit: int = SEARCH_DEFAULT_LIMIT,
    db: Session = Depends(get_db)
):
    """
    Search across clients and/or documents
    
    - **q**: Search query string
    - **type**: Search type - 'all', 'clients', or 'documents' (default: all)
    - **limit**: Maximum number of results per type (default: 10)
    """
    if not q or not q.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Search query cannot be empty"
        )
    
    if limit < APILimits.SEARCH_LIMIT_MIN or limit > APILimits.SEARCH_LIMIT_MAX:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Limit must be between {APILimits.SEARCH_LIMIT_MIN} and {APILimits.SEARCH_LIMIT_MAX}"
        )
    
    # Perform search (always uses hybrid search for documents)
    clients_results, documents_results = search_module.perform_search(
        db, q, type.value, limit
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

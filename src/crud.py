from sqlalchemy.orm import Session
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException, status
from typing import List
from . import models, schemas
from .embeddings import generate_embedding
from .summarizer import generate_summary

# -------- Clients --------
def create_client(
    db: Session,
    client: schemas.ClientCreate,
) -> models.Client:
    db_client = models.Client(**client.model_dump())

    try:
        db.add(db_client)
        db.commit()
        db.refresh(db_client)
        return db_client
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=400,
            detail="Client with this email already exists",
        )

def get_client(
    db: Session,
    client_id: str,
) -> models.Client:
    client = db.scalar(
        select(models.Client).where(models.Client.id == client_id)
    )

    if not client:
        raise HTTPException(status_code=404, detail="Client not found")

    return client

def list_clients(
    db: Session,
    offset: int = 0,
    limit: int = 10
) -> tuple[List[models.Client], int]:
    """
    List clients with pagination
    
    Returns:
        Tuple of (clients list, total count)
    """
    total = db.query(models.Client).count()
    clients = db.query(models.Client).offset(offset).limit(limit).all()
    return clients, total


# -------- Documents --------
def create_document(
    db: Session,
    client_id: str,
    document: schemas.DocumentCreate,
) -> models.Document:
    get_client(db, client_id)  # Verify client exists
    embedding = generate_embedding(document.content)

    db_document = models.Document(
        client_id=client_id,
        title=document.title,
        content=document.content,
        summary=None,
        embedding=embedding
    )

    db.add(db_document)
    db.commit()
    db.refresh(db_document)

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
    db: Session,
    client_id: str,
    offset: int = 0,
    limit: int = 10
) -> tuple[list[models.Document], int]:
    """
    Get documents for a client with pagination
    
    Returns:
        Tuple of (documents list, total count)
    """
    get_client(db, client_id)  # Verify client exists

    # Get total count
    total = db.query(models.Document).filter(
        models.Document.client_id == client_id
    ).count()
    
    # Get paginated results
    documents = db.query(models.Document).filter(
        models.Document.client_id == client_id
    ).offset(offset).limit(limit).all()
    
    return documents, total


# -------- Summary --------
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
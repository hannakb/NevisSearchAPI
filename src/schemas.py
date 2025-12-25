from pydantic import BaseModel, EmailStr, Field, ConfigDict
from datetime import datetime
from typing import Optional, List
from enum import Enum


# -------- Clients --------
class ClientCreate(BaseModel):
    first_name: str = Field(min_length=1)
    last_name: str = Field(min_length=1)
    email: EmailStr
    description: Optional[str] = None


class ClientResponse(BaseModel):
    id: str
    first_name: str
    last_name: str
    email: EmailStr
    description: Optional[str]
    created_at: datetime

    model_config = {"from_attributes": True}


# -------- Documents --------
class DocumentCreate(BaseModel):
    title: str = Field(min_length=1)
    content: str = Field(min_length=1)


class DocumentResponse(BaseModel):
    id: str
    client_id: str
    title: str
    content: str
    created_at: datetime

    model_config = {"from_attributes": True}

class DocumentSummaryResponse(BaseModel):
    """Response schema for document summary endpoint"""
    document_id: str
    title: str
    summary: str
    summary_length: int
    cached: bool  # Whether summary was cached or newly generated


# Search Schemas
class SearchType(str, Enum):
    ALL = "all"
    CLIENTS = "clients"
    DOCUMENTS = "documents"


class ClientSearchResult(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: str
    first_name: str
    last_name: str
    email: str
    description: Optional[str] = None
    match_score: float = Field(..., ge=0.0, le=1.0)
    match_field: str  # Which field matched: "email", "name", "description"


class DocumentSearchResult(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: str
    client_id: str
    title: str
    content: str
    created_at: datetime
    match_score: float = Field(..., ge=0.0, le=1.0)
    match_field: str  # "title" or "content"


class SearchResponse(BaseModel):
    query: str
    search_type: SearchType
    clients: List[ClientSearchResult] = []
    documents: List[DocumentSearchResult] = []
    total_results: int

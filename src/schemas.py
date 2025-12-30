from pydantic import BaseModel, EmailStr, Field, ConfigDict
from datetime import datetime
from typing import Optional, List, Generic, TypeVar
from enum import Enum

T = TypeVar('T')


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


class BatchDocumentCreate(BaseModel):
    """Batch document creation request"""
    documents: List[DocumentCreate] = Field(min_length=1, max_length=100, description="List of documents to create (1-100)")


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


# -------- Search --------
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


# -------- Pagination --------
class PaginationParams(BaseModel):
    """Pagination parameters"""
    offset: int = Field(default=0, ge=0, description="Number of items to skip")
    limit: int = Field(default=10, ge=1, le=100, description="Maximum number of items to return")


class PaginatedResponse(BaseModel, Generic[T]):
    """Generic paginated response"""
    items: List[T]
    total: int
    offset: int
    limit: int
    has_next: bool
    has_previous: bool

    @property
    def page(self) -> int:
        """Current page number (1-indexed)"""
        return (self.offset // self.limit) + 1 if self.limit > 0 else 1

    @property
    def total_pages(self) -> int:
        """Total number of pages"""
        return (self.total + self.limit - 1) // self.limit if self.limit > 0 else 1

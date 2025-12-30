# API Examples

This document provides example queries and responses for the Nevis Search API.

## Search Examples

### Example 1: Search for Clients by Email

**Request:**
```http
GET /search?q=john.doe@neviswealth.com&type=clients
```

**Response:**
```json
{
  "query": "john.doe@neviswealth.com",
  "search_type": "clients",
  "clients": [
    {
      "id": "client-12345678-1234-5678-1234-567812345678",
      "first_name": "John",
      "last_name": "Doe",
      "email": "john.doe@neviswealth.com",
      "description": "High net worth individual",
      "match_score": 1.0,
      "match_field": "email"
    }
  ],
  "documents": [],
  "total_results": 1
}
```

### Example 2: Semantic Search for Documents

**Request:**
```http
GET /search?q=machine learning&type=documents&limit=5
```

**Response:**
```json
{
  "query": "machine learning",
  "search_type": "documents",
  "clients": [],
  "documents": [
    {
      "id": "doc-87654321-4321-8765-4321-876543218765",
      "client_id": "client-12345678-1234-5678-1234-567812345678",
      "title": "Attention all you need",
      "content": "The dominant sequence transduction models are based on complex recurrent or convolutional neural networks...",
      "created_at": "2024-01-15T10:30:00Z",
      "match_score": 0.75,
      "match_field": "semantic"
    },
    {
      "id": "doc-11111111-1111-1111-1111-111111111111",
      "client_id": "client-12345678-1234-5678-1234-567812345678",
      "title": "Deep Learning Fundamentals",
      "content": "An introduction to neural networks and machine learning algorithms...",
      "created_at": "2024-01-10T14:20:00Z",
      "match_score": 0.68,
      "match_field": "hybrid"
    }
  ],
  "total_results": 2
}
```

### Example 3: Search All Types (Clients + Documents)

**Request:**
```http
GET /search?q=investment&type=all&limit=10
```

**Response:**
```json
{
  "query": "investment",
  "search_type": "all",
  "clients": [
    {
      "id": "client-22222222-2222-2222-2222-222222222222",
      "first_name": "Jane",
      "last_name": "Smith",
      "email": "jane.smith@example.com",
      "description": "Investment advisor specializing in portfolio management",
      "match_score": 0.5,
      "match_field": "description"
    }
  ],
  "documents": [
    {
      "id": "doc-33333333-3333-3333-3333-333333333333",
      "client_id": "client-22222222-2222-2222-2222-222222222222",
      "title": "Investment Portfolio Analysis",
      "content": "Quarterly review of investment portfolio performance and recommendations...",
      "created_at": "2024-02-01T09:00:00Z",
      "match_score": 0.85,
      "match_field": "title"
    }
  ],
  "total_results": 2
}
```

### Example 4: Semantic Search for Related Concepts

**Request:**
```http
GET /search?q=address proof&type=documents
```

**Response:**
```json
{
  "query": "address proof",
  "search_type": "documents",
  "clients": [],
  "documents": [
    {
      "id": "doc-44444444-4444-4444-4444-444444444444",
      "client_id": "client-12345678-1234-5678-1234-567812345678",
      "title": "Utility Bill - March 2024",
      "content": "Monthly electric utility bill serving as proof of address and residence verification",
      "created_at": "2024-03-15T12:00:00Z",
      "match_score": 0.72,
      "match_field": "semantic"
    },
    {
      "id": "doc-55555555-5555-5555-5555-555555555555",
      "client_id": "client-12345678-1234-5678-1234-567812345678",
      "title": "Lease Agreement",
      "content": "Rental contract for apartment showing current living address",
      "created_at": "2024-02-20T10:00:00Z",
      "match_score": 0.65,
      "match_field": "semantic"
    }
  ],
  "total_results": 2
}
```

### Example 5: Search by Client Name

**Request:**
```http
GET /search?q=John Doe&type=clients
```

**Response:**
```json
{
  "query": "John Doe",
  "search_type": "clients",
  "clients": [
    {
      "id": "client-12345678-1234-5678-1234-567812345678",
      "first_name": "John",
      "last_name": "Doe",
      "email": "john.doe@neviswealth.com",
      "description": "High net worth individual",
      "match_score": 0.95,
      "match_field": "name"
    }
  ],
  "documents": [],
  "total_results": 1
}
```

## Client Management Examples

### Create Client

**Request:**
```http
POST /clients
Content-Type: application/json

{
  "first_name": "John",
  "last_name": "Doe",
  "email": "john.doe@neviswealth.com",
  "description": "High net worth individual"
}
```

**Response:**
```json
{
  "id": "client-12345678-1234-5678-1234-567812345678",
  "first_name": "John",
  "last_name": "Doe",
  "email": "john.doe@neviswealth.com",
  "description": "High net worth individual",
  "created_at": "2024-01-15T10:30:00Z"
}
```

### List Clients (Paginated)

**Request:**
```http
GET /clients?offset=0&limit=10
```

**Response:**
```json
{
  "items": [
    {
      "id": "client-12345678-1234-5678-1234-567812345678",
      "first_name": "John",
      "last_name": "Doe",
      "email": "john.doe@neviswealth.com",
      "description": "High net worth individual",
      "created_at": "2024-01-15T10:30:00Z"
    },
    {
      "id": "client-22222222-2222-2222-2222-222222222222",
      "first_name": "Jane",
      "last_name": "Smith",
      "email": "jane.smith@example.com",
      "description": "Investment advisor",
      "created_at": "2024-01-20T14:20:00Z"
    }
  ],
  "total": 25,
  "offset": 0,
  "limit": 10,
  "has_next": true,
  "has_previous": false
}
```

### Get Client by ID

**Request:**
```http
GET /clients/client-12345678-1234-5678-1234-567812345678
```

**Response:**
```json
{
  "id": "client-12345678-1234-5678-1234-567812345678",
  "first_name": "John",
  "last_name": "Doe",
  "email": "john.doe@neviswealth.com",
  "description": "High net worth individual",
  "created_at": "2024-01-15T10:30:00Z"
}
```

## Document Management Examples

### Create Document

**Request:**
```http
POST /clients/client-12345678-1234-5678-1234-567812345678/documents
Content-Type: application/json

{
  "title": "Tax Return 2023",
  "content": "Annual tax return document with investment income details and deductions"
}
```

**Response:**
```json
{
  "id": "doc-87654321-4321-8765-4321-876543218765",
  "client_id": "client-12345678-1234-5678-1234-567812345678",
  "title": "Tax Return 2023",
  "content": "Annual tax return document with investment income details and deductions",
  "created_at": "2024-01-15T10:35:00Z"
}
```

### List Client Documents (Paginated)

**Request:**
```http
GET /clients/client-12345678-1234-5678-1234-567812345678/documents?offset=0&limit=5
```

**Response:**
```json
{
  "items": [
    {
      "id": "doc-87654321-4321-8765-4321-876543218765",
      "client_id": "client-12345678-1234-5678-1234-567812345678",
      "title": "Tax Return 2023",
      "content": "Annual tax return document with investment income details",
      "created_at": "2024-01-15T10:35:00Z"
    },
    {
      "id": "doc-11111111-1111-1111-1111-111111111111",
      "client_id": "client-12345678-1234-5678-1234-567812345678",
      "title": "Utility Bill - March 2024",
      "content": "Monthly electric utility bill",
      "created_at": "2024-03-15T12:00:00Z"
    }
  ],
  "total": 12,
  "offset": 0,
  "limit": 5,
  "has_next": true,
  "has_previous": false
}
```

### Get Document by ID

**Request:**
```http
GET /documents/doc-87654321-4321-8765-4321-876543218765
```

**Response:**
```json
{
  "id": "doc-87654321-4321-8765-4321-876543218765",
  "client_id": "client-12345678-1234-5678-1234-567812345678",
  "title": "Tax Return 2023",
  "content": "Annual tax return document with investment income details and deductions",
  "created_at": "2024-01-15T10:35:00Z"
}
```

### Get Document Summary

**Request:**
```http
GET /documents/doc-87654321-4321-8765-4321-876543218765/summary?max_length=200
```

**Response:**
```json
{
  "document_id": "doc-87654321-4321-8765-4321-876543218765",
  "title": "Tax Return 2023",
  "summary": "Annual tax return document summarizing investment income, deductions, and financial details for the 2023 tax year.",
  "summary_length": 108,
  "cached": false
}
```

## Health Check Examples

### Database Health Check

**Request:**
```http
GET /health/db
```

**Response:**
```json
{
  "status": "healthy",
  "database": "connected"
}
```

### OpenAI Health Check

**Request:**
```http
GET /health/openai
```

**Response:**
```json
{
  "status": "healthy",
  "openai_api": "connected",
  "api_key": "valid",
  "models_count": 50,
  "sample_models": ["gpt-4o-mini", "gpt-4o", "gpt-4-turbo", "gpt-3.5-turbo", "text-embedding-ada-002"]
}
```

## Error Responses

### 400 Bad Request - Empty Search Query

**Request:**
```http
GET /search?q=
```

**Response:**
```json
{
  "detail": "Search query cannot be empty"
}
```

### 404 Not Found - Client Not Found

**Request:**
```http
GET /clients/non-existent-id
```

**Response:**
```json
{
  "detail": "Client not found"
}
```

### 422 Validation Error - Invalid Pagination

**Request:**
```http
GET /clients?offset=-1
```

**Response:**
```json
{
  "detail": [
    {
      "loc": ["query", "offset"],
      "msg": "ensure this value is greater than or equal to 0",
      "type": "value_error.number.not_ge",
      "ctx": {"limit_value": 0}
    }
  ]
}
```


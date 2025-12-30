# Nevis Search API Documentation

WealthTech search API for clients and documents with semantic search capabilities.

## Base URL

- **Local Development:** `http://localhost:8000`
- **Production:** `https://nevissearchapi-production.up.railway.app`

## Interactive Documentation

FastAPI automatically generates interactive API documentation:
- **Swagger UI:** `/docs` - Interactive API explorer
- **ReDoc:** `/redoc` - Alternative documentation interface

## Authentication

Currently, the API does not require authentication. All endpoints are publicly accessible.

## API Endpoints

### Root

#### GET `/`
Get API information.

**Response:**
```json
{
  "message": "Nevis Search API",
  "version": "1.0.0"
}
```

---

### Health Checks

#### GET `/health/db`
Check database connection health.

**Response (200 OK):**
```json
{
  "status": "healthy",
  "database": "connected"
}
```

**Response (503 Service Unavailable):**
```json
{
  "status": "unhealthy",
  "database": "disconnected",
  "error": "Connection error message"
}
```

#### GET `/health/openai`
Check OpenAI API availability and key validity.

**Response (200 OK):**
```json
{
  "status": "healthy",
  "openai_api": "connected",
  "api_key": "valid",
  "models_count": 50,
  "sample_models": ["gpt-4o-mini", "gpt-4o", "gpt-4-turbo"]
}
```

**Response (503 Service Unavailable):**
```json
{
  "status": "unhealthy",
  "openai_api": "disconnected",
  "api_key": "invalid",
  "error": "Error message"
}
```

---

### Clients

#### GET `/clients`
List all clients with pagination.

**Query Parameters:**
- `offset` (integer, default: 0) - Number of clients to skip (min: 0)
- `limit` (integer, default: 10) - Maximum number of clients to return (min: 1, max: 100)

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
    }
  ],
  "total": 25,
  "offset": 0,
  "limit": 10,
  "has_next": true,
  "has_previous": false
}
```

#### POST `/clients`
Create a new client.

**Request Body:**
```json
{
  "first_name": "John",
  "last_name": "Doe",
  "email": "john.doe@neviswealth.com",
  "description": "High net worth individual"  // Optional
}
```

**Response (201 Created):**
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

**Error (400 Bad Request):** Client with this email already exists

#### GET `/clients/{client_id}`
Get a specific client by ID.

**Path Parameters:**
- `client_id` (string) - Client ID

**Response (200 OK):**
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

**Error (404 Not Found):** Client not found

---

### Documents

#### GET `/documents/{document_id}`
Get a specific document by ID.

**Path Parameters:**
- `document_id` (string) - Document ID

**Response (200 OK):**
```json
{
  "id": "doc-87654321-4321-8765-4321-876543218765",
  "client_id": "client-12345678-1234-5678-1234-567812345678",
  "title": "Tax Return 2023",
  "content": "Annual tax return document with investment income details",
  "created_at": "2024-01-15T10:35:00Z"
}
```

**Error (404 Not Found):** Document not found

#### POST `/clients/{client_id}/documents`
Create a new document for a client.

**Path Parameters:**
- `client_id` (string) - Client ID

**Request Body:**
```json
{
  "title": "Tax Return 2023",
  "content": "Annual tax return document with investment income details"
}
```

**Response (201 Created):**
```json
{
  "id": "doc-87654321-4321-8765-4321-876543218765",
  "client_id": "client-12345678-1234-5678-1234-567812345678",
  "title": "Tax Return 2023",
  "content": "Annual tax return document with investment income details",
  "created_at": "2024-01-15T10:35:00Z"
}
```

**Error (404 Not Found):** Client not found

**Note:** Creating a document automatically generates an embedding for semantic search. This may take a few seconds.

#### GET `/clients/{client_id}/documents`
List all documents for a specific client with pagination.

**Path Parameters:**
- `client_id` (string) - Client ID

**Query Parameters:**
- `offset` (integer, default: 0) - Number of documents to skip (min: 0)
- `limit` (integer, default: 10) - Maximum number of documents to return (min: 1, max: 100)

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
    }
  ],
  "total": 5,
  "offset": 0,
  "limit": 10,
  "has_next": false,
  "has_previous": false
}
```

#### GET `/documents/{document_id}/summary`
Get or generate a summary for a document.

**Path Parameters:**
- `document_id` (string) - Document ID

**Query Parameters:**
- `max_length` (integer, default: 200) - Maximum summary length in characters (min: 50, max: 500)
- `regenerate` (boolean, default: false) - Force regenerate summary even if cached

**Response (200 OK):**
```json
{
  "document_id": "doc-87654321-4321-8765-4321-876543218765",
  "title": "Tax Return 2023",
  "summary": "Annual tax return document summarizing investment income, deductions, and financial details for the 2023 tax year.",
  "summary_length": 108,
  "cached": false
}
```

**Error (404 Not Found):** Document not found

**Error (422 Unprocessable Entity):** Invalid `max_length` parameter

**Note:** Summaries are generated using OpenAI GPT-4o-mini. If OpenAI is unavailable, a fallback extractive summary (first sentences) is used. Summaries are cached in the database.

---

### Search

#### GET `/search`
Search across clients and/or documents using hybrid search (keyword + semantic similarity).

**Query Parameters:**
- `q` (string, required) - Search query string
- `type` (enum, default: `all`) - Search type: `all`, `clients`, or `documents`
- `limit` (integer, default: 10) - Maximum number of results per type (min: 1, max: 100)
- `semantic` (boolean, default: true) - Use semantic search for documents (currently always enabled)

**Response:**
```json
{
  "query": "machine learning",
  "search_type": "all",
  "clients": [
    {
      "id": "client-12345678-1234-5678-1234-567812345678",
      "first_name": "John",
      "last_name": "Doe",
      "email": "john.doe@neviswealth.com",
      "description": "ML researcher",
      "match_score": 0.5,
      "match_field": "description"
    }
  ],
  "documents": [
    {
      "id": "doc-87654321-4321-8765-4321-876543218765",
      "client_id": "client-12345678-1234-5678-1234-567812345678",
      "title": "Attention all you need",
      "content": "The dominant sequence transduction models...",
      "created_at": "2024-01-15T10:35:00Z",
      "match_score": 0.75,
      "match_field": "semantic"
    }
  ],
  "total_results": 2
}
```

**Error (400 Bad Request):** Empty search query or invalid limit

**Error (422 Unprocessable Entity):** Invalid `type` parameter

#### Search Features

1. **Client Search:**
   - Keyword-based search across email, first name, last name, and description
   - Case-insensitive matching
   - Scoring: Exact matches > Starts with > Contains

2. **Document Search (Hybrid):**
   - **Keyword Search:** Matches words in title and content
   - **Semantic Search:** Uses vector embeddings to find semantically similar documents
   - **Combination:** Results are combined with weighted scores (40% keyword, 60% semantic)
   - Semantic similarity threshold: 0.15 (configurable via `SEMANTIC_SIMILARITY_THRESHOLD`)

3. **Match Scores:**
   - Range: 0.0 to 1.0
   - Higher scores indicate better matches
   - Results are sorted by score (descending)

4. **Match Fields:**
   - Clients: `email`, `name`, or `description`
   - Documents: `title`, `content`, `semantic`, or `hybrid`

---

## Data Models

### Client
```json
{
  "id": "string (UUID format: client-*)",
  "first_name": "string",
  "last_name": "string",
  "email": "string (email format)",
  "description": "string | null",
  "created_at": "datetime (ISO 8601)"
}
```

### Document
```json
{
  "id": "string (UUID format: doc-*)",
  "client_id": "string (UUID format: client-*)",
  "title": "string",
  "content": "string",
  "created_at": "datetime (ISO 8601)"
}
```

### Paginated Response
```json
{
  "items": "array of items",
  "total": "integer",
  "offset": "integer",
  "limit": "integer",
  "has_next": "boolean",
  "has_previous": "boolean"
}
```

### Search Result (Client)
```json
{
  "id": "string",
  "first_name": "string",
  "last_name": "string",
  "email": "string",
  "description": "string | null",
  "match_score": "float (0.0-1.0)",
  "match_field": "string (email|name|description)"
}
```

### Search Result (Document)
```json
{
  "id": "string",
  "client_id": "string",
  "title": "string",
  "content": "string",
  "created_at": "datetime",
  "match_score": "float (0.0-1.0)",
  "match_field": "string (title|content|semantic|hybrid)"
}
```

---

## Error Responses

All error responses follow this format:

```json
{
  "detail": "Error message or validation details"
}
```

### HTTP Status Codes

- **200 OK** - Success
- **201 Created** - Resource created successfully
- **400 Bad Request** - Invalid request (e.g., duplicate email, empty search query)
- **404 Not Found** - Resource not found
- **422 Unprocessable Entity** - Validation error
- **503 Service Unavailable** - Service error (database or OpenAI unavailable)

---

## Rate Limits

Currently, there are no rate limits enforced. However, consider the following:

- **Document Creation:** Embedding generation may take a few seconds per document
- **Summary Generation:** Uses OpenAI API (rate limits depend on your OpenAI plan)
- **Search:** Vector similarity search is optimized with HNSW indexing for fast queries

---

## Environment Variables

- `DATABASE_URL` - PostgreSQL connection string (required)
- `OPENAI_API_KEY` - OpenAI API key for summarization (optional, fallback summary used if not set)
- `SEMANTIC_SIMILARITY_THRESHOLD` - Semantic search threshold (default: 0.15, range: 0.0-1.0)

---

## Examples

See [API_EXAMPLES.md](./API_EXAMPLES.md) for detailed request/response examples.

---

## Support

For issues or questions, please refer to the repository or contact the development team.


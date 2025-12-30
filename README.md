# Nevis Search API

WealthTech search API for clients and documents with semantic search capabilities.

**Current production URL: https://nevissearchapi-production.up.railway.app/docs**


## Features

- Client and document management
- Hybrid search (keyword + semantic similarity)
- Document summarization with OpenAI
- Vector embeddings for semantic search

## Development

### Prerequisites

- Docker and Docker Compose

### Running Locally

1. Start services:
```bash
docker-compose up -d
```

2. Run tests:
```bash
# With Docker Compose (starts db service, runs tests in one-off container)
# No need to install Python dependencies locally!
./scripts/run_tests.sh docker

# Or directly with docker-compose:
docker-compose up -d db --remove-orphans
docker-compose run --rm -e DATABASE_URL=postgresql://postgres:postgres@db:5432/nevis_search api pytest tests/ -v

# Or with local PostgreSQL + local Python (requires local setup)
./scripts/run_tests.sh local
```

3. API will be available at http://localhost:8000
4. Interactive API documentation:
   - Swagger UI: http://localhost:8000/docs
   - ReDoc: http://localhost:8000/redoc
5. Additional documentation:
   - [API Documentation](./API_DOCUMENTATION.md) - Complete API reference
   - [API Examples](./API_EXAMPLES.md) - Example queries and responses

### Environment Variables

- `DATABASE_URL` - PostgreSQL connection string
- `OPENAI_API_KEY` - OpenAI API key for summarization
- `SEMANTIC_SIMILARITY_THRESHOLD` - Semantic search threshold (default: 0.15)

## CI/CD

### GitHub Actions

Tests run automatically on:
- Push to `main` or `develop` branches
- Pull requests to `main` or `develop`

The CI pipeline:
1. Sets up PostgreSQL with pgvector
2. Installs dependencies
3. Runs all tests with coverage
4. Uploads coverage reports

### Running Tests Before Deployment

Tests are automatically run in GitHub Actions before any deployment. To run locally:

```bash
# Using Docker Compose (recommended - only starts db service)
./scripts/run_tests.sh docker

# Or with local PostgreSQL (no Docker required)
./scripts/run_tests.sh local
```

## Deployment

### Railway

1. Deploy pgvector service - https://railway.com/deploy/3jJFCA
2. Deploy GitHub code
3. Add environment variables to the deployed NevisSearchAPI service:
   - `DATABASE_URL` - `${{ pgvector.DATABASE_URL_PRIVATE }}`
   - `OPENAI_API_KEY` - Your OpenAI API key (you can take one from docker-compose.yml, in future it should be made private)
   - `SEMANTIC_SIMILARITY_THRESHOLD` - Optional (default: 0.15), so we could callibrate this withouth redeployment

**Current production URL: https://nevissearchapi-production.up.railway.app/docs**

## Improvements to make

0. ✅ Refactor search (completed)
1. ✅ Add pagination (completed)
2. Add async - if multiple advisors are going to access same data, we should add async support
3. ✅ Add testing workflow (completed)
4. Make docker image smaller, use python-slim instead of python docker image
5. Make embedding creation run in background (takes too long to add document)
   - Maybe have it batched and processed in batches
   - Have queue that does that
   - Run on GPU
6. Migrate from Postgres to FAISS when we get a lot of docs

#!/bin/bash
# Script to run tests locally
# Usage: ./scripts/run_tests.sh [docker|local]

set -e

MODE=${1:-docker}

if [ "$MODE" == "docker" ]; then
    echo "Running tests with Docker Compose..."
    docker-compose up -d db
    echo "Waiting for database to be ready..."
    sleep 5
    echo "Running tests in Docker container (one-off)..."
    docker-compose run --rm -e TEST_DATABASE_URL=postgresql://postgres:postgres@db:5432/nevis_search api pytest tests/ -v
elif [ "$MODE" == "local" ]; then
    echo "Running tests with local PostgreSQL..."
    if [ -z "$TEST_DATABASE_URL" ]; then
        export TEST_DATABASE_URL="postgresql://postgres:postgres@localhost:5432/nevis_search"
    fi
    echo "Using DATABASE_URL: $TEST_DATABASE_URL"
    pytest tests/ -v
else
    echo "Usage: $0 [docker|local]"
    exit 1
fi


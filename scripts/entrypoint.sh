#!/bin/bash
set -e

echo "========================================"
echo "Running tests..."
echo "========================================"

# Run tests
pytest tests/ -v --tb=short

if [ $? -eq 0 ]; then
    echo "========================================"
    echo "✅ All tests passed! Starting API..."
    echo "========================================"
else
    echo "========================================"
    echo "❌ Tests failed! Fix tests before starting API"
    echo "========================================"
    exit 1
fi

# Start the application
exec "$@"
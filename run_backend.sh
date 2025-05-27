#!/bin/bash

# Script to run the FastAPI backend server
# Usage: ./run_backend.sh [port]

PORT=${1:-8001}
BACKEND_DIR="$(dirname "$0")/backend"

echo "Starting FastAPI server on port $PORT..."
echo "Backend directory: $BACKEND_DIR"

cd "$BACKEND_DIR" || exit 1

# Check if virtual environment is activated
if [[ "$VIRTUAL_ENV" == "" ]]; then
    echo "Warning: No virtual environment detected. Make sure you have the required dependencies installed."
fi

# Run the server
uvicorn server:app --host 0.0.0.0 --port "$PORT" --reload 
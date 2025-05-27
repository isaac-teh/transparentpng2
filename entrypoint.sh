#!/bin/bash
set -e

# Debug: Show environment
echo "PATH: $PATH"
echo "Python version: $(python3 --version)"
echo "Checking uvicorn..."
python3 -c "import uvicorn; print(f'uvicorn version: {uvicorn.__version__}')" || echo "uvicorn import failed"

# Start the FastAPI backend
cd /backend || { echo "Backend directory not found"; exit 1; }

echo "Starting FastAPI backend"
# Use python -m uvicorn for reliability
python3 -m uvicorn server:app --host 0.0.0.0 --port 8001 &
BACKEND_PID=$!

echo "Waiting for backend to start..."
sleep 10

# Check if backend process is still running
if ! kill -0 $BACKEND_PID 2>/dev/null; then
    echo "Backend process died during startup, exiting"
    exit 1
fi

# Wait for backend to be ready by checking the health endpoint
echo "Checking backend health..."
for i in {1..30}; do
    if curl -f http://127.0.0.1:8001/api/ >/dev/null 2>&1; then
        echo "Backend is ready!"
        break
    fi
    if [ $i -eq 30 ]; then
        echo "Backend failed to become ready after 30 attempts, exiting"
        exit 1
    fi
    echo "Attempt $i/30: Backend not ready yet, waiting..."
    sleep 2
done

# Start Nginx
nginx -g 'daemon off;' &
NGINX_PID=$!

# Handle termination signals
trap 'kill $BACKEND_PID $NGINX_PID; exit 0' SIGTERM SIGINT

# Check if processes are still running
while kill -0 $BACKEND_PID 2>/dev/null && kill -0 $NGINX_PID 2>/dev/null; do
    sleep 1
done

# If we get here, one of the processes died
if kill -0 $BACKEND_PID 2>/dev/null; then
    echo "Nginx died, shutting down backend..."
    kill $BACKEND_PID
else
    echo "Backend died, shutting down nginx..."
    kill $NGINX_PID
fi

exit 1

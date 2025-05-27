#!/bin/bash

echo "Building Docker image..."
docker build -t transparentpng2-test .

if [ $? -ne 0 ]; then
    echo "Docker build failed!"
    exit 1
fi

echo "Running Docker container..."
docker run -p 8080:8080 --name transparentpng2-test-container transparentpng2-test &
CONTAINER_PID=$!

echo "Waiting for container to start..."
sleep 15

echo "Testing endpoints..."
curl -f http://localhost:8080/ && echo "✓ Frontend accessible"
curl -f http://localhost:8080/api/ && echo "✓ Backend API accessible"

echo "Stopping container..."
docker stop transparentpng2-test-container
docker rm transparentpng2-test-container

echo "Test completed!" 
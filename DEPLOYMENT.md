# Deployment Guide

## Issue Resolution

The original error `uvicorn: not found` and `libpython3.11.so.1.0: cannot open shared object file` were caused by incompatible base images in the multi-stage Docker build.

### Root Cause
- Copying Python binaries from `python:3.11-slim` (Debian-based) to `nginx:stable-alpine` (Alpine-based)
- Missing shared libraries and incompatible binary formats

### Solution
- Changed final stage to use `python:3.11-slim` as base image
- Install nginx on top of Python image instead of copying Python to nginx image
- This ensures all Python dependencies and shared libraries are properly available
- Pre-download AI model during build to improve first-time performance
- Configure nginx with proper file upload limits (25MB) and timeouts

## Local Testing

**Note**: The Docker build now takes longer (~90 seconds) due to AI model pre-download, but this significantly improves runtime performance.

Before deploying to Cloud Run, test locally:

```bash
# Build the image
docker build -t transparentpng2 .

# Run locally
docker run -p 8080:8080 --name transparentpng2-local transparentpng2

# Test endpoints
curl http://localhost:8080/                    # Frontend
curl http://localhost:8080/api/                # Backend API

# Clean up
docker stop transparentpng2-local && docker rm transparentpng2-local
```

Or use the provided test script:
```bash
./test-docker.sh
```

## Cloud Run Deployment

### Option 1: Using gcloud CLI

```bash
# Build and push to Google Container Registry
gcloud builds submit --tag gcr.io/YOUR_PROJECT_ID/transparentpng2

# Deploy to Cloud Run
gcloud run deploy transparentpng2 \
  --image gcr.io/YOUR_PROJECT_ID/transparentpng2 \
  --platform managed \
  --region YOUR_REGION \
  --allow-unauthenticated \
  --port 8080 \
  --memory 2Gi \
  --cpu 2 \
  --timeout 300
```

### Option 2: Using Cloud Build

Create a `cloudbuild.yaml`:

```yaml
steps:
  - name: 'gcr.io/cloud-builders/docker'
    args: ['build', '-t', 'gcr.io/$PROJECT_ID/transparentpng2', '.']
  - name: 'gcr.io/cloud-builders/docker'
    args: ['push', 'gcr.io/$PROJECT_ID/transparentpng2']
  - name: 'gcr.io/google.com/cloudsdktool/cloud-sdk'
    entrypoint: gcloud
    args:
      - 'run'
      - 'deploy'
      - 'transparentpng2'
      - '--image'
      - 'gcr.io/$PROJECT_ID/transparentpng2'
      - '--region'
      - 'YOUR_REGION'
      - '--platform'
      - 'managed'
      - '--allow-unauthenticated'
      - '--port'
      - '8080'
```

Then run:
```bash
gcloud builds submit --config cloudbuild.yaml
```

## Key Configuration

### Environment Variables
If you need to set environment variables for your backend, add them to the Cloud Run service:

```bash
gcloud run services update transparentpng2 \
  --set-env-vars="MONGO_URL=your_mongo_url,DB_NAME=your_db_name"
```

### Resource Allocation
- **Memory**: 2Gi (recommended for image processing)
- **CPU**: 2 (recommended for AI model inference)
- **Timeout**: 300s (for large image processing)
- **Concurrency**: 10-50 (depending on your needs)

### Performance Optimizations
- **Pre-downloaded AI Model**: The u2net.onnx model (~176MB) is downloaded during build time, not runtime
- **Fast Startup**: No model download delay on first image processing
- **Large File Support**: Nginx configured to handle up to 25MB image uploads
- **Optimized Timeouts**: Extended proxy timeouts for large image processing

### Health Check
The container includes a health check that verifies both nginx and the backend are running:
- Health check endpoint: `http://localhost:8080/`
- Startup period: 60s
- Check interval: 30s

## Troubleshooting

### Container Logs
Check Cloud Run logs if deployment fails:
```bash
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=transparentpng2" --limit 50
```

### Common Issues
1. **Port Configuration**: Ensure Cloud Run is configured to use port 8080
2. **Memory Limits**: Image processing requires sufficient memory (2Gi recommended)
3. **Timeout**: Large images may need longer processing time
4. **Dependencies**: All Python packages are included in the image

### Local Debugging
If issues persist, debug locally:
```bash
docker run -it --entrypoint /bin/bash transparentpng2
# Then manually run commands to debug
```

## Architecture

```
Cloud Run Container:
├── nginx (port 8080) - Serves frontend and proxies API
│   ├── Frontend (React app) - /
│   └── API Proxy - /api/* → http://localhost:8001
└── FastAPI Backend (port 8001) - Background removal service
    ├── /api/ - Health check
    ├── /api/remove-background - Image processing
    └── /api/remove-background-base64 - Base64 response
```

The container successfully starts both services and handles requests properly. 
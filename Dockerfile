# Stage 1: Build React App
FROM node:20 AS frontend-build
ARG FRONTEND_ENV
ENV FRONTEND_ENV=${FRONTEND_ENV}
WORKDIR /app
COPY frontend/ /app/
RUN rm /app/.env
RUN touch /app/.env
RUN echo "${FRONTEND_ENV}" | tr ',' '\n' > /app/.env
RUN cat /app/.env
RUN yarn install --frozen-lockfile && yarn build

# Stage 2: Install Python Backend
FROM python:3.11-slim AS backend
WORKDIR /app
COPY backend/ /app/
COPY download_model.py /app/
RUN rm /app/.env
RUN pip install --no-cache-dir -r requirements.txt

# Pre-download the AI model to improve first-time performance
RUN python3 /app/download_model.py

# Stage 3: Final Image - Use Python base with nginx
FROM python:3.11-slim
# Install nginx
RUN apt-get update && apt-get install -y nginx bash curl && \
    rm -rf /var/lib/apt/lists/*

# Copy built frontend
COPY --from=frontend-build /app/build /usr/share/nginx/html
# Copy backend
COPY --from=backend /app /backend
COPY --from=backend /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=backend /usr/local/bin /usr/local/bin
# Copy pre-downloaded AI model
COPY --from=backend /root/.u2net /root/.u2net

# Copy nginx config
COPY nginx.conf /etc/nginx/nginx.conf
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Add env variables if needed
ENV PYTHONUNBUFFERED=1

# Add health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8080/ || exit 1

# Start both services: Uvicorn and Nginx
CMD ["/entrypoint.sh"]

# =====================================================================
# VoiceNexus Conversational IVR Platform - Production Dockerfile
# =====================================================================

# Stage 1: Build the React 19 Frontend
FROM node:22-alpine AS frontend-builder
WORKDIR /app/frontend

COPY frontend/package*.json ./
RUN npm ci

COPY frontend/ ./
RUN npm run build

# Stage 2: Python Backend Runtime
FROM python:3.12-slim AS runtime

# System dependencies for audio handling and healthcheck
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python requirements
COPY backend/requirements.txt ./backend/
RUN pip install --no-cache-dir -r backend/requirements.txt

# Copy Backend Source Code
COPY backend/ ./backend/

# Copy Built Static Assets from Stage 1 into the location expected by FastAPI
COPY --from=frontend-builder /app/frontend/dist ./frontend/dist

# Set Python Path & Low-Memory Environment Defaults
ENV PYTHONPATH=/app/backend
ENV PYTHONUNBUFFERED=1
ENV HOST=0.0.0.0
ENV PORT=8000
ENV STT_ENABLED=false
ENV STT_MODEL_SIZE=tiny
ENV MALLOC_ARENA_MAX=2
ENV WEB_CONCURRENCY=1

# Expose Port 8000 for HTTP and WebSockets
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD curl -f http://localhost:${PORT:-8000}/api/health || exit 1

WORKDIR /app/backend
CMD ["sh", "-c", "python -m uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]

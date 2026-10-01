# Production Dockerfile for Requirement Conflict & Overlap Analyzer
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8000 \
    HOST=0.0.0.0 \
    ENVIRONMENT=production

# Install system dependencies (build-essential for C extensions, libpq, etc.)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Install python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application source code
COPY backend/ ./backend/
COPY frontend/ ./frontend/
COPY sample_data/ ./sample_data/
COPY run_server.py .
COPY .env.example .env

# Create non-root user and setup directories
RUN useradd -m -u 1000 appuser && \
    mkdir -p data/uploads data/db && \
    chown -R appuser:appuser /app

USER appuser

# Expose server port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/api/health || exit 1

# Start Uvicorn production server
CMD ["python", "run_server.py"]

# Dockerfile
# Backend Docker container configuration with all dependencies

FROM python:3.11-slim

WORKDIR /app

# Install system dependencies including curl for health checks
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies directly (without Poetry for simpler Docker build)
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create directories for uploads and logs
RUN mkdir -p /app/uploads /app/logs

# Create non-root user for security
RUN useradd --create-home --shell /bin/bash app \
    && chown -R app:app /app
USER app

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Start the application server
# Railway provides $PORT dynamically, defaults to 8000 for local development
# The shell form with sh -c is required to expand environment variables
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
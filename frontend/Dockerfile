FROM python:3.11-slim-bullseye

# Security: Set metadata
LABEL maintainer="Object Detection Team"
LABEL description="Real-Time Object Detection API with YOLOv8"

# Security: Do not run as root
RUN useradd -m -u 1000 appuser

WORKDIR /app

# Install system dependencies with minimal footprint
RUN apt-get update && apt-get install -y --no-install-recommends \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libglib2.0-0 \
    libgl1-mesa-glx \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install with --no-cache-dir for security
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -r requirements.txt

# Copy application code (use .dockerignore to exclude sensitive files)
COPY --chown=appuser:appuser backend/ ./backend/
COPY --chown=appuser:appuser src/ ./src/
COPY --chown=appuser:appuser .env.example .env

# Create logs directory with proper permissions
RUN mkdir -p logs && chown -R appuser:appuser logs

# Security: Switch to non-root user
USER appuser

# Expose ports
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/api/health')" || exit 1

# Run only FastAPI (not Gradio - should be separate container)
CMD ["python", "-m", "uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8000"]

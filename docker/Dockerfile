# ============================================================================
# MULTI-STAGE DOCKERFILE FOR OLLAMA API
# Elite Production Build with Security Hardening
# ============================================================================

# Build Arguments
ARG PYTHON_VERSION=3.11
ARG BUILD_DATE
ARG VCS_REF

# ============================================================================
# STAGE 1: Base Image
# ============================================================================
FROM python:${PYTHON_VERSION}-slim as base

# Metadata
LABEL maintainer="Elevated IQ <admin@elevatediq.ai>"
LABEL org.opencontainers.image.title="Ollama API"
LABEL org.opencontainers.image.description="Elite AI Inference Platform"
LABEL org.opencontainers.image.version="1.0.0"
LABEL org.opencontainers.image.created="${BUILD_DATE}"
LABEL org.opencontainers.image.revision="${VCS_REF}"
LABEL org.opencontainers.image.url="https://elevatediq.ai"
LABEL org.opencontainers.image.source="https://github.com/kushin77/ollama"

# Environment Variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONFAULTHANDLER=1 \
    PYTHONHASHSEED=random \
    PIP_NO_CACHE_DIR=off \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    PIP_DEFAULT_TIMEOUT=100

# System dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# ============================================================================
# STAGE 2: Builder
# ============================================================================
FROM base as builder

WORKDIR /build

# Copy project files
COPY pyproject.toml pyproject.toml
COPY README.md README.md
COPY ollama/ ollama/

# Install dependencies using pip (setuptools-based)
RUN pip install --upgrade pip setuptools wheel && \
    pip install -e . --no-cache-dir

# ============================================================================
# STAGE 3: Development
# ============================================================================
FROM base as development

WORKDIR /app

# Install pip dependencies from builder cache
RUN pip install --upgrade pip setuptools wheel

# Copy application code
COPY . .

# Install app in editable mode for development
RUN pip install -e . --no-cache-dir

# Create non-root user
RUN useradd -m -u 1000 -s /bin/bash ollama && \
    chown -R ollama:ollama /app

USER ollama

# Development command (with auto-reload)
CMD ["uvicorn", "ollama.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

# ============================================================================
# STAGE 4: Production (Minimal, Secure)
# ============================================================================
FROM base as production

# Runtime environment
ENV PATH="/venv/bin:$PATH"

# Runtime dependencies only
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Create directory structure
RUN mkdir -p /app /models /var/log/ollama /app/cache && \
    chmod 1777 /tmp /app/cache

# Install application from source
COPY . /app
WORKDIR /app

# Install dependencies (production-grade, no dev packages)
RUN pip install --upgrade pip setuptools wheel && \
    pip install -e . --no-cache-dir

# Create non-root user with specific UID
RUN useradd -m -u 1000 -s /bin/bash ollama && \
    chown -R ollama:ollama /app /models /var/log/ollama /app/cache

# Switch to non-root user
USER ollama

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Production command with uvicorn (no gunicorn to keep it simple)
CMD ["uvicorn", \
     "ollama.main:app", \
     "--host", "0.0.0.0", \
     "--port", "8000", \
     "--workers", "4"]

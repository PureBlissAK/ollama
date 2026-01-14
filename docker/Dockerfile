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
    PIP_DEFAULT_TIMEOUT=100 \
    POETRY_VERSION=1.7.1 \
    POETRY_HOME="/opt/poetry" \
    POETRY_VIRTUALENVS_IN_PROJECT=true \
    POETRY_NO_INTERACTION=1 \
    PYSETUP_PATH="/opt/pysetup" \
    VENV_PATH="/opt/pysetup/.venv"

# Update PATH
ENV PATH="$POETRY_HOME/bin:$VENV_PATH/bin:$PATH"

# System dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN curl -sSL https://install.python-poetry.org | python3 -

# ============================================================================
# STAGE 2: Builder
# ============================================================================
FROM base as builder

WORKDIR /build

# Copy project files
COPY setup.py setup.py
COPY README.md README.md
COPY pyproject.toml pyproject.toml
COPY requirements/ requirements/
COPY ollama/ ollama/

# Install dependencies
RUN pip install --upgrade pip setuptools wheel && \
    pip install -e . --no-cache-dir

# Copy dependency files
COPY pyproject.toml poetry.lock ./

# Install dependencies (no dev packages)
RUN poetry install --no-dev --no-root

# ============================================================================
# STAGE 3: Development
# ============================================================================
FROM base as development

# Copy virtual environment from builder
COPY --from=builder $PYSETUP_PATH $PYSETUP_PATH

WORKDIR /app

# Install development dependencies
COPY pyproject.toml poetry.lock ./
RUN poetry install

# Copy application code
COPY . .

# Create non-root user
RUN useradd -m -u 1000 -s /bin/bash ollama && \
    chown -R ollama:ollama /app

USER ollama

# Development command
CMD ["uvicorn", "ollama.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

# ============================================================================
# STAGE 4: Production (Minimal, Secure)
# ============================================================================
FROM python:${PYTHON_VERSION}-slim as production

# Environment
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/venv/bin:$PATH"

# Runtime dependencies only
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Copy virtual environment from builder
COPY --from=builder /opt/pysetup/.venv /venv

# Create directory structure
RUN mkdir -p /app /models /var/log/ollama /app/cache && \
    chmod 1777 /tmp /app/cache

# Create non-root user with specific UID
RUN useradd -m -u 1000 -s /bin/bash ollama && \
    chown -R ollama:ollama /app /models /var/log/ollama /app/cache

WORKDIR /app

# Copy application code
COPY --chown=ollama:ollama . .

# Switch to non-root user
USER ollama

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Production command with production-grade settings
CMD ["gunicorn", \
     "ollama.main:app", \
     "--workers", "8", \
     "--worker-class", "uvicorn.workers.UvicornWorker", \
     "--bind", "0.0.0.0:8000", \
     "--access-logfile", "-", \
     "--error-logfile", "-", \
     "--log-level", "info", \
     "--timeout", "300", \
     "--keepalive", "5", \
     "--max-requests", "10000", \
     "--max-requests-jitter", "1000"]

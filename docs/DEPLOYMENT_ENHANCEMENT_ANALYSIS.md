# Deployment Architecture Enhancement Analysis

**Date**: January 13, 2026  
**Status**: Comprehensive Infrastructure Assessment  
**Scope**: Security, Robustness, Cost Optimization, Immutable Infrastructure  

---

## Executive Summary

The Ollama platform has evolved through multiple deployment configurations (Docker Compose variants + Kubernetes manifests with Kustomize). The current architecture demonstrates good foundational patterns (multi-stage Docker builds, health checks, persistent volumes) but requires systematic hardening across four critical dimensions.

### Current State Assessment

| Dimension | Maturity | Priority |
|-----------|----------|----------|
| **Security** | 🟡 Medium (hardcoded secrets, debug mode enabled) | 🔴 CRITICAL |
| **Robustness** | 🟢 Good (health checks, restart policies in prod) | 🟡 MEDIUM |
| **Cost Optimization** | 🔴 Poor (no resource limits, uncontrolled scaling) | 🟡 MEDIUM |
| **Immutable Infrastructure** | 🟡 Partial (Kustomize + K8s, but loose image tags) | 🔴 CRITICAL |

---

## 1. SECURITY ENHANCEMENTS

### 1.1 Critical Issues Identified

#### Issue 1: Hardcoded Credentials in Development Compose
**Severity**: 🔴 CRITICAL  
**Files**: `docker-compose.yml`  
**Current State**:
```yaml
postgres:
  environment:
    POSTGRES_PASSWORD: ollama_dev  # Hardcoded
    
api:
  environment:
    SECRET_KEY: dev-secret-key-change-in-production  # Placeholder
    JWT_ALGORITHM: HS256
```

**Impact**: Credentials committed to version control; development secrets could leak into production if file isn't properly excluded.

**Recommended Solution**:
```yaml
# docker-compose.yml (SECURE)
version: '3.8'

services:
  postgres:
    image: postgres:15-alpine
    environment:
      POSTGRES_USER: ${POSTGRES_USER:-ollama}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}  # Required from .env
      POSTGRES_DB: ${POSTGRES_DB:-ollama}
      
  api:
    environment:
      DATABASE_URL: ${DATABASE_URL}  # Required
      REDIS_URL: ${REDIS_URL}  # Required
      SECRET_KEY: ${SECRET_KEY}  # Required (min 32 chars)
      ENVIRONMENT: ${ENVIRONMENT:-development}
      DEBUG: ${DEBUG:-false}  # Never true in prod
```

**Implementation Steps**:
1. Create `.env.example` with placeholder values:
   ```bash
   # .env.example - NEVER commit actual values
   POSTGRES_USER=ollama
   POSTGRES_PASSWORD=<generate-32-char-random-string>
   POSTGRES_DB=ollama
   DATABASE_URL=postgresql+asyncpg://ollama:${POSTGRES_PASSWORD}@postgres:5432/ollama
   
   REDIS_PASSWORD=<generate-32-char-random-string>
   REDIS_URL=redis://:${REDIS_PASSWORD}@redis:6379/0
   
   SECRET_KEY=<generate-64-char-random-string>
   JWT_ALGORITHM=HS256
   JWT_EXPIRATION_HOURS=24
   
   ENVIRONMENT=production
   DEBUG=false
   LOG_LEVEL=INFO
   
   QDRANT_API_KEY=<generate-api-key>
   GRAFANA_ADMIN_PASSWORD=<generate-secure-password>
   ```

2. Add to `.gitignore`:
   ```bash
   # Secrets
   .env
   .env.*.local
   
   # Credentials
   secrets/
   **/secrets.yaml
   ```

3. Generate secure values for each environment:
   ```bash
   # Generate 32-char random password
   openssl rand -hex 16
   
   # Generate 64-char random secret
   openssl rand -hex 32
   ```

#### Issue 2: Debug Mode Enabled in Development
**Severity**: 🟡 HIGH  
**Files**: `docker-compose.yml`, `app/main.py`  
**Current State**:
```yaml
api:
  environment:
    DEBUG: "true"  # Exposes stack traces, internal state
```

**Impact**: Stack traces leaked to clients; sensitive information exposure; performance degradation.

**Recommended Solution**:
```python
# ollama/main.py - Conditional debug configuration
from fastapi import FastAPI
from starlette.middleware import Middleware
from starlette.middleware.errors import ServerErrorMiddleware
import os

DEBUG = os.getenv("DEBUG", "false").lower() == "true"
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")

app = FastAPI(
    title="Ollama API",
    debug=DEBUG and ENVIRONMENT == "development",  # Only debug in dev mode
    docs_url="/docs" if ENVIRONMENT == "development" else None,  # Hide Swagger in prod
    redoc_url="/redoc" if ENVIRONMENT == "development" else None,  # Hide ReDoc in prod
    openapi_url="/openapi.json" if ENVIRONMENT == "development" else None,
)

# Custom error handler for production
@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    if DEBUG:
        raise  # Re-raise to get full traceback in development
    
    # Production: return generic error
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": {
                "code": "INTERNAL_SERVER_ERROR",
                "message": "An unexpected error occurred",
            },
            "metadata": {
                "request_id": request.headers.get("x-request-id", "unknown"),
                "timestamp": datetime.utcnow().isoformat(),
            }
        }
    )
```

---

#### Issue 3: Image Tags Not Pinned
**Severity**: 🔴 CRITICAL  
**Files**: All docker-compose files, K8s manifests  
**Current State**:
```yaml
services:
  ollama:
    image: ollama/ollama:latest  # Unpredictable updates
  qdrant:
    image: qdrant/qdrant:latest  # Breaks immutability
  prometheus:
    image: prom/prometheus:latest  # No version control
```

**Impact**: 
- Non-deterministic deployments (different versions on different runs)
- Security vulnerabilities in unexpectedly updated images
- Cannot reliably roll back to previous versions
- Violates immutable infrastructure principles

**Recommended Solution**:
```yaml
# docker-compose.yml - PINNED VERSIONS WITH DIGESTS
services:
  postgres:
    image: postgres:15-alpine@sha256:a1b2c3d4e5f6...  # Pin to specific digest
    # Retrieve digest: docker pull postgres:15-alpine && docker inspect --format='{{.RepoDigests}}' postgres:15-alpine
    
  redis:
    image: redis:7-alpine@sha256:f1g2h3i4j5k6...
    
  qdrant:
    image: qdrant/qdrant:v1.7.0@sha256:m1n2o3p4q5r6...
    
  ollama:
    image: ollama/ollama:0.1.32@sha256:s1t2u3v4w5x6...
```

**Implementation Steps**:
1. Create version pinning script:
   ```bash
   # scripts/pin-image-versions.sh
   #!/bin/bash
   
   declare -A IMAGES=(
     ["postgres"]="15-alpine"
     ["redis"]="7-alpine"
     ["qdrant/qdrant"]="v1.7.0"
     ["ollama/ollama"]="0.1.32"
     ["prom/prometheus"]="v2.50.0"
     ["grafana/grafana"]="10.2.2"
     ["jaegertracing/all-in-one"]="v1.51.0"
   )
   
   for image in "${!IMAGES[@]}"; do
     tag="${IMAGES[$image]}"
     full_image="${image}:${tag}"
     echo "Pulling $full_image..."
     docker pull "$full_image"
     
     digest=$(docker inspect --format='{{index .RepoDigests 0}}' "$full_image" | cut -d'@' -f2)
     echo "${image}:${tag}@${digest}"
   done
   ```

2. Update docker-compose files to use pinned versions:
   ```yaml
   # Generate new versions via script above
   # Store in environment variables or directly in YAML
   ```

3. Document version strategy:
   - Update pinned versions monthly
   - Test updates in staging first
   - Create PRs for version bumps with changelog

---

#### Issue 4: No TLS/HTTPS for Local Services
**Severity**: 🟡 HIGH  
**Context**: Services communicate over plain HTTP  
**Files**: `docker-compose.yml`, K8s manifests  

**Impact**: Network traffic sniffable; no mutual authentication between services.

**Recommended Solution**:
```yaml
# docker-compose.yml - Add mTLS for internal communication
services:
  postgres:
    # PostgreSQL native SSL
    environment:
      POSTGRES_INITDB_ARGS: "-c ssl=on -c ssl_cert_file=/etc/ssl/postgresql.crt -c ssl_key_file=/etc/ssl/postgresql.key"
    volumes:
      - ./certs/postgres:/etc/ssl:ro
      
  redis:
    # Redis with TLS
    command: redis-server --tls-port 6379 --port 0 --tls-cert-file /etc/redis/tls/cert.pem --tls-key-file /etc/redis/tls/key.pem --tls-ca-cert-file /etc/redis/tls/ca.pem
    volumes:
      - ./certs/redis:/etc/redis/tls:ro
      
  api:
    environment:
      # Use TLS URLs
      REDIS_URL: rediss://:${REDIS_PASSWORD}@redis:6379/0
      DATABASE_URL: postgresql+asyncpg://ollama:${POSTGRES_PASSWORD}@postgres:5432/ollama?sslmode=require
```

**Implementation**:
```bash
# scripts/generate-certs.sh
#!/bin/bash

# Generate self-signed certificates for local development
mkdir -p ./certs/{postgres,redis}

# PostgreSQL
openssl req -x509 -days 365 -nodes -newkey rsa:2048 \
  -keyout ./certs/postgres/server.key \
  -out ./certs/postgres/server.crt \
  -subj "/CN=postgres"
chmod 600 ./certs/postgres/server.key

# Redis
openssl genrsa -out ./certs/redis/ca-key.pem 4096
openssl req -x509 -new -days 365 -nodes \
  -in ./certs/redis/ca-key.pem \
  -out ./certs/redis/ca.pem \
  -subj "/CN=redis-ca"

openssl genrsa -out ./certs/redis/key.pem 4096
openssl req -new -days 365 \
  -key ./certs/redis/key.pem \
  -out ./certs/redis/cert.csr \
  -subj "/CN=redis"

openssl x509 -req -in ./certs/redis/cert.csr \
  -CA ./certs/redis/ca.pem \
  -CAkey ./certs/redis/ca-key.pem \
  -CAcreateserial \
  -out ./certs/redis/cert.pem \
  -days 365
```

---

### 1.2 Secrets Management Architecture

**Recommended Pattern**:

```python
# ollama/config/secrets.py
from typing import Optional
import os
from pydantic import BaseSettings, SecretStr, Field

class SecretsConfig(BaseSettings):
    """
    Secrets configuration - NEVER logs these values.
    Sourced from environment variables, never from files or defaults.
    """
    
    # Database
    postgres_password: SecretStr = Field(..., env="POSTGRES_PASSWORD")
    database_url: SecretStr = Field(..., env="DATABASE_URL")
    
    # Cache
    redis_password: SecretStr = Field(..., env="REDIS_PASSWORD")
    redis_url: SecretStr = Field(..., env="REDIS_URL")
    
    # Security
    secret_key: SecretStr = Field(..., min_length=64, env="SECRET_KEY")
    jwt_algorithm: str = Field(default="HS256", env="JWT_ALGORITHM")
    api_key_prefix: str = Field(default="sk", env="API_KEY_PREFIX")
    
    # Vector Database
    qdrant_api_key: Optional[SecretStr] = Field(default=None, env="QDRANT_API_KEY")
    
    class Config:
        env_file = ".env"
        case_sensitive = False
        # CRITICAL: Never expose in logs
        json_encoders = {
            SecretStr: lambda v: "***" if v else None
        }
    
    def __repr__(self) -> str:
        """Override to prevent accidental exposure in logs."""
        return f"<SecretsConfig(***)>"

# Usage:
# secrets = SecretsConfig()  # Validates all required fields present
# db_password = secrets.postgres_password.get_secret_value()
```

**Environment Variable Validation**:
```python
# ollama/startup.py
import sys
from ollama.config.secrets import SecretsConfig
from pydantic import ValidationError

def validate_environment() -> SecretsConfig:
    """Validate all required environment variables on startup."""
    try:
        secrets = SecretsConfig()
        print("✓ All required secrets configured")
        return secrets
    except ValidationError as e:
        for error in e.errors():
            field = error["loc"][0]
            msg = error["msg"]
            print(f"✗ Missing or invalid secret: {field} - {msg}")
        print("\nRequired environment variables:")
        print("  - POSTGRES_PASSWORD")
        print("  - DATABASE_URL")
        print("  - REDIS_PASSWORD")
        print("  - REDIS_URL")
        print("  - SECRET_KEY (min 64 characters)")
        sys.exit(1)

# In main.py startup:
@app.on_event("startup")
async def startup():
    app.state.secrets = validate_environment()
```

---

### 1.3 Security Scanning in CI/CD

**Add to GitHub Actions** (`.github/workflows/security.yml`):
```yaml
name: Security Scanning

on: [push, pull_request]

jobs:
  scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      # 1. Scan for committed secrets
      - uses: gitleaks/gitleaks-action@v2
      
      # 2. Container image scanning
      - uses: aquasecurity/trivy-action@master
        with:
          image-ref: 'ollama:latest'
          format: 'sarif'
          output: 'trivy-results.sarif'
      
      # 3. Dependency vulnerability check
      - run: pip-audit --desc
      
      # 4. SBOM generation
      - uses: anchore/sbom-action@v0
        with:
          output-file: sbom.spdx.json
      
      # 5. Security policy validation
      - name: Check for hardcoded credentials
        run: |
          ! grep -r "password.*=" docker-compose.yml | grep -v "^\${" || exit 1
          ! grep -r "SECRET_KEY.*=" docker-compose.yml | grep -v "^\${" || exit 1
```

---

## 2. ROBUSTNESS ENHANCEMENTS

### 2.1 Restart Policies

**Current Issue**: Development compose lacks restart policies.

**Recommended Solution**:

```yaml
# docker-compose.yml - ALL services should auto-restart
services:
  postgres:
    restart: unless-stopped  # Auto-restart on crash
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ollama"]
      interval: 10s
      timeout: 5s
      retries: 5
      start_period: 40s  # Wait before first check
      
  redis:
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 3s
      retries: 5
      start_period: 10s
      
  api:
    restart: on-failure:5  # Restart max 5 times on failure
    healthcheck:
      test: ["CMD", "curl", "-f", "--fail", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 60s
```

---

### 2.2 Resource Limits

**Current Issue**: No memory/CPU limits defined.

**Recommended Solution**:

```yaml
# docker-compose.yml - Resource reservations and limits
services:
  postgres:
    restart: unless-stopped
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 4G
        reservations:
          cpus: '1'
          memory: 2G
          
  redis:
    restart: unless-stopped
    deploy:
      resources:
        limits:
          cpus: '1'
          memory: 2G
        reservations:
          cpus: '0.5'
          memory: 1G
          
  ollama:
    restart: unless-stopped
    deploy:
      resources:
        limits:
          cpus: '4'
          memory: 16G
        reservations:
          cpus: '2'
          memory: 8G
          
  api:
    restart: on-failure:5
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 2G
        reservations:
          cpus: '1'
          memory: 1G
```

---

### 2.3 Health Check Improvements

**Pattern for production-grade health checks**:

```python
# ollama/api/routes/health.py
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from redis.asyncio import Redis
from datetime import datetime
from typing import Dict, Any

router = APIRouter(prefix="/health", tags=["health"])

async def check_database(db: AsyncSession) -> Dict[str, Any]:
    """Check database connectivity and performance."""
    try:
        start = datetime.utcnow()
        await db.execute("SELECT 1")
        latency = (datetime.utcnow() - start).total_seconds() * 1000
        
        return {
            "status": "healthy" if latency < 100 else "degraded",
            "latency_ms": latency,
            "message": "Database connection OK" if latency < 100 else "Slow response"
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "message": "Database connection failed"
        }

async def check_redis(redis: Redis) -> Dict[str, Any]:
    """Check Redis connectivity."""
    try:
        start = datetime.utcnow()
        await redis.ping()
        latency = (datetime.utcnow() - start).total_seconds() * 1000
        
        return {
            "status": "healthy" if latency < 50 else "degraded",
            "latency_ms": latency,
            "message": "Redis connection OK"
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "message": "Redis connection failed"
        }

@router.get("/")
async def health_check(
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis)
) -> Dict[str, Any]:
    """
    Health check endpoint - used by load balancers.
    Returns 200 OK if all dependencies healthy.
    """
    db_status = await check_database(db)
    redis_status = await check_redis(redis)
    
    # Overall status is worst of components
    overall_statuses = [db_status["status"], redis_status["status"]]
    if "unhealthy" in overall_statuses:
        overall = "unhealthy"
        http_status = 503  # Service Unavailable
    elif "degraded" in overall_statuses:
        overall = "degraded"
        http_status = 200  # Still OK, but monitoring should alert
    else:
        overall = "healthy"
        http_status = 200
    
    response = {
        "status": overall,
        "timestamp": datetime.utcnow().isoformat(),
        "checks": {
            "database": db_status,
            "cache": redis_status,
        },
        "version": "1.0.0"
    }
    
    return JSONResponse(status_code=http_status, content=response)

@router.get("/ready")
async def readiness_check(
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    Readiness check - is service ready to accept traffic?
    Stricter than liveness - fails if dependencies degraded.
    """
    try:
        await db.execute("SELECT 1")
        return {"ready": True}
    except Exception as e:
        raise HTTPException(status_code=503, detail="Service not ready")

@router.get("/live")
async def liveness_check() -> Dict[str, Any]:
    """
    Liveness check - is service process alive?
    Minimal check - should rarely fail.
    """
    return {"alive": True}
```

**Update health checks in docker-compose**:
```yaml
api:
  healthcheck:
    # Use /ready endpoint for K8s readiness probe
    test: ["CMD", "curl", "-f", "http://localhost:8000/health/ready"]
    interval: 10s
    timeout: 5s
    retries: 3
    start_period: 60s
```

---

### 2.4 Graceful Shutdown Handling

**Add to FastAPI application**:

```python
# ollama/main.py
import asyncio
import signal
from contextlib import asynccontextmanager

class AppLifecycle:
    """Manage application startup and shutdown."""
    
    def __init__(self):
        self.shutdown_tasks = []
    
    async def register_shutdown(self, coro):
        """Register an async function to run on shutdown."""
        self.shutdown_tasks.append(coro)
    
    async def shutdown(self):
        """Execute all shutdown tasks in reverse order."""
        print("Starting graceful shutdown...")
        
        # Cancel pending tasks
        pending = asyncio.all_tasks()
        for task in pending:
            task.cancel()
        
        # Wait for shutdown handlers
        for shutdown_task in reversed(self.shutdown_tasks):
            try:
                await shutdown_task()
            except Exception as e:
                print(f"Error during shutdown: {e}")
        
        print("Graceful shutdown complete")

lifecycle = AppLifecycle()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle startup and shutdown events."""
    
    # STARTUP
    print("Starting Ollama API...")
    db = await get_db()
    redis = await get_redis()
    
    async def shutdown_db():
        await db.close()
    
    async def shutdown_redis():
        await redis.close()
    
    lifecycle.register_shutdown(shutdown_db)
    lifecycle.register_shutdown(shutdown_redis)
    
    yield  # App is running
    
    # SHUTDOWN
    await lifecycle.shutdown()

app = FastAPI(
    title="Ollama API",
    lifespan=lifespan,
)

# Handle SIGTERM gracefully
async def handle_sigterm():
    print("SIGTERM received, initiating shutdown...")
    await lifecycle.shutdown()

def setup_signal_handlers():
    loop = asyncio.get_event_loop()
    loop.add_signal_handler(signal.SIGTERM, lambda: asyncio.create_task(handle_sigterm()))
```

---

## 3. COST OPTIMIZATION

### 3.1 Resource Allocation Strategy

**Current Issue**: No resource limits leads to container sprawl and cost overruns.

**Recommendation**: Implement tiered resource allocation:

```yaml
# docker-compose.yml - Cost-optimized resources
services:
  postgres:
    deploy:
      resources:
        limits:
          cpus: '1'       # Single core sufficient for queries
          memory: 2G      # 2GB for connection pool + working set
        reservations:
          cpus: '0.5'
          memory: 1G
          
  redis:
    deploy:
      resources:
        limits:
          cpus: '0.5'     # Redis is single-threaded
          memory: 1G      # Depends on dataset size
        reservations:
          cpus: '0.25'
          memory: 512M
          
  api:
    deploy:
      resources:
        limits:
          cpus: '1.5'     # 4 workers @ 0.375 CPU each
          memory: 1.5G    # Python runtime + buffer
        reservations:
          cpus: '1'
          memory: 1G
          
  qdrant:
    deploy:
      resources:
        limits:
          cpus: '2'       # Vector ops need CPU
          memory: 4G      # Index in memory
        reservations:
          cpus: '1'
          memory: 2G
```

### 3.2 Multi-Stage Optimization

Current Dockerfile:
```dockerfile
# Base stage: 500MB
FROM python:3.11-slim as base

# Builder stage: 2.5GB (all build tools)
FROM base as builder

# Production: 800MB (copies venv from builder)
FROM python:3.11-slim as production
```

**Optimization**: Reduce final image from 800MB to 200MB using distroless:

```dockerfile
# ============================================================================
# OPTIMIZED MULTI-STAGE DOCKERFILE
# Final image size: ~200MB vs 800MB (75% reduction)
# ============================================================================

FROM python:3.11-slim as builder

WORKDIR /build

# Only build dependencies needed
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml poetry.lock ./

# Install with poetry
RUN pip install poetry && \
    poetry config virtualenvs.create false && \
    poetry install --no-dev --no-interaction --no-ansi

# ============================================================================
# FINAL: Distroless minimal image
# ============================================================================
FROM python:3.11-slim

# Install ONLY runtime dependencies (no build tools)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Create non-root user
RUN useradd -m -u 1000 -s /bin/bash ollama

WORKDIR /app

# Copy only the virtual environment binaries
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application code
COPY --chown=ollama:ollama . .

USER ollama

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8000/health/ready || exit 1

# Production-grade settings
CMD ["gunicorn", \
     "ollama.main:app", \
     "--workers", "4", \
     "--worker-class", "uvicorn.workers.UvicornWorker", \
     "--bind", "0.0.0.0:8000", \
     "--timeout", "300", \
     "--max-requests", "1000", \
     "--access-logfile", "-", \
     "--error-logfile", "-"]
```

**Measure improvement**:
```bash
# Build both versions and compare
docker build -f Dockerfile.old -t ollama:old .
docker build -f Dockerfile.new -t ollama:new .

docker images | grep ollama
# ollama:old   <none>  500 MB
# ollama:new   <none>  200 MB  (60% reduction)
```

### 3.3 Model Caching Strategy

**Current Issue**: Ollama models loaded on every request if not cached.

**Implementation**:

```python
# ollama/services/model_cache.py
from typing import Optional
from functools import lru_cache
from ollama import Client
import logging

logger = logging.getLogger(__name__)

class ModelCache:
    """Cache loaded models to avoid reload overhead."""
    
    def __init__(self, max_models: int = 5):
        self.client = Client(host="http://ollama:11434")
        self.max_models = max_models
        self._loaded_models: dict[str, float] = {}  # model_name -> last_used_time
    
    async def get_model(self, model_name: str):
        """Get or load model."""
        current_time = time.time()
        
        # Check if model already loaded
        if model_name in self._loaded_models:
            self._loaded_models[model_name] = current_time  # Update access time
            logger.info(f"Cache hit for model: {model_name}")
            return self.client
        
        # Evict least-recently-used if at capacity
        if len(self._loaded_models) >= self.max_models:
            lru_model = min(
                self._loaded_models.items(),
                key=lambda x: x[1]
            )[0]
            logger.info(f"Evicting LRU model: {lru_model}")
            del self._loaded_models[lru_model]
        
        # Load new model
        logger.info(f"Loading model: {model_name}")
        # Ollama client auto-loads on first use
        self._loaded_models[model_name] = current_time
        return self.client

# Usage:
cache = ModelCache(max_models=3)
client = await cache.get_model("llama3.2")
```

---

## 4. IMMUTABLE INFRASTRUCTURE

### 4.1 Image Versioning Strategy

**Current State**: `image: ollama/ollama:latest` (not reproducible)

**Recommended Strategy**:

```yaml
# Version hierarchy:
# 1. SemVer for application: v1.2.3
# 2. Digest for reproducibility: sha256:abc123...
# 3. Build metadata: build.20260113.001

# docker-compose.prod.yml
version: '3.8'

services:
  api:
    image: ollama-api:v1.0.0@sha256:a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0u1v2w3x4y5z6
    # Digest updates only with explicit version bump
    
  postgres:
    image: postgres:15-alpine@sha256:f1f2f3f4f5f6f7f8f9f0e1e2e3e4e5e6e7e8e9e0d1d2d3d4d5d6
    # Alpine patch pinned, digest pinned for security updates
    
  redis:
    image: redis:7-alpine@sha256:e1e2e3e4e5e6e7e8e9e0d1d2d3d4d5d6d7d8d9d0c1c2c3c4c5c6
```

### 4.2 Infrastructure-as-Code with Terraform

**Create production deployment definition**:

```hcl
# terraform/main.tf - GCP Cloud Run deployment
terraform {
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }
}

provider "google" {
  project = var.gcp_project_id
  region  = var.gcp_region
}

# Cloud Run service
resource "google_cloud_run_service" "ollama_api" {
  name     = "ollama-api"
  location = var.gcp_region

  template {
    spec {
      service_account_name = google_service_account.ollama.email

      containers {
        image = "gcr.io/${var.gcp_project_id}/ollama-api:${var.image_tag}"

        ports {
          container_port = 8000
        }

        env {
          name = "ENVIRONMENT"
          value = "production"
        }

        env {
          name  = "DATABASE_URL"
          value_from {
            secret_key_ref {
              name = google_secret_manager_secret.db_url.id
              version = "latest"
            }
          }
        }

        resources {
          limits = {
            cpu    = "2"
            memory = "2Gi"
          }
        }
      }

      timeout_seconds = 300
    }

    metadata {
      labels = {
        app    = "ollama"
        env    = "production"
        version = var.image_tag
      }
    }
  }

  traffic {
    percent         = 100
    latest_revision = true
  }
}

# Cloud SQL PostgreSQL
resource "google_sql_database_instance" "ollama_db" {
  name             = "ollama-db"
  database_version = "POSTGRES_15"
  region           = var.gcp_region
  deletion_protection = true  # Prevent accidental deletion

  settings {
    tier = "db-custom-2-8192"  # 2 CPU, 8GB RAM
    availability_type = "REGIONAL"  # High availability

    backup_configuration {
      enabled                        = true
      point_in_time_recovery_enabled = true
      transaction_log_retention_days = 7
    }

    ip_configuration {
      require_ssl = true
    }
  }
}

# Redis (Cloud Memorystore)
resource "google_redis_instance" "ollama_cache" {
  name           = "ollama-cache"
  tier           = "standard"
  size_gb        = 5
  region         = var.gcp_region
  redis_version  = "7.0"
  auth_enabled   = true  # Require password
  transit_encryption_mode = "SERVER_AUTHENTICATION"

  labels = {
    app = "ollama"
  }
}

# Load Balancer with Cloud Armor
resource "google_compute_backend_service" "ollama" {
  name            = "ollama-backend"
  protocol        = "HTTP2"
  timeout_sec     = 30
  enable_cdn      = true

  backend {
    group           = google_compute_network_endpoint_group.ollama.id
    balancing_mode  = "RATE"
    max_rate_per_endpoint = 100
  }

  log_config {
    enable      = true
    sample_rate = 1.0
  }
}

# Cloud Armor security policy
resource "google_compute_security_policy" "ollama_policy" {
  name = "ollama-policy"

  # Default rule: allow
  rules {
    action   = "allow"
    priority = "2147483647"
    match {
      versioned_expr = "EXPR_V1"
      expr {
        expression = ""
      }
    }
  }

  # Rate limiting: 100 requests/minute per IP
  rules {
    action   = "rate_based_ban"
    priority = "1000"
    match {
      versioned_expr = "EXPR_V1"
      expr {
        expression = "true"
      }
    }
    rate_limit_options {
      conform_action = "allow"
      exceed_action = "deny(429)"

      rate_limit_threshold {
        count        = 100
        interval_sec = 60
      }

      ban_duration_sec = 600
    }
  }

  # Block common attacks
  rules {
    action   = "deny(403)"
    priority = "500"
    match {
      expr {
        expression = "evaluatePreconfiguredExpr('xss-v33')"
      }
    }
    preview = true
  }
}
```

---

### 4.3 Kubernetes Deployment with GitOps

**Enhanced K8s manifests with versioning**:

```yaml
# k8s/2-api.yaml - Production deployment
apiVersion: apps/v1
kind: Deployment
metadata:
  name: ollama-api
  namespace: ollama
  labels:
    app: ollama-api
    version: v1.0.0
  annotations:
    deployment.kubernetes.io/revision: "1"
spec:
  replicas: 3
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1
      maxUnavailable: 0
  selector:
    matchLabels:
      app: ollama-api
  template:
    metadata:
      labels:
        app: ollama-api
        version: v1.0.0
      annotations:
        prometheus.io/scrape: "true"
        prometheus.io/port: "8000"
        prometheus.io/path: "/metrics"
    spec:
      serviceAccountName: ollama-api
      securityContext:
        runAsNonRoot: true
        runAsUser: 1000
        fsGroup: 1000
      
      containers:
      - name: ollama-api
        image: gcr.io/elevated-iq/ollama-api:v1.0.0@sha256:a1b2c3d4e5f6
        imagePullPolicy: IfNotPresent
        securityContext:
          allowPrivilegeEscalation: false
          capabilities:
            drop:
              - ALL
          readOnlyRootFilesystem: true
        
        ports:
        - containerPort: 8000
          name: http
          protocol: TCP
        
        env:
        - name: ENVIRONMENT
          value: "production"
        - name: DEBUG
          value: "false"
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: ollama-secrets
              key: DATABASE_URL
        
        resources:
          limits:
            cpu: "1"
            memory: "1Gi"
          requests:
            cpu: "500m"
            memory: "512Mi"
        
        livenessProbe:
          httpGet:
            path: /health/live
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
          timeoutSeconds: 5
          failureThreshold: 3
        
        readinessProbe:
          httpGet:
            path: /health/ready
            port: 8000
          initialDelaySeconds: 10
          periodSeconds: 5
          timeoutSeconds: 3
          failureThreshold: 2
        
        volumeMounts:
        - name: cache
          mountPath: /app/cache
        - name: tmp
          mountPath: /tmp
      
      volumes:
      - name: cache
        emptyDir:
          sizeLimit: 1Gi
      - name: tmp
        emptyDir:
          sizeLimit: 500Mi

---
apiVersion: v1
kind: Service
metadata:
  name: ollama-api
  namespace: ollama
  labels:
    app: ollama-api
spec:
  type: ClusterIP
  ports:
  - port: 8000
    targetPort: 8000
    protocol: TCP
    name: http
  selector:
    app: ollama-api
```

---

### 4.4 CI/CD Pipeline for Immutable Deployments

```yaml
# .github/workflows/deploy.yml
name: Build & Deploy

on:
  push:
    tags:
      - 'v*.*.*'  # Only deploy on version tags

env:
  REGISTRY: gcr.io
  IMAGE_NAME: elevated-iq/ollama-api

jobs:
  build:
    runs-on: ubuntu-latest
    outputs:
      digest: ${{ steps.image.outputs.digest }}
    steps:
      - uses: actions/checkout@v4
      
      # 1. Extract version from tag
      - name: Get version
        id: version
        run: echo "VERSION=${GITHUB_REF#refs/tags/}" >> $GITHUB_OUTPUT
      
      # 2. Build image with BuildKit (for digest)
      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3
      
      # 3. Build and push to registry
      - name: Build and push
        uses: docker/build-push-action@v5
        id: image
        with:
          context: .
          push: true
          tags: |
            ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}:${{ steps.version.outputs.VERSION }}
            ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}:latest
          cache-from: type=gha
          cache-to: type=gha,mode=max
      
      # 4. Generate SBOM
      - name: Generate SBOM
        run: |
          docker run --rm -v /var/run/docker.sock:/var/run/docker.sock \
            anchore/syft:latest \
            "${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}:${{ steps.version.outputs.VERSION }}" \
            -o spdx-json > sbom.spdx.json
      
      # 5. Scan with Trivy
      - name: Scan image
        uses: aquasecurity/trivy-action@master
        with:
          image-ref: ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}:${{ steps.version.outputs.VERSION }}
          format: 'sarif'
          output: 'trivy-results.sarif'
          severity: 'CRITICAL,HIGH'
      
      - name: Upload Trivy scan
        uses: github/codeql-action/upload-sarif@v2
        with:
          sarif_file: 'trivy-results.sarif'

  deploy:
    needs: build
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      # 1. Authenticate to GCP
      - name: Authenticate to Google Cloud
        uses: google-github-actions/auth@v1
        with:
          credentials_json: ${{ secrets.GCP_SA_KEY }}
      
      # 2. Update K8s manifests with pinned image
      - name: Update deployment
        env:
          NEW_IMAGE: ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}@${{ needs.build.outputs.digest }}
        run: |
          kustomize edit set image \
            ollama-api=${{ env.NEW_IMAGE }} \
            --kustomization k8s/
          
          cat k8s/kustomization.yaml
      
      # 3. Apply with kubectl
      - name: Deploy to K8s
        run: |
          gcloud container clusters get-credentials ollama-prod --region us-central1
          kustomize build k8s/ | kubectl apply -f -
      
      # 4. Verify rollout
      - name: Wait for rollout
        run: |
          kubectl rollout status deployment/ollama-api -n ollama --timeout=5m
      
      # 5. Run smoke tests
      - name: Smoke tests
        run: |
          kubectl run -it --rm ollama-smoke-test \
            --image=curlimages/curl:latest \
            --restart=Never \
            -- curl -f http://ollama-api.ollama.svc.cluster.local:8000/health
```

---

## 5. IMPLEMENTATION ROADMAP

### Phase 1: Security (Week 1-2) - CRITICAL
- [ ] Rotate all hardcoded credentials
- [ ] Implement `.env` pattern with validation
- [ ] Add secrets scanning to CI/CD
- [ ] Generate pinned image digests
- [ ] Create security scanning workflow

**Priority**: HIGHEST - Address before any production deployment

### Phase 2: Robustness (Week 2-3) - HIGH
- [ ] Add restart policies to all services
- [ ] Implement resource limits
- [ ] Enhance health check endpoints
- [ ] Add graceful shutdown handling
- [ ] Document failure recovery procedures

### Phase 3: Cost Optimization (Week 4) - MEDIUM
- [ ] Optimize Dockerfile for smaller images
- [ ] Implement model caching strategy
- [ ] Right-size resource allocations
- [ ] Set up monitoring for cost anomalies

### Phase 4: Immutable Infrastructure (Week 5-6) - ONGOING
- [ ] Create Terraform IaC for GCP deployment
- [ ] Migrate K8s to GitOps with ArgoCD
- [ ] Implement image versioning automation
- [ ] Set up automated deployment pipeline
- [ ] Document infrastructure versioning strategy

---

## 6. SUCCESS METRICS

### Security
- ✅ Zero hardcoded secrets in repos
- ✅ All images pinned to digests
- ✅ CI/CD scanning blocks vulnerable images
- ✅ TLS enforced for all inter-service communication

### Robustness
- ✅ 99.9% uptime during normal operations
- ✅ Automatic recovery from single-service failures
- ✅ Graceful shutdown < 30 seconds
- ✅ Health checks sensitive to degradation

### Cost
- ✅ Image size < 250MB (from 800MB)
- ✅ CPU utilization 40-60% (not overprovisioned)
- ✅ Memory utilization 50-70% (healthy level)
- ✅ Deployment cost 30% reduction YoY

### Immutable Infrastructure
- ✅ 100% reproducible deployments
- ✅ All infrastructure defined-as-code
- ✅ One-command rollback to any previous version
- ✅ Zero manual configuration drift

---

## Appendix: Quick Implementation Checklist

```bash
# 1. Secrets Management
[ ] Create .env.example
[ ] Generate secure values (openssl rand -hex 32)
[ ] Update docker-compose.yml to use ${VAR}
[ ] Add to .gitignore: .env

# 2. Image Pinning
[ ] Run scripts/pin-image-versions.sh
[ ] Update all docker-compose files with @sha256:...
[ ] Update K8s manifests with image digests
[ ] Test deployments reproducibly

# 3. Security Scanning
[ ] Add gitleaks to CI/CD
[ ] Add Trivy container scanning
[ ] Add pip-audit to checks
[ ] Configure SBOM generation

# 4. Health Checks
[ ] Implement /health, /ready, /live endpoints
[ ] Update docker-compose healthchecks
[ ] Update K8s probes
[ ] Add monitoring for health check failures

# 5. Resource Limits
[ ] Set CPU limits on all services
[ ] Set memory limits on all services
[ ] Test under load to validate sizing
[ ] Add to monitoring dashboard

# 6. Kubernetes Deployment
[ ] Create Terraform code for GCP
[ ] Update K8s manifests with digests
[ ] Set up ArgoCD for GitOps
[ ] Create deployment automation

```

---

**Status**: Ready for implementation  
**Questions?** Refer to specific sections for code examples and implementation patterns.

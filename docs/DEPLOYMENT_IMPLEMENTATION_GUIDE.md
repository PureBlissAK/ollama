# Deployment Enhancement Implementation Guide

**Start Date**: January 13, 2026  
**Target Duration**: 6 weeks  
**Owner**: Engineering Team  
**Status**: In Planning  

---

## Quick Start (First 24 Hours)

### 1. Generate Secure Secrets

```bash
#!/bin/bash
# scripts/setup-env-production.sh

# Generate 32-char passwords
POSTGRES_PASSWORD=$(openssl rand -hex 16)
REDIS_PASSWORD=$(openssl rand -hex 16)

# Generate 64-char secret keys
SECRET_KEY=$(openssl rand -hex 32)

# Create .env file (NEVER commit)
cat > .env.production << EOF
# PostgreSQL
POSTGRES_USER=ollama
POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
POSTGRES_DB=ollama

# Database Connection
DATABASE_URL=postgresql+asyncpg://ollama:${POSTGRES_PASSWORD}@postgres:5432/ollama

# Redis
REDIS_PASSWORD=${REDIS_PASSWORD}
REDIS_URL=redis://:${REDIS_PASSWORD}@redis:6379/0

# Application Security
SECRET_KEY=${SECRET_KEY}
JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=24
API_KEY_PREFIX=sk

# Environment
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=INFO

# Qdrant (if using API key auth)
QDRANT_API_KEY=$(openssl rand -hex 16)

# Grafana
GRAFANA_ADMIN_PASSWORD=$(openssl rand -base64 32)

# Monitoring
JAEGER_AGENT_HOST=jaeger
JAEGER_AGENT_PORT=6831
EOF

echo "✓ .env.production created with secure values"
echo "✓ NEVER commit this file"
echo "✓ Store secrets in secure vault (e.g., AWS Secrets Manager, Vault)"
```

### 2. Pin Image Versions

```bash
#!/bin/bash
# scripts/generate-pinned-versions.sh

# Fetch current digests for all services
declare -A IMAGES=(
    ["postgres:15-alpine"]="postgres"
    ["redis:7-alpine"]="redis"
    ["qdrant/qdrant:v1.7.0"]="qdrant"
    ["ollama/ollama:0.1.32"]="ollama"
    ["prom/prometheus:v2.50.0"]="prometheus"
    ["grafana/grafana:10.2.2"]="grafana"
    ["jaegertracing/all-in-one:v1.51.0"]="jaeger"
)

echo "Pinned Image Versions:"
echo "====================="

for image in "${!IMAGES[@]}"; do
    echo "Pulling $image..."
    docker pull "$image" > /dev/null 2>&1
    
    digest=$(docker inspect --format='{{index .RepoDigests 0}}' "$image" | cut -d'@' -f2)
    echo "${IMAGES[$image]}: $image@$digest"
done
```

### 3. Update docker-compose.yml

```yaml
# docker-compose.yml - Security hardened version
version: '3.8'

services:
  postgres:
    image: postgres:15-alpine@sha256:f1f2f3f4f5f6f7f8f9f0  # PINNED
    container_name: ollama-postgres
    restart: unless-stopped
    environment:
      POSTGRES_USER: ${POSTGRES_USER:-ollama}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}  # Required
      POSTGRES_DB: ${POSTGRES_DB:-ollama}
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ollama"]
      interval: 10s
      timeout: 5s
      retries: 5
      start_period: 40s
    deploy:
      resources:
        limits:
          cpus: '1'
          memory: 2G
        reservations:
          cpus: '0.5'
          memory: 1G

  redis:
    image: redis:7-alpine@sha256:e1e2e3e4e5e6e7e8e9e0  # PINNED
    container_name: ollama-redis
    restart: unless-stopped
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    command: redis-server --appendonly yes --requirepass ${REDIS_PASSWORD}
    healthcheck:
      test: ["CMD", "redis-cli", "-a", "${REDIS_PASSWORD}", "ping"]
      interval: 10s
      timeout: 3s
      retries: 5
      start_period: 10s
    deploy:
      resources:
        limits:
          cpus: '0.5'
          memory: 1G
        reservations:
          cpus: '0.25'
          memory: 512M

  qdrant:
    image: qdrant/qdrant:v1.7.0@sha256:d1d2d3d4d5d6d7d8d9d0  # PINNED
    container_name: ollama-qdrant
    restart: unless-stopped
    ports:
      - "6333:6333"
      - "6334:6334"
    volumes:
      - qdrant_data:/qdrant/storage
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:6333/health"]
      interval: 10s
      timeout: 5s
      retries: 5
      start_period: 30s
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 4G
        reservations:
          cpus: '1'
          memory: 2G

  ollama:
    image: ollama/ollama:0.1.32@sha256:c1c2c3c4c5c6c7c8c9c0  # PINNED
    container_name: ollama-engine
    restart: unless-stopped
    ports:
      - "11434:11434"
    volumes:
      - ollama_data:/root/.ollama
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:11434/api/version"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 60s
    deploy:
      resources:
        limits:
          cpus: '4'
          memory: 16G
        reservations:
          cpus: '2'
          memory: 8G

  api:
    build:
      context: .
      dockerfile: Dockerfile
      args:
        BUILD_DATE: ${BUILD_DATE:-2026-01-13}
        VCS_REF: ${GIT_COMMIT:-unknown}
    image: ollama-api:latest
    container_name: ollama-api
    restart: on-failure:5
    environment:
      # Database
      DATABASE_URL: ${DATABASE_URL}
      
      # Cache
      REDIS_URL: ${REDIS_URL}
      
      # Vector Database
      QDRANT_URL: http://qdrant:6333
      QDRANT_API_KEY: ${QDRANT_API_KEY:-}
      
      # LLM Engine
      OLLAMA_URL: http://ollama:11434
      
      # Security - NO HARDCODED VALUES
      SECRET_KEY: ${SECRET_KEY}
      JWT_ALGORITHM: ${JWT_ALGORITHM:-HS256}
      ACCESS_TOKEN_EXPIRE_MINUTES: 30
      
      # Environment
      ENVIRONMENT: ${ENVIRONMENT:-development}
      DEBUG: ${DEBUG:-false}  # Never true in production
      LOG_LEVEL: ${LOG_LEVEL:-INFO}
      
      # Monitoring
      JAEGER_AGENT_HOST: ${JAEGER_AGENT_HOST:-jaeger}
      JAEGER_AGENT_PORT: ${JAEGER_AGENT_PORT:-6831}
    ports:
      - "8000:8000"
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
      qdrant:
        condition: service_healthy
      ollama:
        condition: service_healthy
    volumes:
      - ./ollama:/app/ollama:ro
      - ./tests:/app/tests:ro
    command: uvicorn ollama.main:app --host 0.0.0.0 --port 8000 --reload
    healthcheck:
      test: ["CMD", "curl", "-f", "--fail", "http://localhost:8000/health/ready"]
      interval: 10s
      timeout: 5s
      retries: 3
      start_period: 60s
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 2G
        reservations:
          cpus: '1'
          memory: 1G

  prometheus:
    image: prom/prometheus:v2.50.0@sha256:a1a2a3a4a5a6a7a8a9a0  # PINNED
    container_name: ollama-prometheus
    restart: unless-stopped
    ports:
      - "9090:9090"
    volumes:
      - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml:ro
      - prometheus_data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
    deploy:
      resources:
        limits:
          cpus: '1'
          memory: 1G
        reservations:
          cpus: '0.5'
          memory: 512M

  grafana:
    image: grafana/grafana:10.2.2@sha256:b1b2b3b4b5b6b7b8b9b0  # PINNED
    container_name: ollama-grafana
    restart: unless-stopped
    ports:
      - "3000:3000"
    environment:
      GF_SECURITY_ADMIN_USER: admin
      GF_SECURITY_ADMIN_PASSWORD: ${GRAFANA_ADMIN_PASSWORD}  # From .env
      GF_PATHS_PROVISIONING: /etc/grafana/provisioning
      GF_SECURITY_ADMIN_JWT_SECRET: ${SECRET_KEY}
    volumes:
      - ./monitoring/grafana/dashboards:/etc/grafana/provisioning/dashboards:ro
      - ./monitoring/grafana/datasources:/etc/grafana/provisioning/datasources:ro
      - grafana_data:/var/lib/grafana
    depends_on:
      - prometheus
    deploy:
      resources:
        limits:
          cpus: '0.5'
          memory: 512M
        reservations:
          cpus: '0.25'
          memory: 256M

  jaeger:
    image: jaegertracing/all-in-one:v1.51.0@sha256:j1j2j3j4j5j6j7j8j9j0  # PINNED
    container_name: ollama-jaeger
    restart: unless-stopped
    ports:
      - "5775:5775/udp"
      - "6831:6831/udp"
      - "6832:6832/udp"
      - "5778:5778"
      - "16686:16686"
      - "14268:14268"
      - "14250:14250"
      - "9411:9411"
    environment:
      COLLECTOR_ZIPKIN_HOST_PORT: ":9411"
    deploy:
      resources:
        limits:
          cpus: '1'
          memory: 1G
        reservations:
          cpus: '0.5'
          memory: 512M

volumes:
  postgres_data:
  redis_data:
  qdrant_data:
  ollama_data:
  prometheus_data:
  grafana_data:
```

---

## Phase 1: Security Implementation (Week 1-2)

### Checklist

- [ ] 1.1: Create .env.example template
- [ ] 1.2: Generate production secrets
- [ ] 1.3: Update docker-compose.yml to use ${VARS}
- [ ] 1.4: Pin all image digests
- [ ] 1.5: Add .env to .gitignore
- [ ] 1.6: Implement SecretsConfig validation
- [ ] 1.7: Add security scanning to CI/CD
- [ ] 1.8: Rotate all hardcoded credentials

### Testing Commands

```bash
# Verify no hardcoded secrets in compose files
grep -r "password.*=" docker-compose.yml | grep -v "\${" || echo "✓ No hardcoded passwords"
grep -r "SECRET_KEY.*=" docker-compose.yml | grep -v "\${" || echo "✓ No hardcoded secrets"

# Test docker-compose with .env file
docker-compose config | grep -E "(PASSWORD|SECRET)" || echo "✓ Variables properly substituted"

# Verify image digests
docker-compose config | grep "@sha256:" || echo "! Check image pinning"
```

---

## Phase 2: Robustness Implementation (Week 2-3)

### Update Health Check Endpoints

```python
# ollama/api/routes/health.py - FULL IMPLEMENTATION

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from redis.asyncio import Redis
from datetime import datetime
from typing import Dict, Any
from sqlalchemy import text
from ollama.config.database import get_db
from ollama.config.redis import get_redis

router = APIRouter(prefix="/health", tags=["health"])

@router.get("", response_model=Dict[str, Any])
@router.get("/", response_model=Dict[str, Any])
async def health_check(
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis)
) -> Dict[str, Any]:
    """
    Comprehensive health check - used by load balancers.
    Returns 200 OK if all critical dependencies operational.
    """
    db_status = await check_database(db)
    redis_status = await check_redis(redis)
    
    # Determine overall status
    all_statuses = [db_status["status"], redis_status["status"]]
    if "unhealthy" in all_statuses:
        overall = "unhealthy"
        http_code = 503
    elif "degraded" in all_statuses:
        overall = "degraded"
        http_code = 200  # Still accepts traffic but monitoring alerts
    else:
        overall = "healthy"
        http_code = 200
    
    response = {
        "status": overall,
        "timestamp": datetime.utcnow().isoformat(),
        "checks": {
            "database": db_status,
            "cache": redis_status,
        },
        "version": "1.0.0"
    }
    
    return JSONResponse(status_code=http_code, content=response)

@router.get("/ready")
async def readiness_check(
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    Readiness probe - is service ready to accept new traffic?
    Stricter than liveness - fails if database unavailable.
    Used by K8s readiness probe and load balancer.
    """
    try:
        async with db.begin():
            await db.execute(text("SELECT 1"))
        
        return JSONResponse(
            status_code=200,
            content={"ready": True}
        )
    except Exception as e:
        return JSONResponse(
            status_code=503,
            content={
                "ready": False,
                "error": str(e)
            }
        )

@router.get("/live")
async def liveness_check() -> Dict[str, Any]:
    """
    Liveness probe - is process still running?
    Minimal check - should rarely fail unless process is hung.
    Used by K8s liveness probe.
    """
    return JSONResponse(
        status_code=200,
        content={"alive": True}
    )

async def check_database(db: AsyncSession) -> Dict[str, Any]:
    """Check database connectivity and latency."""
    try:
        start = datetime.utcnow()
        async with db.begin():
            await db.execute(text("SELECT 1"))
        latency_ms = (datetime.utcnow() - start).total_seconds() * 1000
        
        return {
            "status": "healthy" if latency_ms < 100 else "degraded",
            "latency_ms": round(latency_ms, 2),
            "message": "Database responsive"
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "message": "Database unreachable"
        }

async def check_redis(redis: Redis) -> Dict[str, Any]:
    """Check Redis connectivity and latency."""
    try:
        start = datetime.utcnow()
        await redis.ping()
        latency_ms = (datetime.utcnow() - start).total_seconds() * 1000
        
        return {
            "status": "healthy" if latency_ms < 50 else "degraded",
            "latency_ms": round(latency_ms, 2),
            "message": "Redis responsive"
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "message": "Redis unreachable"
        }
```

### Add to Main Application

```python
# ollama/main.py

from fastapi import FastAPI
from contextlib import asynccontextmanager
from ollama.api.routes import health, generate, chat, models
import signal
import asyncio
import logging

logger = logging.getLogger(__name__)

class AppState:
    """Manage application lifecycle."""
    shutdown_event = asyncio.Event()
    
    @classmethod
    async def trigger_shutdown(cls):
        cls.shutdown_event.set()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle startup and shutdown."""
    
    # STARTUP
    logger.info("🚀 Starting Ollama API...")
    
    # Setup signal handlers
    loop = asyncio.get_event_loop()
    
    def handle_sigterm():
        logger.info("SIGTERM received, initiating graceful shutdown...")
        asyncio.create_task(AppState.trigger_shutdown())
    
    loop.add_signal_handler(signal.SIGTERM, handle_sigterm)
    
    yield  # App is now running
    
    # SHUTDOWN (triggered by SIGTERM or context manager exit)
    logger.info("🛑 Shutting down gracefully...")
    
    # Cancel pending tasks
    pending = asyncio.all_tasks()
    for task in pending:
        if task != asyncio.current_task():
            task.cancel()
    
    # Give tasks 30 seconds to complete
    await asyncio.sleep(30)
    
    logger.info("✓ Graceful shutdown complete")

# Create application
app = FastAPI(
    title="Ollama API",
    description="Elite AI Inference Platform",
    version="1.0.0",
    lifespan=lifespan,
)

# Include routers
app.include_router(health.router)
app.include_router(generate.router)
app.include_router(chat.router)
app.include_router(models.router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "ollama.main:app",
        host="0.0.0.0",
        port=8000,
        reload=False,
        workers=4,
        access_log=True
    )
```

---

## Phase 3 & 4: Advanced Setup

See main `DEPLOYMENT_ENHANCEMENT_ANALYSIS.md` for:
- Terraform infrastructure-as-code (GCP Cloud Run, Cloud SQL, Cloud Armor)
- Kubernetes manifests with GitOps
- CI/CD pipeline with automated scanning and deployment

---

## Verification Checklist

```bash
# After implementation
[ ] docker-compose config shows all variables substituted
[ ] No secrets in git: git log -p | grep -i password
[ ] Health endpoints respond: curl http://localhost:8000/health
[ ] All images pinned with digests
[ ] Resource limits enforced: docker stats
[ ] Graceful shutdown works: docker-compose down (< 30s)
[ ] Tests pass: pytest tests/ -v
[ ] Linting passes: ruff check ollama/
[ ] Type checking passes: mypy ollama/ --strict
[ ] Security audit clean: pip-audit
```

---

## Support & References

- **Security**: See `DEPLOYMENT_ENHANCEMENT_ANALYSIS.md` Section 1
- **Robustness**: See `DEPLOYMENT_ENHANCEMENT_ANALYSIS.md` Section 2
- **Cost**: See `DEPLOYMENT_ENHANCEMENT_ANALYSIS.md` Section 3
- **Infrastructure**: See `DEPLOYMENT_ENHANCEMENT_ANALYSIS.md` Section 4

---

**Status**: Ready for phased implementation  
**Questions?** Review corresponding section in enhancement analysis.

# OLLAMA Local Development Setup

## Overview

This guide covers setting up the complete Ollama AI platform locally for development, including:

- **PostgreSQL** database (metadata, conversations, usage)
- **Redis** cache (sessions, rate limiting, caching)
- **Ollama** inference engine (LLM model serving)
- **Qdrant** vector database (embeddings, RAG)
- **FastAPI** application server
- **Prometheus** metrics collection (optional)
- **Grafana** dashboards (optional)

## Prerequisites

### System Requirements

- **RAM**: Minimum 16GB (32GB recommended)
  - 4GB for API/database/cache
  - 8GB+ for Ollama inference engine
- **Disk**: 50GB+ (for model storage)
- **CPU**: 4+ cores (8+ recommended)
- **GPU**: NVIDIA GPU with CUDA support (optional but recommended for inference)

### Software Requirements

- **Docker**: 24.0+ with Compose 2.20+
- **NVIDIA Docker**: `nvidia-docker` or `nvidia-container-runtime` (for GPU support)
- **Python**: 3.11+ (for running tests/scripts locally)
- **Git**: For version control

### Installation

#### macOS (Intel)

```bash
# Install Docker Desktop
brew install --cask docker

# For NVIDIA GPU support (if applicable)
# Note: NVIDIA GPUs not supported on macOS natively
# Use CPU-only: export OLLAMA_NUM_GPU=0
```

#### macOS (Apple Silicon - M1/M2/M3)

```bash
# Install Docker Desktop for Apple Silicon
brew install --cask docker

# Note: GPU acceleration works differently on Apple Silicon
# Ollama will auto-detect Metal GPU support
```

#### Ubuntu/Debian

```bash
# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Install Docker Compose
sudo apt-get install docker-compose-plugin

# Install NVIDIA Docker Runtime (for GPU support)
distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | sudo apt-key add -
curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.list | \
  sudo tee /etc/apt/sources.list.d/nvidia-docker.list

sudo apt-get update && sudo apt-get install -y nvidia-docker2
sudo systemctl restart docker
```

#### Windows (WSL2)

```bash
# Install Docker Desktop for Windows with WSL2 backend
# https://docs.docker.com/desktop/install/windows-install/

# Install NVIDIA CUDA Toolkit for WSL2 (for GPU support)
# https://docs.nvidia.com/cuda/wsl-user-guide/
```

## Quick Start (5 minutes)

### 1. Start All Services

```bash
cd /home/akushnir/ollama

# Start all services in background
docker-compose -f docker-compose.local.yml up -d

# Or with live logs (in separate terminal)
docker-compose -f docker-compose.local.yml up

# Watch services come online
docker-compose -f docker-compose.local.yml ps
```

### 2. Wait for Services to Be Ready

```bash
# Check service health
docker-compose -f docker-compose.local.yml ps

# All services should show "healthy" or "running"
# Takes ~30-60 seconds depending on your system
```

### 3. Verify Services Are Accessible

```bash
# API Health
curl http://127.0.0.1:8000/health

# Database
psql -h localhost -U ollama -d ollama -c "SELECT 1"

# Redis
redis-cli -h 127.0.0.1 ping

# Ollama
curl http://127.0.0.1:11434/api/tags

# Qdrant
curl http://127.0.0.1:6333/health

# Prometheus (optional)
curl http://127.0.0.1:9090/-/healthy

# Grafana (optional)
curl http://127.0.0.1:3000/api/health
```

### 4. Run Tests

```bash
# Install dependencies (first time only)
pip install -e ".[dev]"

# Run all tests with coverage
pytest tests/ -v --cov=ollama --cov-report=html

# Run specific test file
pytest tests/unit/test_auth.py -v

# Run with live output
pytest tests/ -v -s
```

### 5. Access the Application

```bash
# API Server
curl http://127.0.0.1:8000/api/v1/health

# Grafana Dashboards (optional)
# Open browser: http://127.0.0.1:3000
# Username: admin
# Password: admin

# Prometheus Metrics (optional)
# Open browser: http://127.0.0.1:9090
```

## Detailed Service Information

### PostgreSQL Database

- **Host**: `postgres` (Docker network) or `127.0.0.1` (local)
- **Port**: 5432
- **User**: ollama
- **Password**: ollama-dev-password
- **Database**: ollama
- **Connection String**: `postgresql://ollama:ollama-dev-password@postgres:5432/ollama`

**Access locally:**

```bash
psql -h 127.0.0.1 -U ollama -d ollama

# Or use pgAdmin (optional)
docker-compose -f docker-compose.local.yml up -d pgadmin
# Access: http://127.0.0.1:5050
```

### Redis Cache

- **Host**: `redis` (Docker network) or `127.0.0.1` (local)
- **Port**: 6379
- **Database**: 0
- **Password**: (none - development)

**Access locally:**

```bash
redis-cli -h 127.0.0.1

# Inside redis-cli
> PING
PONG
> KEYS *
> GET mykey
```

### Ollama Inference Engine

- **Host**: `ollama` (Docker network) or `127.0.0.1` (local)
- **Port**: 11434
- **Base URL**: `http://ollama:11434`

**Common Commands:**

```bash
# List available models
curl http://127.0.0.1:11434/api/tags

# Pull a model (downloads ~4-40GB depending on model)
docker exec ollama-engine-local ollama pull llama2
docker exec ollama-engine-local ollama pull mistral
docker exec ollama-engine-local ollama pull neural-chat

# Generate text
curl -X POST http://127.0.0.1:11434/api/generate \
  -H "Content-Type: application/json" \
  -d '{
    "model": "llama2",
    "prompt": "Why is the sky blue?",
    "stream": false
  }'
```

### Qdrant Vector Database

- **Host**: `qdrant` (Docker network) or `127.0.0.1` (local)
- **Port**: 6333 (REST), 6334 (gRPC)
- **API Key**: qdrant-dev-key (development)

**Access locally:**

```bash
# Web UI
# Open browser: http://127.0.0.1:6333/dashboard

# Health check
curl http://127.0.0.1:6333/health

# Create a collection
curl -X PUT http://127.0.0.1:6333/collections/my-vectors \
  -H "Content-Type: application/json" \
  -d '{
    "vectors": {
      "size": 1536,
      "distance": "Cosine"
    }
  }'
```

## Common Development Tasks

### Running the API in Development Mode (with auto-reload)

**Option 1: Using Docker (recommended)**

```bash
# API will auto-reload when code changes
docker-compose -f docker-compose.local.yml up api

# In another terminal, watch the logs
docker-compose -f docker-compose.local.yml logs -f api
```

**Option 2: Running Locally (requires dependencies)**

```bash
# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -e ".[dev]"

# Set environment variables
export $(cat .env.local | xargs)

# Run dev server with auto-reload
uvicorn ollama.main:app --reload --host 0.0.0.0 --port 8000
```

### Pulling Models into Ollama

```bash
# Pull a model (first time downloads from ollama.ai, then caches locally)
docker exec ollama-engine-local ollama pull llama2

# Available models at https://ollama.ai/library
# Popular options:
# - llama2 (7B default, 4GB)
# - mistral (7B, 4GB, faster)
# - neural-chat (7B, 4GB, conversational)
# - codellama (7B, code-optimized)
# - orca-mini (3B, lightweight)

# List downloaded models
docker exec ollama-engine-local ollama list
```

### Running Tests

```bash
# Run all tests
pytest tests/ -v

# Run specific test suite
pytest tests/unit/services/ -v

# Run with coverage report
pytest tests/ --cov=ollama --cov-report=html
# Open htmlcov/index.html in browser

# Run integration tests (requires all services running)
pytest tests/integration/ -v

# Run a single test
pytest tests/unit/test_auth.py::test_validate_api_key -v

# Run tests matching a pattern
pytest -k "test_generate" -v

# Run with live output (no capture)
pytest tests/ -v -s
```

### Database Migrations

```bash
# Create a new migration
alembic revision -m "Add users table"

# Apply migrations
alembic upgrade head

# Rollback to previous migration
alembic downgrade -1

# View migration history
alembic history

# Create tables from scratch
python -c "
from sqlalchemy import create_engine
from ollama.models import Base
import os

db_url = os.getenv('DATABASE_URL')
engine = create_engine(db_url)
Base.metadata.create_all(engine)
"
```

### Code Quality Checks

```bash
# Type checking
mypy ollama/ --strict

# Linting
ruff check ollama/

# Format code
black ollama/ tests/ --line-length=100

# Security audit
pip-audit

# All checks (parallel)
pytest tests/ && mypy ollama/ --strict && ruff check ollama/ && pip-audit
```

### Monitoring and Observability

```bash
# View Prometheus metrics
curl http://127.0.0.1:9090/api/v1/query?query=up

# View Grafana dashboards
# Open: http://127.0.0.1:3000

# View application logs
docker-compose -f docker-compose.local.yml logs -f api

# View database logs
docker-compose -f docker-compose.local.yml logs -f postgres

# View Ollama logs
docker-compose -f docker-compose.local.yml logs -f ollama
```

## Troubleshooting

### Services Won't Start

```bash
# Check Docker is running
docker ps

# Check logs for errors
docker-compose -f docker-compose.local.yml logs

# Check service-specific logs
docker-compose -f docker-compose.local.yml logs api
docker-compose -f docker-compose.local.yml logs postgres

# Rebuild images
docker-compose -f docker-compose.local.yml build --no-cache

# Remove containers and try again
docker-compose -f docker-compose.local.yml down -v
docker-compose -f docker-compose.local.yml up -d
```

### Out of Memory

```bash
# Reduce resource limits in docker-compose.local.yml
# Or stop unnecessary services:
docker-compose -f docker-compose.local.yml down prometheus grafana

# Check memory usage
docker stats
```

### Ollama Model Not Loading

```bash
# Check available disk space
df -h

# Check Ollama logs
docker-compose -f docker-compose.local.yml logs ollama

# Restart Ollama
docker-compose -f docker-compose.local.yml restart ollama

# Force pull model again
docker exec ollama-engine-local ollama pull llama2 --insecure
```

### Database Connection Refused

```bash
# Check if PostgreSQL is running
docker-compose -f docker-compose.local.yml ps postgres

# Check database logs
docker-compose -f docker-compose.local.yml logs postgres

# Restart PostgreSQL
docker-compose -f docker-compose.local.yml restart postgres

# Reset database (WARNING: deletes all data)
docker-compose -f docker-compose.local.yml down -v postgres
docker-compose -f docker-compose.local.yml up -d postgres
```

### Redis Connection Issues

```bash
# Test Redis connection
redis-cli -h 127.0.0.1 ping

# Check Redis logs
docker-compose -f docker-compose.local.yml logs redis

# Restart Redis
docker-compose -f docker-compose.local.yml restart redis

# Check used memory
redis-cli -h 127.0.0.1 INFO memory
```

## Cleanup

### Stop All Services

```bash
docker-compose -f docker-compose.local.yml down
```

### Remove All Data (WARNING: Destructive)

```bash
# Remove containers, networks, and volumes
docker-compose -f docker-compose.local.yml down -v

# This will DELETE all:
# - Databases
# - Cached models
# - Redis data
# - Vector database collections
```

### Reset to Fresh State

```bash
# Stop services
docker-compose -f docker-compose.local.yml down -v

# Remove images (to force rebuild)
docker-compose -f docker-compose.local.yml rm -f

# Start fresh
docker-compose -f docker-compose.local.yml up -d
```

## Performance Tuning

### For Inference

```bash
# Enable NVIDIA GPU support in docker-compose.local.yml
# Uncomment devices section in ollama service

# Or set environment variable
export OLLAMA_NUM_GPU=1

# Check GPU is being used
docker exec ollama-engine-local sh -c "nvidia-smi"
```

### For Database

```bash
# Increase connection pool size in .env.local
DATABASE_POOL_SIZE=50  # default: 20

# Increase shared_buffers in PostgreSQL (docker-compose.local.yml)
# Add to postgres environment:
# POSTGRES_INITDB_ARGS="-c shared_buffers=256MB -c effective_cache_size=1GB"
```

### For Redis

```bash
# Increase max memory in .env.local
# Add to redis command in docker-compose.local.yml:
# --maxmemory 4gb
```

## Next Steps

1. **Run Tests**: `pytest tests/ -v --cov=ollama`
2. **Check API**: `curl http://127.0.0.1:8000/health`
3. **Pull Models**: `docker exec ollama-engine-local ollama pull llama2`
4. **Generate Text**: Use the `/api/v1/generate` endpoint
5. **Monitor**: View Grafana dashboards at `http://127.0.0.1:3000`

## Documentation

- **API Docs**: http://127.0.0.1:8000/docs (SwaggerUI)
- **RedDoc**: http://127.0.0.1:8000/redoc
- **Architecture**: See `docs/architecture.md`
- **Contributing**: See `CONTRIBUTING.md`

## Support

For issues or questions:

1. Check `Troubleshooting` section above
2. Review Docker logs: `docker-compose logs -f`
3. Check GitHub Issues: https://github.com/kushin77/ollama/issues
4. Read Full Documentation: `docs/`

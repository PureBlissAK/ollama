# ⚡ OLLAMA DEVELOPER QUICK REFERENCE

**Version**: 2.1.0 | **Last Updated**: January 14, 2026
**Production Status**: ✅ Verified (Tier 2 Load Test: 50 users, 75ms P95, 100% success)

---

## 🚀 Get Started in 5 Minutes

### 1. Clone & Setup

```bash
git clone https://github.com/kushin77/ollama.git
cd ollama
python -m venv .venv && source .venv/bin/activate
pip install -e .
```

### 2. Start Local Services (Using Real IP, NOT localhost)

```bash
# IMPORTANT: Set real IP for development (never use localhost)
export REAL_IP=$(hostname -I | awk '{print $1}')
sed -i "s|PUBLIC_API_URL=.*|PUBLIC_API_URL=http://$REAL_IP:8000|" .env.dev

# Start services
docker-compose -f docker-compose.local.yml up -d postgres redis ollama
docker-compose logs -f  # Watch logs
```

### 3. Run Development Server

```bash
# Terminal 1: Start server with real IP (auto-reload)
export REAL_IP=$(hostname -I | awk '{print $1}')
uvicorn ollama.main:app --reload --host 0.0.0.0 --port 8000

# Terminal 2: Test endpoint via real IP (NOT localhost)
curl http://$REAL_IP:8000/health
```

### 4. Make Your First Request

```bash
# Use real IP or DNS in development
export REAL_IP=$(hostname -I | awk '{print $1}')

# List available models
curl http://$REAL_IP:8000/api/v1/models

# Generate text
curl -X POST http://$REAL_IP:8000/api/v1/generate \
  -H "Content-Type: application/json" \
  -d '{"model": "llama3.2", "prompt": "Hello world"}'

# Production: Use https://elevatediq.ai/ollama endpoint
curl -H "X-API-Key: your-api-key" \
  https://elevatediq.ai/ollama/api/v1/generate \
  -X POST \
  -H "Content-Type: application/json" \
  -d '{"model": "llama3.2", "prompt": "Hello"}'
```

---

## 📚 Common Commands

### Development

```bash
# Run all quality checks (required before commit)
pytest tests/ -v --cov=ollama
mypy ollama/ --strict
ruff check ollama/
pip-audit

# Or run individual checks
pytest tests/unit/                      # Unit tests only
mypy ollama/ --strict                   # Type checking only
ruff check ollama/ --fix                # Linting with fixes
black ollama/ tests/                    # Format code
pip-audit                               # Security audit

# Pre-commit hooks (automatic on git commit -S)
.githooks/setup.sh                      # Install hooks
git add .
git commit -S -m "feat: my feature"     # Requires GPG signature
```

### Production Endpoints

```bash
# Primary production endpoint (GCP Load Balancer)
curl -H "X-API-Key: your-api-key" \
  https://elevatediq.ai/ollama/api/v1/health

# Health check
curl https://elevatediq.ai/ollama/api/v1/health

# Direct service (internal only)
# ❌ NOT accessible from internet: ollama-service-sozvlwbwva-uc.a.run.app
```

### Git Workflow

```bash
# Create feature branch
git checkout -b feature/my-feature

# Work on feature
# ... make changes ...
git add .
git commit -S -m "feat(scope): description"  # -S for GPG signing

# Push frequently (minimum every 4 hours)
git push origin feature/my-feature

# Create pull request on GitHub
# Wait for CI/CD checks to pass
# Address review feedback
# Merge when approved
```

### Database

```bash
# Create migration
alembic revision --autogenerate -m "Add new field"

# Apply migrations
alembic upgrade head

# Rollback last migration
alembic downgrade -1

# Check migration status
alembic current
alembic history
```

### Docker

```bash
# Build image
docker build -t ollama:latest .

# Run container
docker run -p 8000:8000 ollama:latest

# Stop/remove
docker stop <container_id>
docker rm <container_id>

# View logs
docker logs -f <container_id>
```

### Testing

```bash
# Run specific test
pytest tests/unit/test_auth.py::test_create_api_key -v

# Run with coverage
pytest tests/ --cov=ollama --cov-report=html

# Generate coverage report
open htmlcov/index.html

# Run integration tests
pytest tests/integration/ -v

# Run load tests
locust -f load_test.py --host http://localhost:8000
```

---

## 🏗️ Project Structure

```
ollama/
├── api/
│   ├── routes/           # API endpoints
│   │   ├── inference.py  # Model inference (7 endpoints)
│   │   ├── auth.py       # Authentication
│   │   ├── chat.py       # Conversations
│   │   └── ...
│   └── dependencies.py   # FastAPI dependency injection
│
├── services/
│   ├── models.py         # OllamaModelManager (async)
│   ├── database.py       # DB operations
│   ├── cache.py          # Redis operations
│   └── ...
│
├── middleware/
│   ├── rate_limit.py     # Rate limiting
│   ├── auth.py           # Authentication
│   └── metrics.py        # Metrics
│
├── models.py             # SQLAlchemy ORM models
├── main.py               # FastAPI app setup
└── config.py             # Configuration
```

---

## 🔑 Key Files to Know

| File                                      | Purpose                    | Lines |
| ----------------------------------------- | -------------------------- | ----- |
| `ollama/main.py`                          | FastAPI app initialization | 80    |
| `ollama/api/routes/inference.py`          | Main API endpoints         | 426   |
| `ollama/services/models.py`               | Ollama integration         | 403   |
| `ollama/models.py`                        | Database models            | 243   |
| `.github/workflows/quality-checks.yml`    | CI/CD checks               | 75    |
| `.github/workflows/deploy-production.yml` | Auto deployment            | 103   |
| `docker-compose.yml`                      | Local services             | 80    |
| `docs/DEPLOYMENT_RUNBOOK.md`              | Deployment guide           | 300+  |

---

## 🧪 Testing Patterns

### Unit Test Template

```python
# tests/unit/test_my_feature.py
import pytest
from ollama.services.models import OllamaModelManager

@pytest.fixture
def model_manager():
    return OllamaModelManager(base_url="http://localhost:11434")

def test_list_models(model_manager):
    """Test listing available models."""
    models = await model_manager.list_available_models()
    assert models is not None
    assert len(models) > 0

@pytest.mark.asyncio
async def test_generate_text(model_manager):
    """Test text generation."""
    request = GenerateRequest(
        model="llama3.2",
        prompt="Test prompt"
    )
    response = await model_manager.generate(request)
    assert response is not None
    assert response.response is not None
```

### Integration Test Template

```python
# tests/integration/test_api_endpoints.py
import pytest
from httpx import AsyncClient
from ollama.main import app

@pytest.mark.asyncio
async def test_health_endpoint():
    """Test health check endpoint."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"
```

---

## 📝 API Endpoints

### Models

```
GET    /api/v1/models                      # List all models
GET    /api/v1/models/{model_name}         # Get model details
POST   /api/v1/models/pull                 # Download model
DELETE /api/v1/models/{model_name}         # Delete model
```

### Generation

```
POST   /api/v1/generate                    # Text generation
POST   /api/v1/embeddings                  # Generate embeddings
POST   /api/v1/chat                        # Chat with history
```

### Utilities

```
GET    /health                             # Health check
GET    /metrics                            # Prometheus metrics
GET    /api/v1/health                      # API health
```

---

## 🔧 Configuration

### Environment Variables

```bash
# Development (.env)
ENVIRONMENT=development
DEBUG=true
DATABASE_URL=postgresql+asyncpg://postgres:password@localhost/ollama
REDIS_URL=redis://localhost:6379/0
OLLAMA_BASE_URL=http://localhost:11434
API_KEY_PREFIX=dev_

# Production (GCP Secret Manager)
ENVIRONMENT=production
DEBUG=false
PUBLIC_API_ENDPOINT=https://ollama.elevatediq.ai
REQUIRE_API_KEY=true
RATE_LIMIT_REQUESTS=100
RATE_LIMIT_WINDOW=60
```

### Settings (code)

```python
# config/settings.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    environment: str = "development"
    debug: bool = False
    database_url: str
    redis_url: str
    ollama_base_url: str = "http://localhost:11434"
    api_key_prefix: str = "sk_"

    class Config:
        env_file = ".env"

settings = Settings()
```

---

## 🚨 Common Issues & Solutions

### Issue: "Connection refused" to Ollama

**Solution**:

```bash
# Check if Ollama is running
docker ps | grep ollama

# Start it
docker-compose up -d ollama

# Verify connection
curl http://ollama:11434/api/tags
```

### Issue: "Database connection error"

**Solution**:

```bash
# Check PostgreSQL
docker ps | grep postgres

# Check URL format
echo $DATABASE_URL

# Test connection
psql $DATABASE_URL -c "SELECT 1"
```

### Issue: "Rate limit exceeded"

**Solution**:

```bash
# Reset rate limiting
redis-cli -h localhost FLUSHALL

# Or wait for window to reset (default: 60s)
```

### Issue: "Pre-commit hook failed"

**Solution**:

```bash
# Fix issues manually
black ollama/ tests/          # Format code
ruff check ollama/ --fix      # Auto-fix lint issues

# Run tests
pytest tests/ -v

# Retry commit
git commit -S -m "feat: my feature"
```

---

## 🔐 Security Checklist

Before committing:

- [ ] No hardcoded passwords or API keys
- [ ] No unencrypted credentials in code
- [ ] All type hints present (`mypy --strict` passes)
- [ ] Linting passes (`ruff check`)
- [ ] All tests pass (`pytest`)
- [ ] Security audit clean (`pip-audit`)
- [ ] Commit is signed (`git commit -S`)

Before pushing:

- [ ] Branch name follows pattern: `feature/`, `bugfix/`, `refactor/`, etc.
- [ ] Commit messages follow format: `type(scope): description`
- [ ] All local tests pass
- [ ] Pre-commit hooks installed (`.githooks/setup.sh`)

---

## 📖 Documentation

| Document                                                         | Purpose                        |
| ---------------------------------------------------------------- | ------------------------------ |
| [README.md](README.md)                                           | Project overview               |
| [DEPLOYMENT_RUNBOOK.md](DEPLOYMENT_RUNBOOK.md)                   | Complete deployment guide      |
| [docs/architecture.md](docs/architecture.md)                     | System architecture (40 pages) |
| [PUBLIC_API.md](PUBLIC_API.md)                                   | API reference                  |
| [docs/POSTGRESQL_INTEGRATION.md](docs/POSTGRESQL_INTEGRATION.md) | Database guide                 |
| [docs/troubleshooting.md](docs/troubleshooting.md)               | Common issues                  |
| [CONTRIBUTING.md](CONTRIBUTING.md)                               | Contribution guide             |

---

## 🚀 Deployment

### Local Development

```bash
# Start all services
docker-compose up -d

# Run migrations
alembic upgrade head

# Start server
uvicorn ollama.main:app --reload --host 0.0.0.0 --port 8000
```

### Production

```bash
# Commit and push to main
git push origin main

# GitHub Actions automatically:
# 1. Runs all quality checks
# 2. Builds Docker image
# 3. Pushes to GCR
# 4. Deploys to Cloud Run
# 5. Verifies health checks

# Check deployment status in GitHub Actions tab
```

---

## 📊 Performance Tips

### Database Queries

```python
# ❌ Bad: N+1 query problem
users = await session.execute(select(User))
for user in users:
    keys = user.api_keys  # Separate query per user!

# ✅ Good: Eager loading
users = await session.execute(
    select(User).options(joinedload(User.api_keys))
)

# ✅ Good: Specific columns
result = await session.execute(
    select(User.id, User.username)
)
```

### Caching

```python
# Use Redis for frequently accessed data
@app.get("/api/v1/models", response_model=ListModelsResponse)
async def list_models(cache: Redis = Depends(get_redis)):
    # Check cache
    cached = await cache.get("models_list")
    if cached:
        return json.loads(cached)

    # Fetch and cache
    models = await model_manager.list_available_models()
    await cache.setex("models_list", 3600, json.dumps(models))

    return {"models": models}
```

### Streaming

```python
# Use streaming for long responses
@app.post("/api/v1/generate", response_class=StreamingResponse)
async def generate_streaming(request: GenerateRequest):
    async def event_generator():
        async for token in model_manager.generate_streaming(request):
            yield f"data: {json.dumps(token)}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")
```

---

## 💡 Tips & Tricks

```bash
# View service logs in real-time
docker-compose logs -f api

# Access database directly
docker-compose exec postgres psql -U postgres -d ollama

# Monitor Redis
docker-compose exec redis redis-cli MONITOR

# Generate coverage report
pytest --cov=ollama --cov-report=html && open htmlcov/index.html

# Profile code
python -m cProfile -s cumulative main.py > profile.txt
python -c "import pstats; stats = pstats.Stats('profile.txt'); stats.sort_stats('cumulative').print_stats(20)"

# Run specific test with debugging
pytest tests/unit/test_auth.py::test_create_api_key -v -s --pdb
```

---

## 🎯 Code Style

### Python Style

```python
# Type hints on all functions
async def generate(request: GenerateRequest) -> GenerateResponse:
    """Generate text completion.

    Args:
        request: Generation request with model and prompt.

    Returns:
        Generated response with text and metrics.
    """
    # Implementation...
    pass

# Docstrings (Google style)
def my_function(param: str) -> str:
    """One-line description.

    Longer description explaining what this does.
    Can span multiple lines.

    Args:
        param: Parameter description.

    Returns:
        Return value description.

    Raises:
        ValueError: When parameter is invalid.
    """
    pass

# Use async/await
async def fetch_data():
    result = await client.get(url)
    return result

# Format with black (line length 100)
# Check with ruff
# Type check with mypy --strict
```

---

## 📞 Getting Help

1. **Check documentation**: Start with [README.md](README.md)
2. **Search issues**: GitHub Issues tab
3. **Read runbook**: [DEPLOYMENT_RUNBOOK.md](DEPLOYMENT_RUNBOOK.md)
4. **Ask team**: Create GitHub Discussion
5. **File issue**: With reproduction steps and environment details

---

## 🎓 Learning Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [SQLAlchemy 2.0 Docs](https://docs.sqlalchemy.org/)
- [PostgreSQL Guide](https://www.postgresql.org/docs/)
- [pytest Documentation](https://docs.pytest.org/)
- [GCP Cloud Run Docs](https://cloud.google.com/run/docs)

---

**Questions?** Open an issue or discussion on GitHub!

**Ready to contribute?** See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

---

**Version**: 2.0.0
**Last Updated**: January 13, 2026
**Status**: ✅ Up-to-date

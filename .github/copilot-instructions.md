# Ollama Elite AI Platform - GitHub Copilot Instructions

## Project Overview

**Ollama** is a production-grade local AI infrastructure platform for building, deploying, and monitoring large language models. All AI workloads run locally on Docker containers with optional GCP Load Balancer for public access via `https://elevatediq.ai/ollama`.

**Core Purpose**: Provide engineers with enterprise-grade reliability, security, and performance for local AI inference.

**Target Audience**: Elite engineers, research teams, enterprises requiring air-gapped AI systems.

## Core Development Principles

### 1. Precision & Quality First
- Every line of code is production-ready—no sketches, prototypes, or placeholders
- Type hints are mandatory on all function signatures (Python 3.11+)
- 100% test coverage for critical paths; ≥90% overall coverage
- Code reviews required before merging to main

### 2. Local Sovereignty with Public Access
- All AI models and inference engines run locally (Docker containers)
- Zero cloud dependencies for model execution
- Optional GCP Load Balancer for public endpoint (elevatediq.ai/ollama)
- Data never leaves local infrastructure unless explicitly configured

### 3. Security & Privacy Non-Negotiable
- API key authentication for all public endpoints
- Rate limiting enforced at LB and application layers
- CORS with explicit allow lists (never use *)
- TLS 1.3+ for public traffic, mutual TLS for internal services
- Never commit credentials—use `.env.example` templates
- Sign all git commits: `git commit -S`
- Regular security audits with `pip-audit`, `safety`, Snyk

### 4. Architecture Excellence
- **Language**: Python 3.11+ (primary), TypeScript for tooling
- **Framework**: FastAPI (async-first), SQLAlchemy 2.0+
- **Database**: PostgreSQL (primary), Redis (cache/queues)
- **Containerization**: Docker 24+, Docker Compose 2.20+
- **Monitoring**: Prometheus, Grafana, Jaeger (distributed tracing)
- **ML Stack**: Ollama, PyTorch, HuggingFace Transformers

## Code Structure and Patterns

### Directory Layout
```
ollama/
├── app/                    # FastAPI application
│   ├── api/               # API routes and schemas
│   ├── repositories/      # Data access layer
│   ├── services/          # Business logic
│   ├── middleware/        # Request/response processing
│   └── monitoring/        # Observability
├── config/                # Configuration files
├── docker/                # Docker configuration
├── docs/                  # Documentation
├── k8s/                   # Kubernetes manifests
├── monitoring/            # Prometheus, Grafana configs
├── scripts/               # Automation scripts
├── tests/                 # Test suites
│   ├── unit/
│   ├── integration/
│   └── e2e/
└── alembic/               # Database migrations
```

### Module Organization
Every Python module must include:
- Clear single responsibility
- Type hints on all functions
- Google-style docstrings with examples
- Proper error handling with custom exception hierarchy
- Unit tests co-located in `tests/` directory

### Example Code Pattern
```python
from typing import Optional
from pydantic import BaseModel, Field

class ModelRequest(BaseModel):
    """Request schema for model inference.
    
    Args:
        prompt: User input text
        max_tokens: Maximum tokens to generate
        temperature: Sampling temperature (0.0-2.0)
    
    Example:
        >>> req = ModelRequest(prompt="Hello world", max_tokens=100)
        >>> req.temperature
        0.7
    """
    prompt: str = Field(..., min_length=1, max_length=10000)
    max_tokens: Optional[int] = Field(default=512, ge=1, le=4096)
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)

async def generate_response(
    request: ModelRequest,
    model_name: str
) -> dict[str, Any]:
    """Generate model response asynchronously.
    
    Args:
        request: Validated request parameters
        model_name: Name of the Ollama model to use
    
    Returns:
        Dictionary containing generated text and metadata
        
    Raises:
        ModelNotFoundError: If model doesn't exist
        InferenceError: If generation fails
    """
    # Implementation...
```

## Development Workflow

### Git Commit Standards
- **Format**: `type(scope): description`
- **Types**: `feat`, `fix`, `refactor`, `perf`, `test`, `docs`, `infra`, `security`
- **Examples**:
  - `feat(api): add conversation history endpoint`
  - `fix(auth): resolve token expiration edge case`
  - `perf(inference): optimize batch processing for 2x throughput`
  - `security(cors): restrict origins to allowlist`
  - `docs(readme): update deployment instructions`

### Branch Naming
- `feature/add-conversation-api`
- `bugfix/fix-token-refresh`
- `refactor/simplify-model-loading`
- `infra/add-kubernetes-manifests`
- `security/add-rate-limiting`

### Required Checks Before Commit
1. All tests pass: `pytest tests/ -v`
2. Type checking passes: `mypy ollama/ --strict`
3. Linting passes: `ruff check ollama/`
4. Security audit clean: `pip-audit`
5. Coverage threshold met: `pytest --cov=ollama --cov-report=term-missing`

## Testing Strategy

### Test Types and Coverage
```python
# Unit Test Example (tests/unit/test_auth.py)
import pytest
from ollama.services.auth import generate_api_key, verify_api_key

def test_generate_api_key():
    """API key generation produces valid format."""
    key = generate_api_key(prefix="sk")
    assert key.startswith("sk-")
    assert len(key) == 48

def test_verify_api_key_valid():
    """Valid API key passes verification."""
    key = generate_api_key()
    assert verify_api_key(key) is True

@pytest.mark.asyncio
async def test_verify_api_key_rate_limit(redis_client):
    """Rate limiting blocks excessive requests."""
    key = generate_api_key()
    # Simulate 100 requests in 1 second
    for _ in range(100):
        await verify_api_key(key, redis=redis_client)
    
    with pytest.raises(RateLimitExceeded):
        await verify_api_key(key, redis=redis_client)
```

### Integration Tests
- Test real component interactions (DB, Redis, model inference)
- Use Docker Compose for isolated test environments
- Clean up resources after each test

### Performance Tests
- Benchmark critical paths (inference latency, API response time)
- Track regressions with historical data
- Document performance characteristics

## API Design Principles

### RESTful Endpoints
```
POST   /api/v1/generate          # Generate text completion
POST   /api/v1/chat              # Chat completion with context
POST   /api/v1/embeddings        # Generate embeddings
GET    /api/v1/models            # List available models
GET    /api/v1/models/{name}     # Get model details
POST   /api/v1/conversations     # Create conversation
GET    /api/v1/conversations/{id} # Get conversation history
POST   /api/v1/documents         # Upload document for RAG
GET    /health                   # Health check (no auth required)
GET    /metrics                  # Prometheus metrics (internal only)
```

### Response Format
```json
{
  "success": true,
  "data": {
    "text": "Generated response...",
    "model": "llama3.2",
    "tokens_used": 142,
    "inference_time_ms": 1250
  },
  "metadata": {
    "request_id": "req_abc123",
    "timestamp": "2026-01-13T10:30:00Z"
  }
}
```

### Error Handling
```json
{
  "success": false,
  "error": {
    "code": "RATE_LIMIT_EXCEEDED",
    "message": "Rate limit exceeded. Retry after 60 seconds.",
    "details": {
      "limit": 100,
      "window": "1m",
      "retry_after": 60
    }
  },
  "metadata": {
    "request_id": "req_xyz789",
    "timestamp": "2026-01-13T10:30:00Z"
  }
}
```

## Security Requirements

### Authentication & Authorization
- API keys for all endpoints (except `/health`)
- JWT tokens for user sessions (future)
- Role-based access control (RBAC) for team deployments
- Audit logging for all authenticated requests

### Input Validation
- Validate all user inputs with Pydantic models
- Sanitize prompts to prevent injection attacks
- Limit request sizes (10MB max for documents)
- Rate limiting per API key (100 req/min default)

### Network Security
- TLS 1.3+ for public endpoints
- Internal services use mutual TLS
- Firewall rules for container network isolation
- DDoS protection via Cloud Armor (public endpoint)

### Data Protection
- Encrypt sensitive data at rest (API keys, user data)
- Secure credential management (env vars, secret managers)
- PII detection and redaction for compliance
- Regular backups with encryption

## Performance Optimization

### Inference Optimization
- Batch processing for multiple requests
- Model caching with LRU eviction
- Quantization for memory efficiency (4-bit, 8-bit)
- GPU acceleration when available (CUDA, ROCm)
- Streaming responses for long-form generation

### Application Performance
- Connection pooling for database and Redis
- Async I/O for all network operations
- Response caching with TTL
- CDN for static content
- Lazy loading for large models

### Performance Baselines
- API response time: <500ms p99 (excluding inference)
- Model inference: Document per-model (e.g., llama3.2: 50 tok/s)
- Startup time: <10s for full stack
- Memory footprint: <2GB baseline (excluding models)
- Database queries: <100ms p95

## Monitoring & Observability

### Metrics to Track
```python
# Prometheus metrics
inference_requests_total = Counter(
    "ollama_inference_requests_total",
    "Total inference requests",
    ["model", "status"]
)

inference_latency_seconds = Histogram(
    "ollama_inference_latency_seconds",
    "Inference latency in seconds",
    ["model"],
    buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0]
)

model_cache_hits = Counter(
    "ollama_model_cache_hits_total",
    "Model cache hits",
    ["model"]
)
```

### Structured Logging
```python
import structlog

log = structlog.get_logger()

log.info(
    "inference_completed",
    model=model_name,
    tokens=tokens_generated,
    latency_ms=latency,
    request_id=request_id,
    user_id=user_id
)
```

### Alerting
- API error rate > 1%
- Inference latency p99 > 10s
- Model cache hit rate < 70%
- Database connection pool exhaustion
- Disk usage > 80%
- Memory usage > 90%

## Deployment Practices

### Local Development
```bash
# Start all services
docker-compose up -d

# Run migrations
alembic upgrade head

# Start dev server with hot reload
uvicorn ollama.main:app --reload --host 0.0.0.0 --port 8000
```

### Production Deployment
```bash
# Build production image
docker build -t ollama:latest -f docker/Dockerfile .

# Run production stack
docker-compose -f docker-compose.prod.yml up -d

# Health check
curl https://elevatediq.ai/ollama/health
```

### Deployment Checklist
- [ ] All tests passing
- [ ] Security audit clean
- [ ] Performance benchmarks meet baselines
- [ ] Documentation updated
- [ ] Rollback plan documented
- [ ] Monitoring dashboards configured
- [ ] Alerts configured
- [ ] Load testing completed
- [ ] Database migrations tested
- [ ] Backup verified

## Documentation Standards

### Code Documentation
- All modules have docstrings explaining purpose
- Complex algorithms include step-by-step comments
- Public APIs have usage examples
- Type hints on all function signatures

### External Documentation
- `README.md`: Quick start and overview
- `docs/architecture.md`: System design and components
- `docs/DEPLOYMENT.md`: Deployment procedures
- `docs/public-deployment.md`: GCP Load Balancer setup
- `docs/monitoring.md`: Observability and alerting
- `CONTRIBUTING.md`: Contribution guidelines

### Architecture Decision Records (ADRs)
Document major architectural decisions:
- Context: What problem are we solving?
- Decision: What approach did we choose?
- Consequences: What are the trade-offs?
- Alternatives: What else did we consider?

## Copilot Collaboration Guidelines

### When I Ask for "Implementation"
- Write production-ready code with type hints
- Include comprehensive error handling
- Add unit tests alongside implementation
- Update documentation if API changes
- No TODOs or placeholders—complete the feature

### When I Ask for "Analysis"
- Provide deep technical analysis
- List trade-offs for each approach
- Quantify performance implications
- Consider security and scalability
- Recommend best option with rationale

### When I Ask for "Review"
- Check type safety and error handling
- Verify test coverage for new code
- Identify security vulnerabilities
- Flag performance bottlenecks
- Suggest improvements with examples

### When I Ask for "Optimization"
- Profile code before optimizing
- Benchmark before and after changes
- Quantify improvements (latency, memory, throughput)
- Ensure correctness with tests
- Document optimization strategy

### What I Won't Accept Without Escalation
- Code without type hints
- Missing tests for critical paths
- Unvetted dependencies
- Security vulnerabilities
- Ignored linting errors
- Technical debt without tracking

## Common Tasks and Examples

### Adding a New API Endpoint
1. Define Pydantic schema in `ollama/api/schemas/`
2. Create route handler in `ollama/api/routes/`
3. Add business logic in `ollama/services/`
4. Write unit tests in `tests/unit/`
5. Add integration test in `tests/integration/`
6. Update OpenAPI documentation
7. Add to `PUBLIC_API.md` if public-facing

### Adding a New Model
1. Download model: `ollama pull model_name`
2. Add model config to `config/models.yaml`
3. Create model adapter in `ollama/services/models/`
4. Add model tests with sample prompts
5. Benchmark inference performance
6. Update `README.md` with model details
7. Add to monitoring dashboard

### Database Migration
1. Create migration: `alembic revision -m "description"`
2. Write upgrade and downgrade logic
3. Test migration on dev database
4. Document migration in commit message
5. Test rollback procedure
6. Apply to staging, verify
7. Schedule production deployment

## Dependencies Management

### Adding New Dependencies
```bash
# Add to pyproject.toml
poetry add package_name

# Or for requirements.txt (pinned versions)
echo "package_name==1.2.3" >> requirements/base.txt

# Run security audit
pip-audit

# Check for known vulnerabilities
safety check
```

### Approved Dependencies
- **Web**: FastAPI, Uvicorn, Pydantic, SQLAlchemy
- **ML**: PyTorch, Transformers, Ollama, LangChain
- **Data**: Pandas, NumPy, Polars (for large datasets)
- **Database**: asyncpg, psycopg2, redis-py
- **Testing**: pytest, pytest-asyncio, pytest-cov, hypothesis
- **Monitoring**: prometheus-client, opentelemetry
- **Security**: cryptography, pyjwt, argon2-cffi

## Troubleshooting Common Issues

### Model Loading Failures
```python
# Check if model exists
ollama list

# Re-download if corrupted
ollama rm model_name
ollama pull model_name

# Check disk space
df -h
```

### Database Connection Issues
```python
# Verify PostgreSQL is running
docker ps | grep postgres

# Check connection string
echo $DATABASE_URL

# Test connection
psql $DATABASE_URL -c "SELECT 1"
```

### Performance Degradation
```python
# Profile API endpoint
python -m cProfile -o profile.out main.py

# Analyze with snakeviz
snakeviz profile.out

# Check memory usage
memory_profiler --pdb-mmem=100 main.py

# Analyze with flamegraph
py-spy record -o profile.svg -- python main.py
```

## Success Criteria

### Code Quality
- ✅ All code has type hints
- ✅ Test coverage ≥90%
- ✅ No security warnings from audits
- ✅ Linting passes with zero errors
- ✅ Documentation matches implementation

### Performance
- ✅ API response time <500ms p99
- ✅ Model inference meets documented baselines
- ✅ Memory usage within limits
- ✅ Zero memory leaks in 24h stress test

### Security
- ✅ All commits signed
- ✅ No hardcoded credentials
- ✅ Dependencies audited
- ✅ HTTPS enforced for public endpoints
- ✅ Rate limiting functional

### Deployment
- ✅ Health checks passing
- ✅ Monitoring configured
- ✅ Alerts firing correctly
- ✅ Rollback tested
- ✅ Documentation complete

---

**Version**: 2.0.0  
**Last Updated**: January 13, 2026  
**Maintained By**: kushin77/ollama engineering team  
**Repository**: https://github.com/kushin77/ollama

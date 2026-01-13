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
- **MANDATE**: No commits without passing all quality checks (tests, type checking, linting, security audit)

### 2. Local Sovereignty with Public Access
- All AI models and inference engines run locally (Docker containers)
- Zero cloud dependencies for model execution
- **MANDATE**: Default deployment targets `https://elevatediq.ai/ollama` (GCP Load Balancer only)
- **MANDATE**: GCP Load Balancer is the ONLY external communication point for clients
- **MANDATE**: All internal services communicate locally via Docker network
- **MANDATE**: Zero direct client connections to internal services (all routed through LB)
- **MANDATE**: Local development MUST point to real server IP or DNS (never localhost/127.0.0.1)
  - Ensures feature parity with production deployments
  - Catches network-specific issues early
  - Validates DNS resolution and service discovery
- Data never leaves local infrastructure unless explicitly configured

### 3. Security & Privacy Non-Negotiable
- API key authentication for all public endpoints
- Rate limiting enforced at LB and application layers
- CORS with explicit allow lists (never use *)
- TLS 1.3+ for public traffic, mutual TLS for internal services
- Never commit credentials—use `.env.example` templates
- **MANDATE**: Sign all git commits with GPG: `git commit -S` (enforced by hooks)
- **MANDATE**: All commits are immutable and traceable—no force pushes without approval
- Regular security audits with `pip-audit`, `safety`, Snyk

### 4. Architecture Excellence
- **Language**: Python 3.11+ (primary), TypeScript for tooling
- **Framework**: FastAPI (async-first), SQLAlchemy 2.0+
- **Database**: PostgreSQL (primary), Redis (cache/queues)
- **Containerization**: Docker 24+, Docker Compose 2.20+
- **Monitoring**: Prometheus, Grafana, Jaeger (distributed tracing)
- **ML Stack**: Ollama, PyTorch, HuggingFace Transformers
- **MANDATE**: Filesystem structure strictly enforced (see Elite Filesystem Standards)
- **MANDATE**: Docker hygiene and consistency strictly enforced (see Docker Standards)
- **MANDATE**: All development pointing to real IPs/DNS, never localhost (see Development Endpoints)

## Deployment Architecture Mandate

**CRITICAL MANDATE**: All deployment and configuration must default to the GCP Load Balancer topology with zero client access to internal services.

### Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                          EXTERNAL CLIENTS                           │
│                  (Internet, Partner Systems, Users)                 │
└────────────────────────┬────────────────────────────────────────────┘
                         │
                    HTTPS/TLS 1.3+
                         │
        ┌────────────────▼────────────────┐
        │   GCP LOAD BALANCER             │
        │ (https://elevatediq.ai/ollama)  │
        │   - API Key Authentication      │
        │   - Rate Limiting (100 req/min) │
        │   - DDoS Protection (Cloud       │
        │     Armor)                      │
        │   - CORS Enforcement            │
        │   - TLS Termination             │
        └────────────────┬────────────────┘
                         │
                    Mutual TLS 1.3+
                         │
        ┌────────────────▼────────────────────────────────────────┐
        │      DOCKER CONTAINER NETWORK (Internal Only)           │
        │                                                          │
        │  ┌──────────┐   ┌──────────┐   ┌──────────┐             │
        │  │  FastAPI │   │PostgreSQL│   │  Redis   │             │
        │  │  Server  │──▶│ Database │   │  Cache   │             │
        │  │:8000     │   │:5432     │   │:6379     │             │
        │  └──────────┘   └──────────┘   └──────────┘             │
        │       ▲                                                   │
        │       │                                                   │
        │  ┌────────────┐     ┌──────────┐                        │
        │  │  Ollama    │     │Prometheus│                        │
        │  │  Models    │     │ Metrics  │                        │
        │  │:11434      │     │:9090     │                        │
        │  └────────────┘     └──────────┘                        │
        │                                                          │
        └──────────────────────────────────────────────────────────┘
                         ▲
            NO EXTERNAL CLIENT ACCESS
           (Firewall blocked from outside)
```

### MANDATE: Configuration Defaults

**All services and configurations MUST default to:**

1. **Single Entry Point**: `https://elevatediq.ai/ollama`
   - All client requests route through GCP Load Balancer
   - Load Balancer authenticates with API keys
   - Load Balancer enforces rate limits
   - Load Balancer applies security policies

2. **Internal Communication Only**
   - FastAPI server listens on `localhost:8000` (not exposed)
   - Database on `postgres:5432` (Docker network only)
   - Redis on `redis:6379` (Docker network only)
   - Ollama on `ollama:11434` (Docker network only)
   - All inter-service communication via Docker network

3. **No Direct Client Access**
   - Firewall MUST block external connections to ports:
     - 8000 (FastAPI) - Internal only
     - 5432 (PostgreSQL) - Internal only
     - 6379 (Redis) - Internal only
     - 11434 (Ollama) - Internal only
   - Only port 443 (HTTPS) open to external clients → routed to LB

4. **GCP Load Balancer is the ONLY external gateway**
   - LB handles all SSL/TLS termination
   - LB enforces authentication
   - LB applies rate limiting
   - LB provides DDoS protection
   - LB logs all access

### MANDATE: Environment Configuration

**All `.env` files MUST default to:**

```bash
# Default: All services use GCP LB endpoint
PUBLIC_API_ENDPOINT=https://elevatediq.ai/ollama
GCP_LOAD_BALANCER_IP=<GCP-LB-IP>

# Internal services (Docker network)
FASTAPI_HOST=0.0.0.0  # Listen on all interfaces within container
FASTAPI_PORT=8000     # Only accessible from Docker network
DATABASE_URL=postgresql://user:pass@postgres:5432/ollama
REDIS_URL=redis://redis:6379/0
OLLAMA_BASE_URL=http://ollama:11434

# Security defaults
REQUIRE_API_KEY=true  # Always require API key
RATE_LIMIT_REQUESTS=100
RATE_LIMIT_WINDOW=60  # 100 requests per 60 seconds
CORS_ORIGINS=https://elevatediq.ai  # Only LB origin
TLS_MIN_VERSION=1.3

# Production defaults
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=info
```

### MANDATE: Docker Compose Configuration

**docker-compose.yml MUST:**

```yaml
version: '3.9'

services:
  api:
    image: ollama:latest
    container_name: ollama-api
    # ❌ NEVER expose port directly to host
    # ✅ ONLY accessible from Docker network
    ports:
      - "127.0.0.1:8000:8000"  # localhost only (development)
      # Production: NO ports mapping, internal only
    environment:
      FASTAPI_HOST: 0.0.0.0
      FASTAPI_PORT: 8000
      PUBLIC_API_ENDPOINT: https://elevatediq.ai/ollama
    depends_on:
      - postgres
      - redis
      - ollama
    networks:
      - ollama-net

  postgres:
    image: postgres:15-alpine
    container_name: ollama-postgres
    environment:
      POSTGRES_DB: ollama
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
    # ❌ NEVER expose database to external clients
    ports:
      - "127.0.0.1:5432:5432"  # localhost only
    networks:
      - ollama-net
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine
    container_name: ollama-redis
    # ❌ NEVER expose cache to external clients
    ports:
      - "127.0.0.1:6379:6379"  # localhost only
    networks:
      - ollama-net
    command: redis-server --requirepass ${REDIS_PASSWORD}

  ollama:
    image: ollama/ollama:latest
    container_name: ollama-inference
    # ❌ NEVER expose model server to external clients
    ports:
      - "127.0.0.1:11434:11434"  # localhost only
    networks:
      - ollama-net
    volumes:
      - ollama_data:/root/.ollama

networks:
  ollama-net:
    driver: bridge
    # ❌ NEVER expose network to host

volumes:
  postgres_data:
  ollama_data:
```

### MANDATE: API Configuration

**All FastAPI route configurations MUST:**

```python
# app/main.py

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import os

app = FastAPI()

# ✅ MANDATORY: CORS only allows GCP LB
app.add_middleware(
    CORSMiddleware,
    # ❌ NEVER use allow_origins=["*"]
    # ✅ ONLY allow GCP Load Balancer origin
    allow_origins=[
        "https://elevatediq.ai",
        "https://elevatediq.ai/ollama"
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
    max_age=3600
)

# ✅ MANDATORY: Listen on all interfaces within container
# (Only accessible from Docker network, not from host)
HOST = os.getenv("FASTAPI_HOST", "0.0.0.0")
PORT = int(os.getenv("FASTAPI_PORT", 8000))

# ✅ MANDATORY: All endpoints require API key
# (GCP LB will validate and forward)
@app.get("/api/v1/health")
async def health_check():
    """Health check endpoint - public but still authenticated by LB"""
    return {"status": "healthy"}

@app.post("/api/v1/generate")
async def generate(request: GenerateRequest):
    """Generate endpoint - authenticated by GCP LB"""
    # Clients MUST go through GCP LB to reach here
    # This endpoint is NOT accessible directly
    pass

# ✅ MANDATORY: Run only on internal port
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host=HOST,  # 0.0.0.0 - listen on all interfaces in container
        port=PORT,  # 8000 - internal port
        # ❌ NO TLS here - LB handles TLS termination
        # ❌ NO direct client access
    )
```

### MANDATE: Client Connection Flow

```
┌──────────────────┐
│  External Client │
│   (Internet)     │
└────────┬─────────┘
         │
         │ 1. Client connects to:
         │    https://elevatediq.ai/ollama
         │
    ┌────▼────────────────────┐
    │  GCP Load Balancer      │
    │ - Verifies API key      │
    │ - Rate limit check      │
    │ - DDoS check            │
    │ - TLS termination       │
    │ - Route to backend      │
    └────┬────────────────────┘
         │
         │ 2. Internal request (Mutual TLS)
         │    http://api:8000/api/v1/generate
         │    (Docker network only)
         │
    ┌────▼──────────────────────┐
    │  FastAPI Container        │
    │ - Trust LB authentication │
    │ - Process request         │
    │ - Return response         │
    └────┬──────────────────────┘
         │
         │ 3. Response back to LB
         │
    ┌────▼────────────────────┐
    │  GCP Load Balancer      │
    │ - Format response       │
    │ - Set headers           │
    │ - Send to client        │
    └────┬────────────────────┘
         │
    ┌────▼─────────────┐
    │ External Client  │
    │ Response received│
    └──────────────────┘
```

### MANDATE: Firewall Rules (GCP)

**Production firewall MUST enforce:**

```yaml
# Allow external clients to GCP LB only
- ingress:
    from_internet: true
    protocol: tcp
    port: 443  # HTTPS only
    target: gcp-load-balancer

# Block external access to all internal services
- ingress:
    from_internet: true
    protocol: tcp
    port: 8000  # FastAPI
    deny: true

- ingress:
    from_internet: true
    protocol: tcp
    port: 5432  # PostgreSQL
    deny: true

- ingress:
    from_internet: true
    protocol: tcp
    port: 6379  # Redis
    deny: true

- ingress:
    from_internet: true
    protocol: tcp
    port: 11434  # Ollama
    deny: true

# Allow internal container communication
- ingress:
    from: docker-network
    protocol: tcp
    ports: [8000, 5432, 6379, 11434]
    allow: true
```

### MANDATE: Configuration Code Examples

**❌ WRONG - Never do this:**

```python
# FORBIDDEN: Exposing internal service directly
@app.get("/")
async def root():
    return {"message": "API is running"}
# If this runs on port 8000 and is exposed to internet, it's vulnerable!

# FORBIDDEN: Accepting requests from anywhere
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # ❌ Opens to all clients
)

# FORBIDDEN: Listening on 0.0.0.0 with TLS in FastAPI
# (TLS should only be at LB)
uvicorn.run(app, ssl_keyfile="...", ssl_certfile="...")

# FORBIDDEN: Hardcoding internal service URLs
OLLAMA_URL = "http://localhost:11434"  # ❌ No localhost in Docker
DATABASE_URL = "postgresql://localhost/ollama"  # ❌ No localhost
```

**✅ CORRECT - Always do this:**

```python
# CORRECT: All endpoints accessible only through GCP LB
@app.get("/api/v1/health")
async def health_check():
    """Only reachable through https://elevatediq.ai/ollama/api/v1/health"""
    return {"status": "healthy"}

# CORRECT: Restricting CORS to LB only
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://elevatediq.ai",
        "https://elevatediq.ai/ollama"
    ],
)

# CORRECT: No TLS in FastAPI (LB handles it)
uvicorn.run(
    app,
    host="0.0.0.0",  # Listen in container
    port=8000,        # Internal port
    # ❌ No ssl_keyfile or ssl_certfile
)

# CORRECT: Using Docker service names
OLLAMA_URL = "http://ollama:11434"  # Docker service name
DATABASE_URL = "postgresql://postgres:5432/ollama"  # Docker service
```

### MANDATE: Testing and Validation

**All deployment code MUST include:**

```python
# tests/integration/test_deployment_architecture.py

def test_api_only_accessible_through_lb():
    """Verify FastAPI only listens internally"""
    # Should NOT be able to connect directly to port 8000 from outside
    with pytest.raises(ConnectionError):
        requests.get("http://<public-ip>:8000/health", timeout=2)

def test_gcp_lb_is_only_external_endpoint():
    """Verify only GCP LB accepts external connections"""
    # Should be able to connect through GCP LB
    response = requests.get(
        "https://elevatediq.ai/ollama/api/v1/health",
        headers={"Authorization": "Bearer <api-key>"}
    )
    assert response.status_code == 200

def test_cors_restricts_to_lb_only():
    """Verify CORS only allows GCP LB"""
    # Direct request without proper origin should be rejected
    with pytest.raises(requests.exceptions.ConnectionError):
        requests.get(
            "http://api:8000/health",
            headers={"Origin": "https://external-site.com"}
        )

def test_internal_services_not_exposed():
    """Verify internal services don't accept external connections"""
    # PostgreSQL should not be accessible from outside
    with pytest.raises(ConnectionError):
        psycopg2.connect(
            host="<public-ip>",
            port=5432,
            database="ollama"
        )

def test_firewall_blocks_internal_ports():
    """Verify firewall rules are enforced"""
    closed_ports = [8000, 5432, 6379, 11434]
    for port in closed_ports:
        with pytest.raises(ConnectionRefusedError):
            socket.create_connection(("<public-ip>", port), timeout=2)
```

### MANDATE: Documentation

**All deployment documentation MUST include:**

1. **Architecture diagram** showing:
   - GCP LB as single entry point
   - Internal Docker network with no external access
   - Service communication paths
   - Default endpoint: `https://elevatediq.ai/ollama`

2. **Configuration guide** stating:
   - Default values for all services
   - Environment variables and their defaults
   - No way to expose internal services directly
   - All configuration options assume GCP LB routing

3. **Security checklist** verifying:
   - FastAPI only listens on localhost/Docker network
   - Database not accessible externally
   - Redis not accessible externally
   - Ollama not accessible externally
   - Firewall blocks all internal ports
   - GCP LB is only external entry point

## Code Structure and Patterns

### Directory Layout
```
ollama/
├── app/                    # FastAPI application
│   ├── api/               # API routes and schemas
│   │   ├── routes/        # Route handlers (one file per resource)
│   │   ├── schemas/       # Pydantic models (request/response)
│   │   └── dependencies.py # Dependency injection
│   ├── repositories/      # Data access layer (one class per entity)
│   ├── services/          # Business logic (one file per domain)
│   ├── middleware/        # Request/response processing
│   ├── exceptions.py      # Custom exception hierarchy
│   ├── models.py          # SQLAlchemy ORM models
│   └── monitoring/        # Observability (logging, metrics, tracing)
├── config/                # Configuration files
│   ├── settings.py        # Environment-based settings
│   ├── development.yaml   # Dev environment config
│   └── production.yaml    # Production environment config
├── docker/                # Docker configuration
│   ├── Dockerfile         # Multi-stage build
│   ├── nginx/            # Reverse proxy config
│   ├── postgres/         # Database initialization
│   └── redis/            # Cache initialization
├── docs/                  # Documentation
│   ├── architecture.md    # System design
│   ├── api-design.md      # API conventions
│   ├── DEPLOYMENT.md      # Deployment procedures
│   └── troubleshooting.md # Common issues and solutions
├── k8s/                   # Kubernetes manifests
│   ├── base/             # Base configurations
│   ├── overlays/         # Environment-specific overlays
│   └── helm/             # Helm charts
├── monitoring/            # Prometheus, Grafana, Jaeger configs
│   ├── prometheus.yml    # Metrics collection
│   ├── alerts.yml        # Alert rules
│   └── grafana/          # Dashboard definitions
├── scripts/               # Automation and utility scripts
│   ├── setup.sh          # Initial setup
│   ├── migrate.sh        # Database migrations
│   └── health-check.sh   # Health verification
├── tests/                 # Test suites (mirror app structure)
│   ├── unit/             # Unit tests (fast, isolated)
│   ├── integration/      # Integration tests (with services)
│   └── e2e/              # End-to-end tests (full stack)
├── alembic/              # Database migrations
│   └── versions/         # Migration scripts (ordered, descriptive names)
└── venv/                 # Virtual environment (gitignored)
```

### Elite Filesystem Standards

**MANDATE**: Filesystem structure is non-negotiable and strictly enforced.

#### Naming Conventions
- **Modules**: `lowercase_with_underscores.py` (snake_case)
- **Classes**: `PascalCase` (CapWords)
- **Functions**: `snake_case`
- **Constants**: `SCREAMING_SNAKE_CASE`
- **Files per module**: Maximum 1 class per file (exceptions: helper constants, enums in same file)
- **Directories**: Singular or plural consistently (`services/`, `repositories/`, `api/routes/`)

#### File Organization Rules
```python
# Standard module header (ALWAYS INCLUDE)
"""Module description in one sentence.

Detailed description (2-3 sentences) explaining what this module does,
its responsibilities, and how it fits into the system.

Example:
    >>> from ollama.services.auth import generate_api_key
    >>> key = generate_api_key(prefix="sk")
    >>> print(key)
    sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
"""

# Imports (organized in groups)
from typing import Optional, Any
from pathlib import Path
import logging

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
import structlog

from ollama.exceptions import AuthenticationError
from ollama.repositories.user import UserRepository

# Module-level constants
DEFAULT_TOKEN_EXPIRY = 3600
MAX_RETRIES = 3

# Logger
log = structlog.get_logger(__name__)

# Classes
class APIKeyManager:
    """Manages API key generation, validation, and revocation."""

    def __init__(self, repo: UserRepository) -> None:
        """Initialize manager with user repository."""
        self.repo = repo

    def generate_key(self, prefix: str = "sk") -> str:
        """Generate a cryptographically secure API key."""
        # Implementation...
```

#### Test File Mirroring
- Tests mirror app structure exactly
- Test file: `tests/unit/test_auth.py` mirrors `ollama/services/auth.py`
- Test class: `TestAPIKeyManager` for `APIKeyManager` class
- Test method: `test_generate_key_valid` for `generate_key` method
- Prefix test methods with `test_` and use descriptive names

#### Directory Creation Rules
- Create parent directories only when needed (no premature structure)
- Use consistent naming across the codebase
- Document directory purpose in `__init__.py` docstring
- One domain per directory (never mix auth with models)

### Module Organization
Every Python module must include:
- Clear docstring explaining module purpose (not class, not function, but module)
- Single responsibility principle (one domain = one file)
- Type hints on all functions (no exceptions)
- Google-style docstrings with examples
- Proper error handling with custom exception hierarchy
- Unit tests co-located in `tests/` directory (mirroring structure)
- All imports organized and sorted (stdlib, third-party, local)

## Function Separation & Elite Coding Standards

### Single Responsibility Principle (SRP)
- **MANDATE**: Every function has ONE reason to change
- **Function Length**: Maximum 50 lines (ideal), 100 lines (acceptable)
- **Cognitive Complexity**: Max complexity score of 10 (measure with flake8-cognitive-complexity)
- **Parameters**: Max 4 parameters (use dataclasses for more)
- **Returns**: Return single value or explicit tuple (never implicit)

#### Function Design Rules
```python
# ❌ BAD: Function does too much (violates SRP)
def process_user_and_generate_token(user_data: dict) -> dict:
    """Validates user, stores in DB, generates token, sends email."""
    # 50+ lines mixing validation, DB, crypto, and email
    user = validate_user_data(user_data)  # Validation
    db.users.insert(user)                 # Data access
    token = generate_jwt(user.id)         # Cryptography
    send_welcome_email(user.email)        # External service
    return {"user": user, "token": token}

# ✅ GOOD: Each function has single purpose
def validate_user_data(data: dict) -> UserData:
    """Validate user input data."""
    schema = UserSchema()
    return schema.load(data)

def persist_user(user: UserData) -> User:
    """Save validated user to database."""
    return UserRepository().create(user)

def generate_user_token(user_id: UUID) -> str:
    """Generate JWT token for user."""
    return TokenGenerator().create_token(user_id)

async def notify_user_registration(user: User) -> None:
    """Send welcome email to user."""
    await EmailService().send_welcome(user.email)

async def register_user(user_data: dict) -> dict:
    """Orchestrate user registration workflow.

    Coordinates validation, persistence, token generation, and notification.
    """
    user = validate_user_data(user_data)
    persisted_user = persist_user(user)
    token = generate_user_token(persisted_user.id)
    await notify_user_registration(persisted_user)
    return {"user": persisted_user, "token": token}
```

### Pure Functions & Immutability
- **MANDATE**: Favor pure functions (no side effects)
- **Rule**: If function has side effects, prefix name with verb: `send_email()`, `persist_user()`
- **Never modify inputs**: Use `dataclasses.replace()` or `copy.deepcopy()`

```python
# ❌ BAD: Modifies input (side effect)
def apply_discount(product: dict) -> dict:
    """Apply discount to product."""
    product["price"] = product["price"] * 0.9  # Modifies input!
    return product

# ✅ GOOD: Pure function (no side effects)
def apply_discount(product: Product) -> Product:
    """Return product with discount applied."""
    from dataclasses import replace
    discounted_price = product.price * 0.9
    return replace(product, price=discounted_price)
```

### Error Handling: Explicit Over Implicit
- **MANDATE**: Always use custom exception hierarchy
- **Never**: Catch `Exception` (catch specific exceptions)
- **Never**: Silent failures or bare `except` clauses
- **Always**: Provide context in exceptions (message + data)

```python
# ❌ BAD: Silent failure, bare except
try:
    inference_engine.generate(prompt)
except:
    pass  # What happened?!

# ✅ GOOD: Explicit exception handling
try:
    response = inference_engine.generate(prompt)
except ModelNotFoundError as e:
    log.error("model_not_found", model=e.model_name, prompt=prompt[:50])
    raise APIException(
        code="MODEL_NOT_FOUND",
        message=f"Model {e.model_name} not found",
        status_code=404
    )
except InferenceTimeoutError as e:
    log.warning("inference_timeout", elapsed_ms=e.elapsed_ms)
    raise APIException(
        code="INFERENCE_TIMEOUT",
        message="Inference timed out. Try again.",
        status_code=504
    )
```

### Type Safety: Always
- **MANDATE**: 100% type coverage for all functions
- **Rule**: `mypy ollama/ --strict` must pass without errors
- **Never**: Use `Any` without explicit `# type: ignore` with justification
- **Always**: Type method arguments and return values

```python
# ❌ BAD: No types, uses Any
def process_request(request):
    data = request.json()
    result = do_something(data)
    return result

# ✅ GOOD: Full type coverage
from typing import Optional
from fastapi import Request
from ollama.api.schemas import QueryRequest, QueryResponse

async def process_request(request: Request) -> QueryResponse:
    """Process query request and return response."""
    data = await request.json()
    query = QueryRequest(**data)
    result = await do_something(query)
    return QueryResponse(**result)
```

### Testing & Coverage
- **MANDATE**: ≥90% code coverage, 100% for critical paths
- **Rule**: Test file for every module (mirror structure)
- **Never**: Skip test or use `# pragma: no cover` without approval
- **Always**: Test happy path, edge cases, and error paths

```python
# ❌ BAD: Untested code paths
def validate_input(value: int) -> bool:
    if value < 0:
        return False  # Not tested!
    return value > 100

# ✅ GOOD: All paths tested
def validate_input(value: int) -> bool:
    """Validate that value is positive and > 100."""
    return value > 0 and value > 100

class TestValidateInput:
    """Tests for validate_input function."""

    def test_valid_input(self) -> None:
        """Input above 100 returns True."""
        assert validate_input(150) is True

    def test_below_threshold(self) -> None:
        """Input below 100 returns False."""
        assert validate_input(50) is False

    def test_negative_input(self) -> None:
        """Negative input returns False."""
        assert validate_input(-10) is False

    def test_boundary_100(self) -> None:
        """Input exactly 100 returns False."""
        assert validate_input(100) is False

    def test_boundary_101(self) -> None:
        """Input 101 returns True."""
        assert validate_input(101) is True
```

### Code Organization: Vertical Density
- **Related code should be close together** (but not crowded)
- **Unrelated code should be separated** (different files/modules)
- **Order of declarations**: Classes before functions, public before private
- **Imports at top** (organized: stdlib, third-party, local)

```python
# Standard module structure
"""Module description."""

from typing import Optional
import logging

from fastapi import HTTPException
from pydantic import BaseModel

import structlog

from ollama.exceptions import AuthenticationError
from ollama.repositories.user import UserRepository

log = structlog.get_logger(__name__)

# Constants
DEFAULT_EXPIRY = 3600

# Classes (public first)
class APIKeyManager:
    """Manages API keys."""

    def generate_key(self) -> str:
        """Generate key."""
        ...

    def _validate_key(self, key: str) -> bool:
        """Private helper method."""
        ...

# Functions (public first)
async def authenticate_request(token: str) -> dict:
    """Authenticate incoming request."""
    ...

# Private functions (underscore prefix)
def _parse_token(token: str) -> dict:
    """Parse JWT token."""
    ...
```

## Development Workflow

### Mandatory Git Hygiene

**MANDATE**: Perfect git history is non-negotiable.

#### Commit Frequency & Size
- **Commit Early, Commit Often**: Minimum of 1 meaningful commit per 30 minutes of development
- **Atomic Commits**: Each commit represents ONE logical unit of work
  - Commit should be reversible without breaking other commits
  - Should not contain unrelated changes (e.g., don't mix refactoring with new features)
  - All tests passing at every commit (enforce with pre-commit hooks)
- **Maximum File Changes Per Commit**:
  - Ideal: 5-10 files
  - Acceptable: Up to 20 files
  - Never: Single commits touching 100+ files (split into logical chunks)
- **Commit Size Guide**:
  - Small: 10-50 lines changed (ideal)
  - Medium: 50-200 lines changed (acceptable)
  - Large: 200-500 lines changed (review needed)
  - Never: Single commits > 1000 lines (always split)

#### Commit Message Standards
- **Format**: `type(scope): description`
- **Rules**:
  - First line (subject): Max 50 characters
  - Blank line after subject (required)
  - Body: Explain WHAT and WHY, not HOW
  - Body lines: Max 72 characters
  - Sign all commits: `git commit -S` (GPG signing enforced)
  - Reference issues: `Fixes #123` or `Relates to #456`

**Types** (must be lowercase):
- `feat`: New feature (always increases version minor)
- `fix`: Bug fix (increases patch version)
- `refactor`: Code refactoring without behavior change
- `perf`: Performance improvement
- `test`: Adding/modifying tests
- `docs`: Documentation updates
- `infra`: Infrastructure, CI/CD, Docker changes
- `security`: Security-related changes
- `chore`: Maintenance, dependency updates

**Scope** (lowercase, 15 chars max):
- `api`: API routes and endpoints
- `auth`: Authentication and authorization
- `models`: ML model integration
- `db`: Database and repositories
- `cache`: Redis and caching
- `config`: Configuration management
- `docker`: Docker and containerization
- `k8s`: Kubernetes orchestration
- `monitoring`: Observability, metrics, logging
- `testing`: Test infrastructure
- `types`: Type hints and mypy fixes

**Examples**:
```
feat(api): add streaming response support

Add support for server-sent events (SSE) in the inference endpoint.
This allows clients to receive partial responses as tokens are generated,
improving perceived latency for long-form generations.

Implements RFC-001: Streaming API Design
Performance improvement: 40% reduction in perceived latency
All existing tests pass. New tests added for SSE handling.

Fixes #234
```

```
fix(auth): resolve token expiration race condition

Previously, concurrent requests could both trigger token refresh,
causing duplicate refresh tokens to be issued.

Now using atomic compare-and-swap operation for token updates.
Race condition eliminated; all auth tests pass.

Fixes #198
```

```
refactor(services): split inference into dedicated modules

Move inference logic from monolithic services/models.py into:
- services/inference/generation.py
- services/inference/embedding.py
- services/inference/completion.py

No functional changes. All tests passing.
Test coverage maintained at 94%.
```

#### Push Frequency
- **MANDATE**: Push commits at least every 4 hours of active development
- **Rationale**: Reduces risk of local loss, enables early detection of conflicts
- **Workflow**: After each atomic commit that passes all checks → Push immediately
  ```bash
  git add .
  git commit -S -m "feat(api): implement new endpoint"
  git push origin feature/my-feature  # Push IMMEDIATELY
  ```
- **Never**: Work locally for more than 4 hours without pushing
- **Never**: Accumulate commits without pushing (max 5 commits before push)
- **Rule**: One push per meaningful feature segment

#### Branch Naming (Strict Rules)
- **Format**: `{type}/{descriptive-name}`
- **Valid Types**: `feature`, `bugfix`, `refactor`, `infra`, `security`, `docs`
- **Rules**:
  - Lowercase only
  - Hyphens, not underscores
  - Max 40 characters after type
  - Descriptive but concise
- **Examples**:
  - ✅ `feature/add-conversation-api`
  - ✅ `bugfix/fix-token-refresh-race`
  - ✅ `refactor/simplify-model-loading`
  - ✅ `security/add-rate-limiting`
  - ❌ `Feature/Add_Conversation_API` (wrong format)
  - ❌ `feature/add-new-awesome-conversation-endpoint-with-history` (too long)

#### Before Every Commit

**MANDATE**: Run ALL checks before committing. Enforce with pre-commit hooks.

```bash
# Run in sequence (stops on first failure)
pytest tests/ -v --cov=ollama --cov-report=term-missing  # Must pass
mypy ollama/ --strict                                    # Must pass
ruff check ollama/                                       # Must pass
pip-audit                                               # Must pass

# If all pass: commit
git commit -S -m "type(scope): description"
git push origin feature/branch-name
```

Or run all at once with VS Code task (See "Run All Checks" task).

#### Conflict Resolution Rules
- **Always resolve locally** before pushing
- **Never commit with conflict markers** (`<<<<<<<`, `=======`, `>>>>>>>`)
- **When pulling**: Check for conflicts immediately
  ```bash
  git pull origin main
  # If conflicts exist:
  # 1. Fix conflicts manually
  # 2. Run all tests to verify fix
  # 3. Commit: git commit -S -m "merge: resolve conflicts with main"
  # 4. Push immediately
  ```

#### Force Push Policy
- **MANDATE**: No force pushes without explicit approval (enforce in CI/CD)
- **Rationale**: Maintains immutable, traceable history
- **Exception**: Only on personal feature branches (never on main/develop)
- **Alternative**: Use `git rebase -i` locally, then force push (after approval)

#### PR Creation Workflow
1. Ensure all commits follow naming standards
2. Verify branch name matches pattern
3. Ensure all tests pass on branch
4. Create PR with comprehensive description (see PR Template)
5. Run all checks: Type check, lint, tests, security audit
6. Request code review
7. Address all feedback
8. Merge only after approval + all checks pass

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

## Docker Standards & Hygiene

### MANDATE: Container Hygiene

**Image Management**:
- All images use explicit version tags (never `latest` tag)
- All images from trusted registries (Docker Hub official, GCR, ECR)
- Minimal base images: `alpine:3.18`, `python:3.12-slim`, `postgres:15-alpine`
- No hardcoded credentials in images (use secrets/env vars)
- Regular vulnerability scanning with Trivy
- Build images with multi-stage builds to minimize size
- Remove build dependencies to reduce final image size
- Document all image contents and dependencies

**Container Consistency**:
- All containers use same network driver (`bridge`)
- Container names follow pattern: `ollama-{service}-{env}` (e.g., `ollama-api-dev`)
- All containers have resource limits: `memory`, `cpus`
- All containers have health checks with 30s timeout
- Health check returns exit code 0 (healthy) or 1 (unhealthy)
- Container restart policy: `on-failure:3` (except for one-off tasks)
- All containers log to stdout/stderr (no file logging in containers)
- Structured logging with consistent JSON format

**Volume & Mount Consistency**:
- Named volumes for persistent data (not bind mounts in production)
- Read-only mounts when possible (`ro` flag)
- Mount paths consistent across all environments
- Database volumes: `/var/lib/postgresql/data`, `/var/lib/mysql/data`
- Cache volumes: `/var/lib/redis`, `/data` for Qdrant
- No mounting host `/tmp` or `/var/tmp` (use container temp)
- Document all volume purposes in docker-compose comments

**Environment Variable Consistency**:
- All env vars defined in `.env.example` template
- Dev env vars in `.env.dev` (gitignored)
- Production env vars in GCP Secret Manager (never in `.env`)
- Use UPPER_SNAKE_CASE for all env var names
- Document each var with type and purpose in comments
- Validate all env vars on container startup
- Fail fast if required env vars missing

**Docker Compose Standards**:
- Version: `3.9` or higher
- Use `services`, `networks`, `volumes` top-level keys
- Indent consistently (2 spaces, no tabs)
- Services organized: api → databases → caches → monitoring
- All internal services on single `bridge` network
- Explicit service dependencies with `depends_on`
- Override files: `docker-compose.override.yml` for local dev (gitignored)
- Production file: `docker-compose.prod.yml` (committed, no secrets)

### MANDATE: Development Endpoints

**Local Development MUST use Real IP/DNS (Never localhost/127.0.0.1)**:

```bash
# Get your real local IP
REAL_IP=$(hostname -I | awk '{print $1}')  # Linux
REAL_IP=$(ipconfig getifaddr en0)          # macOS

# Or use DNS name (if configured)
DNS_NAME="dev-ollama.internal"            # Your internal DNS

# Use in development .env
API_HOST=$REAL_IP                          # ✅ CORRECT
API_HOST=$DNS_NAME                         # ✅ CORRECT
# API_HOST=127.0.0.1                       # ❌ WRONG
# API_HOST=localhost                       # ❌ WRONG

# Configure services to bind to real IP
FASTAPI_HOST=0.0.0.0                       # Listen on all interfaces
FASTAPI_PORT=8000                          # Specific port
PUBLIC_API_URL=http://$REAL_IP:8000       # ✅ Use real IP in URLs
```

**Why Real IP Mandate**:
1. **Feature Parity**: Development matches production networking behavior
2. **Service Discovery**: Validates DNS resolution and multi-host communication
3. **Network Testing**: Catches network-specific bugs before production
4. **Cross-Machine Access**: Enables team collaboration on local deployments
5. **Load Balancer Testing**: Simulates public endpoint routing

**Development Environment File** (`.env.dev`):
```bash
# Required for all local development
ENVIRONMENT=development
DEBUG=true
LOG_LEVEL=debug

# ✅ MUST use real IP or DNS
REAL_IP=$(hostname -I | awk '{print $1}')
FASTAPI_HOST=0.0.0.0
FASTAPI_PORT=8000
PUBLIC_API_URL=http://$REAL_IP:8000
API_KEY=dev-key-for-testing-only

# Internal service discovery (Docker network)
DATABASE_URL=postgresql://postgres:password@postgres:5432/ollama
REDIS_URL=redis://redis:6379/0
QDRANT_URL=http://qdrant:6333
OLLAMA_BASE_URL=http://ollama:11434

# ❌ FORBIDDEN: Never use these
# FASTAPI_HOST=127.0.0.1
# FASTAPI_HOST=localhost
# DATABASE_URL=postgresql://localhost/ollama
# REDIS_URL=redis://localhost:6379/0
```

## Deployment Practices

### Local Development
```bash
# 1. Set real IP/DNS in environment
export REAL_IP=$(hostname -I | awk '{print $1}')
# or
export REAL_IP="dev-ollama.internal"  # If using DNS

# 2. Create development environment
cp .env.example .env.dev
sed -i "s|PUBLIC_API_URL=.*|PUBLIC_API_URL=http://$REAL_IP:8000|" .env.dev

# 3. Start all services with Docker (using real IP)
docker-compose up -d

# 4. Run migrations
alembic upgrade head

# 5. Start dev server with real IP
# ✅ CORRECT: Bind to all interfaces, access via real IP
uvicorn ollama.main:app --reload --host 0.0.0.0 --port 8000

# 6. Access through REAL IP (not localhost)
# ✅ CORRECT endpoints (using real IP)
curl http://$REAL_IP:8000/api/v1/health
curl http://dev-ollama.internal:8000/api/v1/health  # If using DNS

# ❌ WRONG endpoints (never use these)
# curl http://localhost:8000/api/v1/health
# curl http://127.0.0.1:8000/api/v1/health

# Production: https://elevatediq.ai/ollama (through GCP LB)
```

### Production Deployment
```bash
# Build production image
docker build -t ollama:latest -f docker/Dockerfile .

# Run production stack
# ✅ All defaults use GCP LB endpoint
docker-compose -f docker-compose.prod.yml up -d

# Verify health check goes through GCP LB
# ✅ CORRECT: Through public endpoint
curl -H "Authorization: Bearer <api-key>" \
     https://elevatediq.ai/ollama/api/v1/health

# ❌ WRONG: Direct access to internal service
# curl http://<server-ip>:8000/health  # FORBIDDEN

# Verify firewall blocks internal ports
# ❌ These MUST fail:
curl http://<server-ip>:8000/health     # Should timeout
curl http://<server-ip>:5432            # Should fail
curl http://<server-ip>:6379            # Should fail
curl http://<server-ip>:11434           # Should fail
```

### Deployment Topology (MANDATORY)

**Development Topology** (using real IP):
```
Development Clients
(Real IP: 192.168.1.100 or dns: dev-ollama.internal)
         ↓
    FastAPI Server
    http://192.168.1.100:8000
    http://dev-ollama.internal:8000
         ↓
Docker Container Network (Internal Only)
├── FastAPI (0.0.0.0:8000) ← binds all interfaces
├── PostgreSQL (postgres:5432) ← internal service name
├── Redis (redis:6379) ← internal service name
└── Ollama (ollama:11434) ← internal service name
```

**Production Topology** (GCP Load Balancer):
```
External Clients (Internet)
         ↓
    GCP Load Balancer
    https://elevatediq.ai/ollama
         ↓
    Mutual TLS 1.3+
         ↓
Docker Container Network (Internal Only)
├── FastAPI (0.0.0.0:8000) ← binds all interfaces
├── PostgreSQL (postgres:5432) ← internal service name
├── Redis (redis:6379) ← internal service name
└── Ollama (ollama:11434) ← internal service name
```

**Key Points:**
- ✅ Development uses real IP or DNS (never localhost)
- ✅ All services bind to 0.0.0.0 (listen on all interfaces)
- ✅ Services referenced by Docker service names internally
- ✅ GCP Load Balancer = ONLY external entry point (production)
- ✅ All client traffic routed through GCP LB (production)
- ❌ Never use localhost in development
- ❌ Never use 127.0.0.1 in development
- ❌ Never expose internal service ports directly
- ❌ Never bypass GCP LB for client requests (production)

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
- [ ] **GCP LB configured as sole entry point**
- [ ] **Firewall blocks all internal service ports**
- [ ] **Default endpoint set to https://elevatediq.ai/ollama**
- [ ] **No direct client access to services verified**
- [ ] **Docker Compose uses internal ports only**

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

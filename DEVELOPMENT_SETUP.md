# Development Setup Guide

This guide walks you through setting up your development environment for contributing to Ollama.

## Prerequisites

- **Python**: 3.11 or 3.12
- **Git**: With GPG signing capability
- **Docker & Docker Compose**: For local development stack
- **VS Code**: Recommended editor with extensions

## Initial Setup

### 1. Clone Repository

```bash
git clone https://github.com/kushin77/ollama.git
cd ollama
```

### 2. Configure Git

Ensure you have GPG signing configured (required for all commits):

```bash
# Generate GPG key if you don't have one
gpg --full-generate-key

# Configure git to sign commits
git config user.signingkey YOUR_GPG_KEY_ID
git config commit.gpgsign true

# Verify configuration
git config --list | grep sign
# Output should show: commit.gpgsign=true
```

### 3. Create Python Virtual Environment

```bash
# Create virtual environment
python3.11 -m venv venv

# Activate it
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Upgrade pip
pip install --upgrade pip setuptools wheel

# Install dependencies
pip install -e ".[dev]"  # If using pyproject.toml with [dev] extras
# OR
pip install -r requirements.txt
pip install -r requirements/dev.txt  # If split requirements
```

### 4. Configure Environment

```bash
# Create .env from template
cp .env.example .env

# Fill in actual values
nano .env
# OR
code .env
```

**Key variables to configure**:
```env
DATABASE_URL=postgresql://ollama:password@localhost:5432/ollama
REDIS_URL=redis://localhost:6379/0
JWT_SECRET=$(python -c "import secrets; print(secrets.token_urlsafe(32))")
```

### 5. Start Development Stack

```bash
# Start Docker services (PostgreSQL, Redis, Qdrant, Ollama)
docker-compose up -d

# Initialize database
alembic upgrade head

# Start development server (in separate terminal)
source venv/bin/activate
uvicorn ollama.main:app --reload --host 0.0.0.0 --port 8000
```

Server will be available at: `http://localhost:8000`

## VS Code Setup

### 1. Install Recommended Extensions

When you open the workspace in VS Code, you'll see a notification to install recommended extensions. Click "Install All" or:

```bash
# Install from command line
code --install-extension ms-python.python
code --install-extension ms-python.vscode-pylance
code --install-extension charliermarsh.ruff
code --install-extension github.copilot
code --install-extension ms-azuretools.vscode-docker
code --install-extension eamodio.gitlens
```

### 2. Verify Python Interpreter

1. Open Command Palette: `Ctrl+Shift+P`
2. Search: "Python: Select Interpreter"
3. Choose: `./venv/bin/python`
4. VS Code will auto-configure settings based on `.vscode/settings.json`

### 3. Configure Git in VS Code

Git is already configured, but verify:
1. Open Settings: `Ctrl+,`
2. Search: `"git.enableCommitSigning"`
3. Should be enabled (✓)

## Running Tests

### Run All Tests

```bash
# From activated venv
pytest tests/ -v --cov=ollama --cov-report=html

# OR use VS Code task
Ctrl+Shift+P → "Tasks: Run Test Task"
```

### Run Specific Tests

```bash
# Run single test file
pytest tests/unit/test_auth.py -v

# Run single test
pytest tests/unit/test_auth.py::test_generate_api_key -v

# Run with coverage
pytest tests/ --cov=ollama --cov-report=term-missing
```

### View Coverage Report

```bash
# Generate and open HTML report
pytest tests/ --cov=ollama --cov-report=html
open htmlcov/index.html  # On macOS
# OR
xdg-open htmlcov/index.html  # On Linux
```

## Code Quality Checks

### Type Checking

```bash
# Run mypy in strict mode
mypy ollama/ --strict

# OR use VS Code task
Ctrl+Shift+P → "Tasks: Run Type Checking"
```

### Linting

```bash
# Run ruff
ruff check ollama/

# With automatic fixes
ruff check ollama/ --fix

# OR use VS Code task
Ctrl+Shift+P → "Tasks: Run Linting"
```

### Code Formatting

```bash
# Format code with black
black ollama/ tests/ --line-length=100

# OR use VS Code task
Ctrl+Shift+P → "Tasks: Format Code"
```

### Security Audit

```bash
# Check for vulnerable dependencies
pip-audit

# OR use VS Code task
Ctrl+Shift+P → "Tasks: Security Audit"
```

### Run All Checks

```bash
# One command to run all checks
Ctrl+Shift+P → "Tasks: Run All Checks"

# OR manually:
mypy ollama/ --strict && \
ruff check ollama/ && \
black ollama/ tests/ --check && \
pip-audit && \
pytest tests/ -v --cov=ollama
```

## Development Workflow

### 1. Create Feature Branch

```bash
# Create and switch to branch
git checkout -b feature/your-feature-name

# Branch naming convention:
# - feature/: New features
# - bugfix/: Bug fixes
# - refactor/: Code refactoring
# - perf/: Performance improvements
# - docs/: Documentation updates
# - test/: Test additions/improvements
```

### 2. Make Changes

- Write code with proper type hints
- Include docstrings (Google-style)
- Write tests for new functionality
- Keep functions focused and small

### 3. Run Checks Before Committing

```bash
# Format code
black ollama/ tests/

# Check linting
ruff check ollama/ --fix

# Run tests
pytest tests/ -v --cov=ollama

# Type check
mypy ollama/ --strict

# Security audit
pip-audit
```

### 4. Commit Changes

```bash
# Stage files
git add .

# Commit with conventional format
# (Uses .gitmessage template automatically)
git commit

# VS Code will prompt for message, or use:
# feat(scope): short description
#
# Longer explanation of changes
#
# Fixes #123
```

**Commit Types**:
- `feat`: New feature
- `fix`: Bug fix
- `refactor`: Code refactoring
- `perf`: Performance improvement
- `test`: Test additions/modifications
- `docs`: Documentation changes
- `infra`: Infrastructure/CI-CD changes
- `security`: Security-related changes
- `chore`: Maintenance tasks

### 5. Push and Create Pull Request

```bash
# Push to origin
git push origin feature/your-feature-name

# Create PR on GitHub
# - Use clear title and description
# - Link related issues
# - Ensure all checks pass
```

## Database Migrations

### Create New Migration

```bash
# Create migration with description
alembic revision -m "description of changes"

# Edit autogenerated migration in alembic/versions/
# Write up() and down() functions

# Test migration locally
alembic upgrade head  # Apply
alembic downgrade -1  # Rollback
alembic upgrade head  # Reapply
```

### Apply Migrations

```bash
# Apply all pending migrations
alembic upgrade head

# Apply specific migration
alembic upgrade abc123def456

# Rollback to previous
alembic downgrade -1

# View migration history
alembic history
```

## Common Tasks

### Add New Dependency

```bash
# Add to pyproject.toml or requirements.txt
pip install package_name

# Verify no security issues
pip-audit

# Update lock file (if using poetry)
poetry lock
```

### Run Specific Test Suite

```bash
# Unit tests only
pytest tests/unit/ -v

# Integration tests only
pytest tests/integration/ -v

# With coverage
pytest tests/ --cov=ollama --cov-report=html
```

### Debug Code

#### Using VS Code Debugger

1. Open file to debug
2. Set breakpoint: Click left of line number
3. Run: `Ctrl+Shift+D` → Select "Python: FastAPI" → Click play
4. Access app at `http://localhost:8000`
5. Step through code, inspect variables

#### Using Python REPL

```bash
# Open Python REPL
python

# Import and test
from ollama.services.cache import CacheManager
cache = CacheManager()
# ...

# Exit
exit()
```

### Check API Documentation

```bash
# With server running (http://localhost:8000)
# Visit these endpoints:

# OpenAPI/Swagger UI
http://localhost:8000/docs

# ReDoc documentation
http://localhost:8000/redoc

# OpenAPI JSON schema
http://localhost:8000/openapi.json
```

### Monitor Services

```bash
# Check running containers
docker ps

# View logs
docker logs container_name
docker logs -f container_name  # Follow logs

# Stop services
docker-compose down

# Stop and remove volumes
docker-compose down -v
```

## Troubleshooting

### Poetry/Pip Lock Issues

```bash
# Clear pip cache
pip cache purge

# Reinstall dependencies
pip install --force-reinstall -r requirements.txt
```

### Database Connection Issues

```bash
# Check PostgreSQL is running
docker ps | grep postgres

# Reset database
docker-compose down -v
docker-compose up -d

# Rerun migrations
alembic upgrade head
```

### Type Checking Issues

```bash
# Clear mypy cache
rm -rf .mypy_cache

# Clear ruff cache
rm -rf .ruff_cache

# Rerun checks
mypy ollama/ --strict
ruff check ollama/
```

### Test Failures

```bash
# Run with verbose output
pytest tests/ -vv

# Run with print statements visible
pytest tests/ -s

# Run specific test
pytest tests/unit/test_file.py::test_function -vv
```

## Tools & Extensions Reference

| Tool | Purpose | Command |
|------|---------|---------|
| pytest | Testing | `pytest tests/` |
| mypy | Type checking | `mypy ollama/ --strict` |
| ruff | Linting | `ruff check ollama/` |
| black | Code formatting | `black ollama/` |
| pip-audit | Security scanning | `pip-audit` |
| alembic | Database migrations | `alembic upgrade head` |
| uvicorn | Dev server | `uvicorn ollama.main:app --reload` |
| docker-compose | Local stack | `docker-compose up -d` |

## Additional Resources

- [Architecture](docs/architecture.md) - System design
- [Contributing](CONTRIBUTING.md) - Contribution guidelines
- [Copilot Instructions](..copilot-instructions) - Development standards
- [Compliance Report](COPILOT_COMPLIANCE_REPORT.md) - Standards compliance

## Getting Help

- **GitHub Issues**: Create issue for bugs or feature requests
- **Discussions**: Start discussion for questions
- **Code Review**: Review PRs and provide feedback
- **Documentation**: Update docs if standards unclear

---

**Last Updated**: January 13, 2026
**Maintained By**: kushin77
**Status**: ✅ Production-Ready

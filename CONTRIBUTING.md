# Contributing to Ollama

Thank you for your interest in contributing to Ollama! This document provides guidelines and instructions for contributing to the project.

**Production Status**: ✅ Live at [https://elevatediq.ai/ollama](https://elevatediq.ai/ollama)
**Performance**: 50-user load test verified (7,162 requests, 75ms P95, 100% success)
**Infrastructure**: [GCP Landing Zone](https://github.com/kushin77/GCP-landing-zone)

## Code of Conduct

We are committed to providing a welcoming and inspiring community for all. Please read and adhere to our Code of Conduct.

## Getting Started

### Prerequisites

- Python 3.11+
- Docker & Docker Compose
- Git (with signed commits enabled)
- Real IP/DNS (NOT localhost for development)

### Setup Development Environment

```bash
git clone https://github.com/kushin77/ollama.git
cd ollama
bash scripts/bootstrap.sh

# IMPORTANT: Development must use real IP, not localhost
export REAL_IP=$(hostname -I | awk '{print $1}')
sed -i "s|PUBLIC_API_URL=.*|PUBLIC_API_URL=http://$REAL_IP:8000|" .env.dev

source venv/bin/activate
```

## Development Workflow

### 1. Create a Feature Branch

```bash
git checkout -b feature/your-feature-name
```

Branch naming convention:

- `feature/`: New features
- `bugfix/`: Bug fixes
- `refactor/`: Code refactoring
- `infra/`: Infrastructure changes
- `docs/`: Documentation updates
- `security/`: Security-related changes

### 2. Make Changes

- Follow the elite development standards in `.github/copilot-instructions.md`
- Write code with type hints (100% coverage required)
- Include comprehensive docstrings
- Write tests for new functionality (≥90% coverage)
- Use real IP/DNS in development (never localhost)

### 3. Commit Changes

```bash
# Stage changes
git add .

# Create atomic, signed commits
git commit -S -m "type(scope): description"

# Examples:
# feat(inference): add flash attention optimization
# fix(api): handle concurrent request race condition
# test(models): add quantization validation tests
```

### 3.1 Pre-commit Hooks (Automatic)

Pre-commit hooks run automatically before each commit:

```bash
# First time setup
pip install pre-commit
pre-commit install

# Hooks will now run automatically on:
# - Code formatting (Black)
# - Linting (Ruff)
# - Type checking (mypy)
# - Security scanning (Bandit)
# - Import sorting (isort)
# - Trailing whitespace removal
# - File ending fixes
# - Commit message validation
```

If any check fails, fix it and try committing again.

### 4. Run Quality Checks Manually

```bash
# Format code
black ollama/ tests/
isort ollama/ tests/

# Lint
ruff check ollama/ tests/ --fix

# Type checking
mypy ollama/ --strict

# Tests
pytest tests/ -v --cov=ollama --cov-report=term-missing

# Security scan
bandit -r ollama/ -ll
pip-audit

# Run all at once
pytest tests/ -v --cov=ollama && \
  mypy ollama/ --strict && \
  ruff check ollama/ && \
  black ollama/ tests/ --check && \
  pip-audit
```

### 5. Push and Create Pull Request

```bash
git push origin feature/your-feature-name
```

Then create a PR on GitHub with:

- Clear title describing the change
- Detailed description of what and why
- Reference to related issues
- Screenshots/benchmarks if applicable

**CI/CD Pipeline** will automatically:

- ✅ Run all tests on Python 3.11 and 3.12
- ✅ Check type safety with mypy
- ✅ Lint with Ruff
- ✅ Scan dependencies for vulnerabilities
- ✅ Run security checks (Bandit, CodeQL)
- ✅ Verify code formatting

All checks must pass before merging.

## Code Style & Standards

### Python

- **Format**: Black (line length: 100)
- **Import sorting**: isort
- **Linting**: Ruff
- **Type checking**: mypy (strict mode)
- **Documentation**: Google-style docstrings

Example:

```python
def generate_text(
    model: str,
    prompt: str,
    max_tokens: int = 512,
    temperature: float = 0.7,
) -> str:
    """
    Generate text using specified model.

    Args:
        model: Model identifier (e.g., 'llama2')
        prompt: Input prompt for generation
        max_tokens: Maximum tokens to generate (default: 512)
        temperature: Sampling temperature 0-2 (default: 0.7)

    Returns:
        Generated text string

    Raises:
        ValueError: If model not found or invalid parameters
        RuntimeError: If inference fails

    Example:
        >>> response = generate_text("llama2", "Explain quantum computing")
        >>> print(response)
    """
    # Implementation with type hints
```

### Testing

- **Minimum coverage**: 90% for critical paths
- **Location**: Co-located with source (`test_*.py` files)
- **Framework**: pytest
- **Async tests**: Use `pytest-asyncio`

```python
import pytest
from ollama.inference import generate_text

@pytest.mark.asyncio
async def test_generate_text_basic():
    """Test basic text generation."""
    result = await generate_text(
        model="test-model",
        prompt="Hello",
    )
    assert isinstance(result, str)
    assert len(result) > 0

@pytest.fixture
def sample_model():
    """Fixture providing test model."""
    return MockModel()
```

## Commit Message Format

```
type(scope): subject

body

footer
```

### Types

- `feat`: New feature
- `fix`: Bug fix
- `refactor`: Code refactoring
- `perf`: Performance improvement
- `test`: Test additions/changes
- `docs`: Documentation
- `infra`: Infrastructure/build changes
- `chore`: Maintenance tasks

### Examples

```
feat(inference): implement flash attention v2

Optimize attention computation using FA v2 kernels.
Reduces memory usage by 40% and improves speed by 60%.

Closes #123
Benchmarks: Added in tests/perf/test_attention.py
```

## Pull Request Process

1. **Fill PR template**: Describe what, why, and how
2. **Pass all checks**: CI/CD must be green
3. **Code review**: At least one approval required
4. **Squash commits**: Clean history before merge
5. **Delete branch**: After merge

## Testing Checklist

Before submitting a PR:

- [ ] Tests pass: `pytest tests/ -v`
- [ ] Coverage maintained: `pytest --cov=ollama`
- [ ] Type checks pass: `mypy ollama/ --strict`
- [ ] Code formatted: `black ollama/ tests/`
- [ ] No security issues: `bandit -r ollama/`
- [ ] Documentation updated
- [ ] Commit messages follow convention
- [ ] No hardcoded credentials or sensitive data

## Performance Contribution

For performance-related changes:

```bash
# Benchmark before
python scripts/benchmark.py > before.txt

# Make changes

# Benchmark after
python scripts/benchmark.py > after.txt

# Compare
diff before.txt after.txt
```

Include benchmarks in PR description showing improvements.

## Documentation

- **Code docstrings**: Google style with type hints
- **README**: Update for user-facing changes
- **Architecture**: Update `docs/architecture.md` for structural changes
- **API**: Update `docs/api.md` for endpoint changes

## Reporting Issues

### Bug Report Template

```markdown
**Description**
Clear description of the bug

**Steps to Reproduce**

1. Step one
2. Step two

**Expected Behavior**
What should happen

**Actual Behavior**
What actually happens

**Environment**

- OS: Ubuntu 22.04
- Python: 3.11.2
- Ollama version: 1.0.0

**Logs**
```

Error log output

```

```

### Feature Request Template

```markdown
**Description**
Clear description of desired feature

**Motivation**
Why is this needed?

**Proposed Solution**
How should it work?

**Alternatives**
Other approaches considered

**Additional Context**
Any other relevant info
```

## Review Process

### For Reviewers

1. Check that code follows standards
2. Verify tests are comprehensive
3. Ensure no performance regression
4. Look for security issues
5. Check documentation is clear
6. Approve or request changes

### For Contributors

- Respond promptly to feedback
- Request clarification if needed
- Make updates in new commits (for review clarity)
- Squash before merging

## Community

- **Discussions**: Use GitHub Discussions for questions
- **Issues**: Use GitHub Issues for bugs/features
- **Code of Conduct**: Be respectful and professional

## License

By contributing to Ollama, you agree that your contributions will be licensed under the MIT License.

---

**Questions?** Open a discussion or contact maintainers.

Thank you for contributing! 🎉

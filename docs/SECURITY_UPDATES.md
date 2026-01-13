# Security Update Requirements

## Critical Updates (Immediate)

Apply these updates immediately to address high-severity vulnerabilities:

```bash
# Upgrade critical security packages
pip install --upgrade \
    cryptography>=43.0.1 \
    fastapi>=0.109.1 \
    starlette>=0.47.2
```

## Recommended Updates (This Week)

Update these packages to address medium-severity vulnerabilities:

```bash
# Upgrade recommended packages
pip install --upgrade \
    transformers>=4.53.0 \
    python-jose>=3.4.0 \
    requests>=2.32.4 \
    python-multipart>=0.0.18 \
    protobuf>=6.31.1 \
    ecdsa>=0.19.2
```

## Verification

After updating, verify all tests still pass:

```bash
# Run full test suite
pytest tests/ -v

# Run linting
ruff check ollama/

# Run security audit again
pip-audit

# Freeze updated dependencies
pip freeze > requirements-updated.txt
```

## Breaking Changes to Watch

### Starlette 0.27.0 → 0.47.2
- May affect middleware signatures
- Review rate limiting and caching middleware

### FastAPI 0.104.1 → 0.109.1
- Minor API changes in dependency injection
- Check custom dependencies in routes

### Transformers 4.35.2 → 4.53.0
- Model loading may have different API
- Verify embedding generation still works
- Test any custom model adapters

## Rollback Plan

If updates cause issues:

```bash
# Rollback to current versions
pip install \
    cryptography==41.0.5 \
    fastapi==0.104.1 \
    starlette==0.27.0
```

## Notes

- All packages are backwards compatible within minor versions
- No breaking changes expected in patch updates
- Test thoroughly in staging before production deployment
- Monitor application logs after deployment for any runtime errors

---

**Generated**: January 13, 2026  
**Source**: pip-audit security scan  
**Priority**: HIGH - Address within 48 hours

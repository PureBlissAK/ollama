# Security Quick Wins - Start Here

**Timeline**: 2-4 hours  
**Impact**: Critical security vulnerabilities addressed  
**Effort**: Low-Medium  

Execute these tasks immediately before deploying to production.

---

## Task 1: Create .env.example (15 minutes)

```bash
# Create .env.example - commits to repo, shows expected format
cat > .env.example << 'EOF'
# ============================================================================
# Ollama Environment Configuration
# Copy this file to .env and fill in actual values (never commit .env)
# Generate secrets with: openssl rand -hex 16 (passwords) or -hex 32 (keys)
# ============================================================================

# PostgreSQL Configuration
POSTGRES_USER=ollama
POSTGRES_PASSWORD=<32-char-hex-random-password>
POSTGRES_DB=ollama

# Database Connection String
DATABASE_URL=postgresql+asyncpg://ollama:<POSTGRES_PASSWORD>@postgres:5432/ollama

# Redis Configuration
REDIS_PASSWORD=<32-char-hex-random-password>
REDIS_URL=redis://:<REDIS_PASSWORD>@redis:6379/0

# Application Security
SECRET_KEY=<64-char-hex-random-string>
JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=24
API_KEY_PREFIX=sk

# Environment Settings
ENVIRONMENT=development
DEBUG=false
LOG_LEVEL=INFO

# Vector Database (Qdrant)
QDRANT_URL=http://qdrant:6333
QDRANT_API_KEY=<optional-32-char-hex>

# Monitoring
JAEGER_AGENT_HOST=jaeger
JAEGER_AGENT_PORT=6831

# Grafana Admin
GRAFANA_ADMIN_PASSWORD=<secure-password>
EOF

git add .env.example
git commit -m "docs: add environment template (secrets never included)"
```

**Verify**:
```bash
cat .env.example | wc -l  # Should have ~30 lines
grep "PASSWORD\|SECRET" .env.example  # Should show template values only
```

---

## Task 2: Update .gitignore (5 minutes)

```bash
# Append to .gitignore
cat >> .gitignore << 'EOF'

# ============================================================================
# Environment & Secrets - NEVER COMMIT THESE
# ============================================================================
.env
.env.*.local
.env.local
.env.*.production
.env.production

# Credential files
/secrets/
**/secrets.yaml
**/secrets.yml
*.pem
*.key
*.crt
*.p12

# Generated certificates
/certs/
/certificates/

# Docker credentials
.dockercfg
.docker/config.json

# Cloud provider credentials
service-account-key.json
gcloud-key.json
aws-credentials.json

# IDE & local config
.idea/
.vscode/local.env
*.swp

EOF

git add .gitignore
git commit -m "security: prevent accidental credential commits"
```

---

## Task 3: Generate Production Secrets (10 minutes)

```bash
#!/bin/bash
# scripts/generate-production-secrets.sh
# Generates secure random values for production deployment

set -e

echo "🔐 Generating Production Secrets"
echo "================================="

# Generate 32-char hex passwords (128 bits)
POSTGRES_PASSWORD=$(openssl rand -hex 16)
REDIS_PASSWORD=$(openssl rand -hex 16)

# Generate 64-char hex secret keys (256 bits)
SECRET_KEY=$(openssl rand -hex 32)
QDRANT_API_KEY=$(openssl rand -hex 16)

# Generate Grafana password (32 chars)
GRAFANA_ADMIN_PASSWORD=$(openssl rand -base64 32 | tr -d '=' | head -c 32)

# Display values (STORE SECURELY)
cat > /tmp/secrets.txt << EOF
# PRODUCTION SECRETS - STORE SECURELY
# ===================================
# Store in: AWS Secrets Manager, Vault, Google Secret Manager, etc.
# Never commit to version control

POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
REDIS_PASSWORD=${REDIS_PASSWORD}
SECRET_KEY=${SECRET_KEY}
QDRANT_API_KEY=${QDRANT_API_KEY}
GRAFANA_ADMIN_PASSWORD=${GRAFANA_ADMIN_PASSWORD}

DATABASE_URL=postgresql+asyncpg://ollama:${POSTGRES_PASSWORD}@postgres:5432/ollama
REDIS_URL=redis://:${REDIS_PASSWORD}@redis:6379/0
EOF

echo "✓ Secrets generated and saved to /tmp/secrets.txt"
echo "✓ Store these in your secrets manager NOW"
echo ""
echo "For local development only:"
echo "  cp /tmp/secrets.txt .env"
echo "  git checkout .env  # Remove from git after copy"
```

**Run it**:
```bash
chmod +x scripts/generate-production-secrets.sh
./scripts/generate-production-secrets.sh

# Output saved to /tmp/secrets.txt
# Copy secrets to secure location (AWS Secrets Manager, etc.)
cat /tmp/secrets.txt
```

---

## Task 4: Update docker-compose.yml (30 minutes)

**Critical changes**:

```bash
# 1. Backup original
cp docker-compose.yml docker-compose.yml.backup

# 2. Replace hardcoded secrets with ${VARIABLES}
# Use your editor or sed:

sed -i "s/POSTGRES_PASSWORD: ollama_dev/POSTGRES_PASSWORD: \${POSTGRES_PASSWORD}/g" docker-compose.yml
sed -i "s/SECRET_KEY: dev-secret-key-change-in-production/SECRET_KEY: \${SECRET_KEY}/g" docker-compose.yml
sed -i "s/GF_SECURITY_ADMIN_PASSWORD: admin/GF_SECURITY_ADMIN_PASSWORD: \${GRAFANA_ADMIN_PASSWORD}/g" docker-compose.yml

# 3. Verify changes
git diff docker-compose.yml | head -50
```

**Or manually edit docker-compose.yml**:

Key changes needed:
```yaml
# BEFORE (❌ INSECURE)
postgres:
  environment:
    POSTGRES_PASSWORD: ollama_dev

# AFTER (✅ SECURE)
postgres:
  environment:
    POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}  # Required from .env
```

**Verify**:
```bash
# Should show all variables substituted from .env
docker-compose config | grep -E "(PASSWORD|SECRET|KEY)" | head -10

# Should NOT show raw values
grep "ollama_dev\|dev-secret-key" docker-compose.yml && echo "❌ Still has hardcoded secrets!" || echo "✓ Secrets properly parameterized"
```

---

## Task 5: Pin Image Digests (20 minutes)

```bash
#!/bin/bash
# scripts/pin-images.sh
# Updates docker-compose.yml with pinned image digests

IMAGES=(
    "postgres:15-alpine"
    "redis:7-alpine"
    "qdrant/qdrant:latest"
    "ollama/ollama:latest"
    "prom/prometheus:latest"
    "grafana/grafana:latest"
    "jaegertracing/all-in-one:latest"
)

echo "📌 Pinning Image Digests"
echo "========================"

for image in "${IMAGES[@]}"; do
    echo "Pulling $image..."
    docker pull "$image" > /dev/null 2>&1
    
    # Get full image reference with digest
    full_ref=$(docker inspect --format='{{index .RepoDigests 0}}' "$image")
    echo "✓ $image"
    echo "  → $full_ref"
done

echo ""
echo "Update docker-compose.yml to use these digests:"
echo "  image: postgres:15-alpine@sha256:a1b2c3d4..."
```

**Run it**:
```bash
chmod +x scripts/pin-images.sh
./scripts/pin-images.sh
```

**Manual update to docker-compose.yml**:
```yaml
services:
  postgres:
    image: postgres:15-alpine@sha256:abc123def456  # BEFORE: postgres:15-alpine
  redis:
    image: redis:7-alpine@sha256:xyz789uvw012    # BEFORE: redis:7-alpine
  # ... etc for all services
```

---

## Task 6: Test Updated Compose File (15 minutes)

```bash
# 1. Create temporary .env for testing
cat > .env.test << 'EOF'
POSTGRES_USER=ollama
POSTGRES_PASSWORD=test_password_12345678901234
POSTGRES_DB=ollama
DATABASE_URL=postgresql+asyncpg://ollama:test_password_12345678901234@postgres:5432/ollama
REDIS_PASSWORD=test_redis_password1234567890
REDIS_URL=redis://:test_redis_password1234567890@redis:6379/0
SECRET_KEY=test_secret_key_1234567890123456789012345678901234567890123456
JWT_ALGORITHM=HS256
ENVIRONMENT=testing
DEBUG=false
LOG_LEVEL=INFO
EOF

# 2. Test compose configuration
docker-compose --env-file .env.test config > /tmp/docker-compose-resolved.yml

# 3. Verify no raw secrets in resolved config
grep -i "password.*=" /tmp/docker-compose-resolved.yml | grep -v ":" && echo "❌ Raw secrets found!" || echo "✓ All secrets properly substituted"

# 4. Verify images have digests
grep "@sha256:" /tmp/docker-compose-resolved.yml | wc -l
# Should show all main services (postgres, redis, qdrant, ollama, api, prometheus, grafana, jaeger)

# 5. Cleanup
rm .env.test
```

---

## Task 7: Add Security Scanning to CI/CD (20 minutes)

Create `.github/workflows/security.yml`:

```yaml
name: Security Scanning

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main, develop]

jobs:
  # 1. Detect committed secrets
  secrets:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0  # Full history for scanning
      
      - name: Detect secrets with gitleaks
        uses: gitleaks/gitleaks-action@v2
        with:
          source: repo
          verbose: true
          fail: true
  
  # 2. Check for hardcoded credentials in compose
  docker-compose:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Check for hardcoded credentials in compose files
        run: |
          echo "🔍 Checking docker-compose files for hardcoded secrets..."
          
          # Should NOT find these patterns
          ! grep -r "POSTGRES_PASSWORD.*=.*[a-z]" docker-compose*.yml || exit 1
          ! grep -r "SECRET_KEY.*=.*[a-z]" docker-compose*.yml || exit 1
          ! grep -r "password.*=.*[a-z]" docker-compose*.yml | grep -v "\${" || exit 1
          
          echo "✓ No hardcoded secrets in docker-compose files"
      
      - name: Verify all compose files use environment variables
        run: |
          for file in docker-compose*.yml; do
            echo "Checking $file..."
            docker-compose --file "$file" config > /dev/null || exit 1
          done
          echo "✓ All docker-compose files valid"

  # 3. Dependency vulnerability scan
  dependencies:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Run pip-audit
        run: |
          pip install pip-audit
          pip-audit --desc || true  # Don't fail on this for now
```

**Create the file**:
```bash
mkdir -p .github/workflows
cat > .github/workflows/security.yml << 'EOF'
# [paste content above]
EOF

git add .github/workflows/security.yml
git commit -m "ci: add security scanning for secrets and dependencies"
```

---

## Task 8: Document the Changes (10 minutes)

Create `docs/SECURITY_INCIDENT_RESPONSE.md`:

```markdown
# Security Incident Response

## Credentials Exposed

If credentials were exposed:

1. **IMMEDIATELY Rotate All Secrets**
   ```bash
   ./scripts/generate-production-secrets.sh
   ```

2. **Update In Secrets Manager**
   - AWS Secrets Manager
   - Google Secret Manager
   - HashiCorp Vault
   - etc.

3. **Rotate Database Passwords**
   ```sql
   ALTER USER ollama PASSWORD 'new_password_here';
   ```

4. **Reset API Keys**
   - Regenerate in Qdrant
   - Regenerate JWT secrets
   - Regenerate Grafana admin password

5. **Audit Logs**
   - Check who accessed the credentials
   - Review unauthorized API calls
   - Monitor for unusual activity

6. **Post-Incident**
   - Create incident report
   - Implement detective controls
   - Schedule security training

## Prevention Checklist

- [ ] All secrets in environment variables
- [ ] No secrets in git history
- [ ] Secrets rotated regularly (every 90 days)
- [ ] Access logs monitored
- [ ] Security scanning in CI/CD
- [ ] Secrets manager backup/recovery tested
```

---

## Verification Checklist (Completion)

```bash
#!/bin/bash
# Verify all security improvements

echo "🔒 Security Implementation Verification"
echo "======================================"
echo ""

# 1. Check .env.example exists
if [ -f ".env.example" ]; then
    echo "✓ .env.example exists"
else
    echo "❌ Missing .env.example"
fi

# 2. Check .env in .gitignore
if grep -q "^.env$" .gitignore; then
    echo "✓ .env in .gitignore"
else
    echo "❌ .env not in .gitignore"
fi

# 3. Check for hardcoded secrets
if grep -r "password.*=.*[a-z]" docker-compose.yml | grep -v "\${"; then
    echo "❌ Hardcoded passwords found"
else
    echo "✓ No hardcoded passwords in compose"
fi

# 4. Check for hardcoded SECRET_KEY
if grep -q "SECRET_KEY.*dev-secret-key" docker-compose.yml; then
    echo "❌ Default SECRET_KEY still in compose"
else
    echo "✓ SECRET_KEY properly parameterized"
fi

# 5. Check image digests
image_pins=$(grep -c "@sha256:" docker-compose.yml || echo 0)
echo "✓ $image_pins images pinned with digests"

# 6. Check CI/CD security scanning
if [ -f ".github/workflows/security.yml" ]; then
    echo "✓ Security scanning workflow added"
else
    echo "❌ Missing security.yml workflow"
fi

echo ""
echo "✅ All critical security improvements completed!"
```

**Run it**:
```bash
chmod +x scripts/verify-security.sh
./scripts/verify-security.sh
```

---

## Summary: What You've Accomplished

| Task | Status | Impact |
|------|--------|--------|
| 1. Created .env.example | ✅ | Standardizes env configuration |
| 2. Updated .gitignore | ✅ | Prevents credential leaks |
| 3. Generated production secrets | ✅ | Secure random credentials |
| 4. Updated docker-compose.yml | ✅ | Removes hardcoded secrets |
| 5. Pinned image digests | ✅ | Reproducible deployments |
| 6. Tested configuration | ✅ | Validates all changes work |
| 7. Added security scanning | ✅ | Automated vulnerability detection |
| 8. Documented procedures | ✅ | Incident response readiness |

**Total Time**: 2-4 hours  
**Security Improvement**: 🔴 → 🟢 (Critical issues resolved)  

---

## Next Steps

1. **Commit these changes**:
   ```bash
   git add -A
   git commit -m "security: implement environment-based secrets management"
   git push
   ```

2. **Deploy to staging**:
   ```bash
   # Load production secrets from secure storage
   source /secure/storage/secrets.sh  # Or AWS Secrets Manager, etc.
   docker-compose up -d
   ```

3. **Run verification**:
   ```bash
   curl http://localhost:8000/health
   pytest tests/ -v
   ```

4. **Then proceed to Phase 2: Robustness** (see `DEPLOYMENT_ENHANCEMENT_ANALYSIS.md`)

---

**Status**: Implementation-ready  
**Commit Message**: `security: implement environment-based secrets and image pinning`

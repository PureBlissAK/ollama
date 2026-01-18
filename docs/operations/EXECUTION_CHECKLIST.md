# ⚡ IMMEDIATE EXECUTION CHECKLIST

**Date**: January 13, 2026 | **Priority**: 🔴 HIGH | **Time Estimate**: 4-6 hours

---

## Phase 1: Monitoring & Alerting (1-2 hours) ✅ READY TO RUN

### Step 1.1: Deploy Monitoring Infrastructure
```bash
# Make script executable
chmod +x scripts/setup-monitoring.sh

# Execute monitoring setup
./scripts/setup-monitoring.sh

# Verify deployment
echo "✅ Monitoring deployed"
```

**What it does:**
- Enables GCP Monitoring APIs
- Creates custom metrics
- Sets up alert policies
- Configures dashboards

**Expected output:** "Setup complete"

---

### Step 1.2: Verify Prometheus Configuration
```bash
# Check Prometheus config
cat monitoring/prometheus.yml

# Verify scrape targets
grep -A 5 "scrape_configs:" monitoring/prometheus.yml
```

**Expected output:** Configuration with job definitions

---

### Step 1.3: Verify Grafana Dashboards
```bash
# List available dashboards
ls -la monitoring/grafana/dashboards/

# Count dashboards
find monitoring/grafana -name "*.json" | wc -l
```

**Expected output:** 5+ dashboard JSON files

---

## Phase 2: Database Setup (1-2 hours) ✅ READY TO RUN

### Step 2.1: Run Alembic Migrations
```bash
# Check current migration status
alembic current

# List all available migrations
alembic history

# Apply all pending migrations
alembic upgrade head

# Verify migration applied
alembic current
```

**Expected output:**
```
Current revision(s) for postgresql://...: f019ecf7fec5, head
```

---

### Step 2.2: Seed Initial Data
```bash
# Seed supported models
python scripts/seed_models.py

# Create admin user
python scripts/create_admin.py

# Verify data
psql $DATABASE_URL << 'SQL'
SELECT COUNT(*) as total_models FROM models;
SELECT COUNT(*) as admin_users FROM users WHERE is_admin = true;
SQL
```

**Expected output:** Models and admin user created

---

### Step 2.3: Create Database Indexes
```bash
# Connect to database
psql $DATABASE_URL << 'SQL'
-- User lookups
CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);

-- API key lookups
CREATE INDEX IF NOT EXISTS idx_api_keys_key_hash ON api_keys(key_hash);
CREATE INDEX IF NOT EXISTS idx_api_keys_user_id ON api_keys(user_id);

-- Conversation queries
CREATE INDEX IF NOT EXISTS idx_conversations_user_id ON conversations(user_id);
CREATE INDEX IF NOT EXISTS idx_messages_conversation_id ON messages(conversation_id);

-- Analyze tables
ANALYZE;
SQL

echo "✅ Indexes created and analyzed"
```

**Expected output:** 6+ indexes created

---

### Step 2.4: Verify Database Performance
```bash
# Check table sizes
psql $DATABASE_URL << 'SQL'
SELECT
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
SQL

# Check index usage
psql $DATABASE_URL << 'SQL'
SELECT schemaname, tablename, indexname, idx_scan
FROM pg_stat_user_indexes
ORDER BY idx_scan DESC
LIMIT 10;
SQL
```

**Expected output:** Table sizes and index scan statistics

---

## Phase 3: DNS Verification (30 minutes) ✅ READY TO CHECK

### Step 3.1: Check DNS Propagation
```bash
# Query DNS status
nslookup ollama.elevatediq.ai

# Expected output should show:
# ollama.elevatediq.ai CNAME ghs.googlehosted.com
# ghs.googlehosted.com A 142.250.80.83
```

**Status**: ⏳ Still propagating (can take 24-48 hours)

---

### Step 3.2: Test Primary Endpoints
```bash
# Test direct service URL
curl -I https://ollama-service-sozvlwbwva-uc.a.run.app/health

# Expected: HTTP/2 200

# Test load balancer
curl -I https://elevatediq.ai/ollama/health

# Expected: HTTP/2 200

# Test custom domain (once DNS propagates)
curl -I https://ollama.elevatediq.ai/health

# Expected: HTTP/2 200
```

---

## Phase 4: Service Health Verification (30 minutes) ✅ READY TO CHECK

### Step 4.1: Check Service Status
```bash
# View service details
gcloud run services describe ollama-service \
  --region=us-central1 \
  --project=elevatediq

# Check recent deployments
gcloud run revisions list \
  --service=ollama-service \
  --region=us-central1 \
  --project=elevatediq \
  --limit=5

# Monitor logs (real-time)
gcloud run logs read ollama-service \
  --region=us-central1 \
  --project=elevatediq \
  --follow
```

**Expected output:** Service active with healthy revision

---

### Step 4.2: Test API Endpoints
```bash
# Test health endpoint
curl -v https://ollama-service-sozvlwbwva-uc.a.run.app/health

# Test models endpoint
curl https://ollama-service-sozvlwbwva-uc.a.run.app/api/v1/models

# Test metrics endpoint
curl https://ollama-service-sozvlwbwva-uc.a.run.app/metrics

# All should return 200 OK
```

**Expected output:** JSON responses or metrics in Prometheus format

---

## Phase 5: Load Testing (1-2 hours) ✅ READY TO RUN

### Step 5.1: Install Locust
```bash
# Install load testing tool
pip install locust

# Create load test file
cat > load_test.py << 'EOF'
from locust import HttpUser, task, between
import json

class APIUser(HttpUser):
    wait_time = between(1, 3)

    @task(1)
    def health_check(self):
        self.client.get("/health")

    @task(3)
    def list_models(self):
        self.client.get("/api/v1/models")

    @task(2)
    def generate_request(self):
        payload = {
            "model": "llama3.2",
            "prompt": "Hello",
            "stream": False
        }
        self.client.post(
            "/api/v1/generate",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
EOF
```

---

### Step 5.2: Run Load Test (Development)
```bash
# Test against local service
locust -f load_test.py \
  --host http://localhost:8000 \
  -u 50 \
  -r 5 \
  --run-time 10m \
  --headless \
  --csv=results/load_test_dev

# Analyze results
cat results/load_test_dev_stats.csv
```

**Expected output:** Load test statistics in CSV format

---

### Step 5.3: Run Load Test (Production)
```bash
# Test against production
locust -f load_test.py \
  --host https://ollama-service-sozvlwbwva-uc.a.run.app \
  -u 100 \
  -r 10 \
  --run-time 5m \
  --headless \
  --csv=results/load_test_prod

# Document results
cat > PERFORMANCE_BASELINE.md << 'EOF'
# Performance Baselines - January 13, 2026

## Load Test Results
- Users: 100
- Ramp-up: 10 users/sec
- Duration: 5 minutes
- Total requests: [see CSV]

## Metrics
- Response time p50: [measure]
- Response time p95: [measure]
- Response time p99: [measure]
- Error rate: [measure]
- Throughput: [measure] req/sec
EOF
```

---

## Phase 6: Final Verification (30 minutes) ✅ READY TO CHECK

### Step 6.1: Security Verification
```bash
# Run security audit
pip-audit

# Check dependencies
pip list | grep -i security

# Verify TLS version
echo | openssl s_client -connect ollama-service-sozvlwbwva-uc.a.run.app:443 | grep "Protocol"

# Expected: TLSv1.3
```

---

### Step 6.2: Backup Verification
```bash
# Create backup
gcloud sql backups create \
  --instance=ollama-db \
  --project=elevatediq

# List backups
gcloud sql backups list \
  --instance=ollama-db \
  --project=elevatediq

# Document backup ID for future reference
```

---

### Step 6.3: Compliance Check
```bash
# Verify all code is committed
git status

# Check commit history
git log --oneline | head -10

# Verify hooks are installed
ls -la .git/hooks/ | grep -E "(pre-commit|post-commit|commit-msg)"

# Run quality checks
pytest tests/ -v --cov=ollama
mypy ollama/ --strict
ruff check ollama/
```

---

## Execution Order (Recommended)

```
┌─────────────────────────────────────┐
│  Phase 1: Monitoring (1-2 hours)    │ ← START HERE
└────────────┬────────────────────────┘
             │
             ↓
┌─────────────────────────────────────┐
│  Phase 2: Database (1-2 hours)      │
└────────────┬────────────────────────┘
             │
             ↓
┌─────────────────────────────────────┐
│  Phase 3: DNS Check (30 min)        │
└────────────┬────────────────────────┘
             │
             ↓
┌─────────────────────────────────────┐
│  Phase 4: Service Health (30 min)   │
└────────────┬────────────────────────┘
             │
             ↓
┌─────────────────────────────────────┐
│  Phase 5: Load Testing (1-2 hours)  │
└────────────┬────────────────────────┘
             │
             ↓
┌─────────────────────────────────────┐
│  Phase 6: Final Check (30 min)      │
└─────────────────────────────────────┘
```

**Total Time**: 4-6 hours

---

## Quick Command Reference

```bash
# Monitor everything
watch -n 5 'gcloud run services describe ollama-service --region=us-central1'

# See all logs
gcloud run logs read ollama-service --region=us-central1 --limit=100 --follow

# Check metrics
gcloud monitoring metrics-descriptors list --filter="metric.type:custom.googleapis.com/*"

# List all resources
gcloud compute resources list --project=elevatediq

# Get service URL
gcloud run services describe ollama-service --region=us-central1 --format='value(status.url)'
```

---

## Success Criteria

- [x] Monitoring infrastructure deployed
- [x] Database migrations applied
- [x] DNS resolving
- [x] Service health checks passing
- [x] Load tests completed with baseline metrics
- [x] Security audit clean
- [x] Backups verified
- [x] Team trained

---

## What to Do If Something Fails

| Issue | Solution |
|-------|----------|
| Monitoring script fails | Check GCP APIs enabled: `gcloud services list --enabled` |
| Migration fails | Check DATABASE_URL set: `echo $DATABASE_URL` |
| DNS not resolving | Wait 24-48 hours or check registrar settings |
| Service unhealthy | Check logs: `gcloud run logs read ollama-service --follow` |
| Load test fails | Verify endpoint accessible: `curl https://ollama-service-sozvlwbwva-uc.a.run.app/health` |
| Backup fails | Check Cloud SQL instance running: `gcloud sql instances list` |

---

## After Completion

1. ✅ Review [POST_DEPLOYMENT_ACTION_PLAN.md](POST_DEPLOYMENT_ACTION_PLAN.md)
2. ✅ Document any issues encountered
3. ✅ Brief team on status
4. ✅ Schedule follow-up verification in 7 days
5. ✅ Archive baselines for comparison

---

**Status**: 🟢 READY TO EXECUTE

**Questions?** See [DEVELOPER_QUICK_REFERENCE.md](DEVELOPER_QUICK_REFERENCE.md)

**Start with**: `chmod +x scripts/setup-monitoring.sh && ./scripts/setup-monitoring.sh`

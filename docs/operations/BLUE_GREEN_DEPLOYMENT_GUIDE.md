# Blue-Green Deployment & Rollback Procedures

This document provides comprehensive procedures for zero-downtime blue-green
deployments and emergency rollback procedures for the Ollama platform.

**Version**: 2.0.0
**Last Updated**: 2026-01-18
**Audience**: Platform Engineering, DevOps, SRE

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Blue-Green Deployment Process](#blue-green-deployment-process)
3. [Smoke Testing & Validation](#smoke-testing--validation)
4. [Traffic Cutover](#traffic-cutover)
5. [Rollback Procedures](#rollback-procedures)
6. [Emergency Procedures](#emergency-procedures)
7. [Monitoring & Alerts](#monitoring--alerts)
8. [Runbooks](#runbooks)

---

## Architecture Overview

### Blue-Green Topology

```text
┌─────────────────────────────────────────────────────────┐
│              GCP Load Balancer                          │
│         https://elevatediq.ai/ollama                   │
└────────────────────┬────────────────────────────────────┘
                     │
          ┌──────────┴──────────┐
          │                     │
      BLUE env               GREEN env
    (Current)             (Candidate)
   ┌──────────┐           ┌──────────┐
   │ FastAPI  │           │ FastAPI  │
   │ v1.0.0   │           │ v1.1.0   │
   │:8000     │           │:8000     │
   └──────────┘           └──────────┘
   ┌──────────┐           ┌──────────┐
   │PostgreSQL│           │PostgreSQL│
   │ Shared DB│──────────▶│ Shared DB│
   └──────────┘           └──────────┘
```

### Key Properties

- **Zero-downtime**: LB switches traffic without stopping services
- **Atomic**: Either all traffic moves or none
- **Reversible**: Instant rollback by reversing LB routing
- **Testable**: Full validation before cutover
- **Observable**: Detailed metrics during cutover

---

## Blue-Green Deployment Process

### Phase 1: Pre-Deployment (Preparation)

#### 1.1 Verify Prerequisites

```bash
#!/bin/bash
# Verify all prerequisites before starting deployment

set -euo pipefail

echo "🔍 Checking prerequisites..."

# 1. Verify current environment is healthy
./scripts/health-check.sh --current-env blue
if [ $? -ne 0 ]; then
    echo "❌ BLUE environment unhealthy. Abort deployment."
    exit 1
fi

# 2. Verify database backups exist
gsutil ls gs://ollama-backups/pre-deployment-$(date +%Y-%m-%d).sql
if [ $? -ne 0 ]; then
    echo "❌ No pre-deployment backup. Creating backup..."
    ./scripts/backup-database.sh
fi

# 3. Verify deployment artifacts are ready
if [ ! -f "./ollama-v1.1.0.tar.gz" ]; then
    echo "❌ Deployment artifact not found"
    exit 1
fi

# 4. Verify GCP credentials and permissions
gcloud auth application-default print-access-token > /dev/null
if [ $? -ne 0 ]; then
    echo "❌ GCP authentication failed"
    exit 1
fi

echo "✅ All prerequisites verified"
```

#### 1.2 Create Pre-Deployment Backup

```bash
#!/bin/bash
# Create database backup before starting deployment

BACKUP_DIR="gs://ollama-backups"
TIMESTAMP=$(date +%Y-%m-%d_%H-%M-%S)
BACKUP_FILE="${BACKUP_DIR}/pre-deployment-${TIMESTAMP}.sql"

echo "📦 Creating database backup..."

# Backup PostgreSQL (shared database)
pg_dump postgresql://user:pass@postgres:5432/ollama | gzip > "${BACKUP_FILE}.gz"

if [ $? -eq 0 ]; then
    echo "✅ Backup created: ${BACKUP_FILE}.gz"

    # Verify backup
    gsutil stat "${BACKUP_FILE}.gz"
    if [ $? -eq 0 ]; then
        echo "✅ Backup verified and accessible"
    else
        echo "⚠️  WARNING: Backup created but not accessible via gsutil"
    fi
else
    echo "❌ Backup failed. Aborting deployment."
    exit 1
fi
```

### Phase 2: Deploy to GREEN Environment

#### 2.1 Deploy Application

```bash
#!/bin/bash
# Deploy new version to GREEN environment

set -euo pipefail

VERSION="1.1.0"
GREEN_ENV="ollama-green"

echo "🚀 Starting deployment to GREEN environment..."
echo "   Version: ${VERSION}"
echo "   Environment: ${GREEN_ENV}"

# 1. Pull new image
echo "📥 Pulling image: ollama:${VERSION}"
docker pull ollama:${VERSION}
if [ $? -ne 0 ]; then
    echo "❌ Failed to pull image"
    exit 1
fi

# 2. Stop old GREEN (if exists)
echo "⏹️  Stopping old GREEN container (if exists)..."
docker-compose -p "${GREEN_ENV}" down --remove-orphans 2>/dev/null || true

# 3. Start new GREEN with new image
echo "▶️  Starting GREEN environment..."
docker-compose -f docker-compose.prod.yml \
    -p "${GREEN_ENV}" \
    up -d

if [ $? -ne 0 ]; then
    echo "❌ Failed to start GREEN environment"
    exit 1
fi

echo "✅ GREEN environment deployed"
echo "   Waiting for health checks..."

# 4. Wait for services to be ready
for i in {1..30}; do
    if docker-compose -p "${GREEN_ENV}" exec -T api curl -f http://localhost:8000/health > /dev/null 2>&1; then
        echo "✅ GREEN environment is healthy"
        break
    fi
    echo "   Waiting... ($i/30)"
    sleep 2
done

if [ $i -eq 30 ]; then
    echo "❌ GREEN environment failed health check"
    docker-compose -p "${GREEN_ENV}" logs api | tail -20
    exit 1
fi
```

#### 2.2 Deploy Database Migrations

```bash
#!/bin/bash
# Apply database migrations to shared database

set -euo pipefail

echo "🔄 Running database migrations..."

# Use Alembic to apply migrations
alembic upgrade head

if [ $? -eq 0 ]; then
    echo "✅ Migrations applied successfully"

    # Verify migration version
    alembic current
else
    echo "❌ Migration failed. Rolling back..."
    alembic downgrade -1
    exit 1
fi

# Verify data consistency
echo "🔍 Verifying data consistency..."
psql postgresql://user:pass@postgres:5432/ollama -c "SELECT COUNT(*) FROM pg_tables WHERE schemaname != 'pg_catalog';"
```

### Phase 3: Smoke Testing & Validation

#### 3.1 Health Checks

```bash
#!/bin/bash
# Comprehensive health checks for GREEN environment

set -euo pipefail

GREEN_ENDPOINT="http://green.ollama.local:8000"  # Internal DNS or IP
API_KEY="test-key-12345"

echo "🧪 Running smoke tests on GREEN environment..."

# Test 1: Basic connectivity
echo "  [1/8] Testing basic connectivity..."
curl -f "${GREEN_ENDPOINT}/health" \
    -H "Authorization: Bearer ${API_KEY}" \
    -m 5
echo "  ✅ Connectivity OK"

# Test 2: Model list
echo "  [2/8] Testing model list..."
MODELS=$(curl -s "${GREEN_ENDPOINT}/api/v1/models" \
    -H "Authorization: Bearer ${API_KEY}" | jq '.models | length')
echo "  ✅ Models available: ${MODELS}"

# Test 3: Inference health
echo "  [3/8] Testing inference capability..."
curl -X POST "${GREEN_ENDPOINT}/api/v1/generate" \
    -H "Authorization: Bearer ${API_KEY}" \
    -H "Content-Type: application/json" \
    -d '{"model": "llama3.2", "prompt": "Hello", "stream": false}' \
    -m 30
echo "  ✅ Inference OK"

# Test 4: Metrics endpoint
echo "  [4/8] Testing metrics..."
curl -f "http://green.ollama.local:9090/metrics" -m 5 > /dev/null
echo "  ✅ Metrics OK"

# Test 5: Database connectivity
echo "  [5/8] Testing database connectivity..."
curl -f "${GREEN_ENDPOINT}/api/v1/health/database" \
    -H "Authorization: Bearer ${API_KEY}" \
    -m 5
echo "  ✅ Database OK"

# Test 6: Cache connectivity
echo "  [6/8] Testing cache connectivity..."
curl -f "${GREEN_ENDPOINT}/api/v1/health/cache" \
    -H "Authorization: Bearer ${API_KEY}" \
    -m 5
echo "  ✅ Cache OK"

# Test 7: Load test (100 requests)
echo "  [7/8] Running load test (100 requests)..."
for i in {1..100}; do
    curl -s "${GREEN_ENDPOINT}/api/v1/generate" \
        -H "Authorization: Bearer ${API_KEY}" \
        -H "Content-Type: application/json" \
        -d "{\"model\": \"llama3.2\", \"prompt\": \"Test $i\", \"stream\": false}" \
        -m 10 > /dev/null &

    if [ $((i % 10)) -eq 0 ]; then
        wait
        echo "    Completed: ${i}/100 requests"
    fi
done
wait
echo "  ✅ Load test passed"

# Test 8: Performance baseline
echo "  [8/8] Testing performance baseline..."
START=$(date +%s%N)
curl -s "${GREEN_ENDPOINT}/api/v1/generate" \
    -H "Authorization: Bearer ${API_KEY}" \
    -H "Content-Type: application/json" \
    -d '{"model": "llama3.2", "prompt": "Test", "stream": false}' \
    -m 30 > /dev/null
END=$(date +%s%N)
LATENCY_MS=$(( (END - START) / 1000000 ))
echo "  ✅ Response latency: ${LATENCY_MS}ms"

echo ""
echo "✅ All smoke tests passed!"
```

#### 3.2 Functional Testing

```bash
#!/bin/bash
# Run automated functional tests

set -euo pipefail

echo "🧪 Running functional tests..."

# Run Python test suite
pytest tests/integration/test_deployment.py -v \
    --tb=short \
    --timeout=30 \
    -k "not slow" \
    --env=green

if [ $? -eq 0 ]; then
    echo "✅ Functional tests passed"
else
    echo "❌ Functional tests failed"
    exit 1
fi
```

### Phase 4: Traffic Cutover

#### 4.1 Switch Traffic to GREEN

```bash
#!/bin/bash
# Switch GCP Load Balancer traffic from BLUE to GREEN

set -euo pipefail

echo "🔄 Switching traffic from BLUE to GREEN..."

# Get current backend service
BLUE_BACKEND="ollama-blue-backend"
GREEN_BACKEND="ollama-green-backend"
FORWARDING_RULE="ollama-https-forwarding-rule"

echo "  Current backend: ${BLUE_BACKEND}"
echo "  Target backend: ${GREEN_BACKEND}"

# Get load balancer targets
echo "  Updating target pool..."
gcloud compute target-pools update "${FORWARDING_RULE}" \
    --backup-pool="${BLUE_BACKEND}" \
    --enable-backup-pool

if [ $? -eq 0 ]; then
    echo "  ✅ Backup pool configured (BLUE)"
fi

# Update forwarding rule to point to GREEN
echo "  Updating forwarding rule..."
gcloud compute forwarding-rules set-target "${FORWARDING_RULE}" \
    --backend-service="${GREEN_BACKEND}" \
    --global

if [ $? -eq 0 ]; then
    echo "  ✅ Traffic switched to GREEN"
else
    echo "  ❌ Failed to switch traffic"
    exit 1
fi

echo ""
echo "⚠️  TRAFFIC NOW ROUTING TO GREEN"
echo "   BLUE environment is in standby"
```

#### 4.2 Gradual Traffic Shift (Canary)

```bash
#!/bin/bash
# Gradually shift traffic to GREEN (safer approach)

set -euo pipefail

echo "🐤 Starting canary deployment (10% -> 50% -> 100%)..."

INCREMENTS=(10 25 50 75 100)
WAIT_TIME=300  # Wait 5 minutes between increments

for PERCENT in "${INCREMENTS[@]}"; do
    echo "🔄 Shifting ${PERCENT}% traffic to GREEN..."

    gcloud compute backend-services update ollama-backend \
        --global \
        --enable-cdn \
        --weight-rps-rules="[{target_pool: 'ollama-green', weight: ${PERCENT}}, {target_pool: 'ollama-blue', weight: $((100 - PERCENT))}]"

    if [ $? -eq 0 ]; then
        echo "  ✅ ${PERCENT}% traffic now on GREEN"

        # Monitor metrics at this traffic level
        echo "  📊 Monitoring for ${WAIT_TIME}s..."
        ./scripts/monitor-deployment.sh --duration=${WAIT_TIME} --threshold=1.0

        if [ $? -ne 0 ]; then
            echo "  ❌ Metrics exceeded threshold. Rolling back to previous percentage..."
            PREVIOUS_PERCENT=$((PERCENT - 25))
            if [ $PREVIOUS_PERCENT -lt 0 ]; then
                PREVIOUS_PERCENT=0
            fi

            # Rollback
            gcloud compute backend-services update ollama-backend \
                --global \
                --weight-rps-rules="[{target_pool: 'ollama-blue', weight: 100}]"

            echo "  ✅ Rolled back to BLUE"
            exit 1
        fi
    else
        echo "  ❌ Failed to update traffic percentage"
        exit 1
    fi
done

echo ""
echo "✅ Canary deployment successful - 100% traffic now on GREEN"
```

### Phase 5: Stabilization

#### 5.1 Monitor New Environment

```bash
#!/bin/bash
# Monitor GREEN environment after traffic cutover

set -euo pipefail

STABILIZATION_TIME=600  # 10 minutes
THRESHOLD_ERROR_RATE=1.0  # 1% error rate
THRESHOLD_LATENCY_P99=1000  # 1000ms

echo "📊 Monitoring GREEN environment for ${STABILIZATION_TIME}s..."

START_TIME=$(date +%s)
END_TIME=$((START_TIME + STABILIZATION_TIME))

while [ $(date +%s) -lt ${END_TIME} ]; do
    # Get current metrics
    ERROR_RATE=$(curl -s "http://prometheus:9090/api/v1/query" \
        --data-urlencode 'query=rate(http_requests_total{status=~"5.."}[5m])' | \
        jq -r '.data.result[0].value[1]')

    LATENCY_P99=$(curl -s "http://prometheus:9090/api/v1/query" \
        --data-urlencode 'query=histogram_quantile(0.99, http_request_duration_seconds)' | \
        jq -r '.data.result[0].value[1]')

    echo "  $(date): Error Rate: ${ERROR_RATE}%, P99 Latency: ${LATENCY_P99}ms"

    # Check thresholds
    if (( $(echo "$ERROR_RATE > $THRESHOLD_ERROR_RATE" | bc -l) )); then
        echo "  ❌ ERROR RATE EXCEEDED THRESHOLD!"
        exit 1
    fi

    if (( $(echo "$LATENCY_P99 > $THRESHOLD_LATENCY_P99" | bc -l) )); then
        echo "  ❌ LATENCY EXCEEDED THRESHOLD!"
        exit 1
    fi

    sleep 30
done

echo "✅ Stabilization period passed - Deployment successful!"
```

---

## Smoke Testing & Validation

### Required Test Suite

```python
"""Deployment smoke tests

pytest tests/integration/test_smoke.py -v --env=green
"""

import pytest
import httpx
import time

@pytest.mark.smoke
async def test_health_check(green_endpoint: str):
    """Test basic health endpoint."""
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{green_endpoint}/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"

@pytest.mark.smoke
async def test_inference_endpoint(green_endpoint: str, api_key: str):
    """Test inference capability."""
    async with httpx.AsyncClient() as client:
        start = time.time()
        response = await client.post(
            f"{green_endpoint}/api/v1/generate",
            headers={"Authorization": f"Bearer {api_key}"},
            json={"model": "llama3.2", "prompt": "Test", "stream": False},
            timeout=30.0
        )
        latency = (time.time() - start) * 1000

        assert response.status_code == 200
        assert latency < 5000  # 5 second max
        data = response.json()
        assert "text" in data
        assert len(data["text"]) > 0

@pytest.mark.smoke
async def test_cache_hit(green_endpoint: str, api_key: str):
    """Test that cache hit reduces latency by 40%."""
    async with httpx.AsyncClient() as client:
        prompt = "What is 2+2?"

        # First request (no cache)
        start1 = time.time()
        resp1 = await client.post(
            f"{green_endpoint}/api/v1/generate",
            headers={"Authorization": f"Bearer {api_key}"},
            json={"model": "llama3.2", "prompt": prompt, "stream": False},
            timeout=30.0
        )
        latency1 = (time.time() - start1) * 1000

        # Second request (should cache hit)
        start2 = time.time()
        resp2 = await client.post(
            f"{green_endpoint}/api/v1/generate",
            headers={"Authorization": f"Bearer {api_key}"},
            json={"model": "llama3.2", "prompt": prompt, "stream": False},
            timeout=30.0
        )
        latency2 = (time.time() - start2) * 1000

        # Cache should be 40% faster
        improvement = ((latency1 - latency2) / latency1) * 100
        assert improvement > 40, f"Cache improvement only {improvement}%"
        assert resp1.json() == resp2.json()  # Same response

@pytest.mark.smoke
async def test_database_connectivity(green_endpoint: str, api_key: str):
    """Test database is accessible."""
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{green_endpoint}/api/v1/health/database",
            headers={"Authorization": f"Bearer {api_key}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["database"]["connected"] is True

@pytest.mark.smoke
async def test_load_tolerance(green_endpoint: str, api_key: str):
    """Test endpoint handles concurrent requests."""
    async with httpx.AsyncClient() as client:
        tasks = []
        for i in range(50):
            task = client.post(
                f"{green_endpoint}/api/v1/generate",
                headers={"Authorization": f"Bearer {api_key}"},
                json={"model": "llama3.2", "prompt": f"Test {i}", "stream": False},
                timeout=30.0
            )
            tasks.append(task)

        # Gather all results
        responses = await asyncio.gather(*tasks, return_exceptions=True)

        # Check that at least 90% succeeded
        successes = sum(1 for r in responses if isinstance(r, httpx.Response) and r.status_code == 200)
        assert successes / len(responses) >= 0.9
```

---

## Traffic Cutover

### Cutover Checklist

- [ ] All smoke tests pass on GREEN
- [ ] Database migrations verified
- [ ] Performance baselines meet or exceed BLUE
- [ ] Backup created and verified
- [ ] GCP credentials and permissions verified
- [ ] Monitoring dashboards configured
- [ ] Alert thresholds set appropriately
- [ ] Team notified and standing by
- [ ] Rollback plan communicated

---

## Rollback Procedures

### Immediate Rollback (< 1 second recovery)

```bash
#!/bin/bash
# Emergency rollback: Switch traffic back to BLUE immediately

set -euo pipefail

echo "🚨 EXECUTING IMMEDIATE ROLLBACK..."
echo "   Switching traffic back to BLUE"

BLUE_BACKEND="ollama-blue-backend"
FORWARDING_RULE="ollama-https-forwarding-rule"

# Switch traffic back to BLUE (atomic operation)
gcloud compute forwarding-rules set-target "${FORWARDING_RULE}" \
    --backend-service="${BLUE_BACKEND}" \
    --global \
    --quiet

if [ $? -eq 0 ]; then
    echo "✅ Traffic switched back to BLUE"
    echo "   All traffic now on previous stable version"

    # Verify
    sleep 2
    ./scripts/health-check.sh --env=blue
    if [ $? -eq 0 ]; then
        echo "✅ BLUE environment confirmed healthy"
        echo ""
        echo "🎯 ROLLBACK COMPLETE"
        echo "   Platform restored to previous version"
    fi
else
    echo "❌ Rollback failed!"
    echo "   Manual intervention required"
    exit 1
fi
```

### Graceful Rollback (Full validation)

```bash
#!/bin/bash
# Graceful rollback with validation

set -euo pipefail

echo "🔄 Starting graceful rollback..."

# Phase 1: Canary rollback (shift traffic gradually)
echo ""
echo "Phase 1: Canary Rollback (shifting traffic to BLUE)"
./scripts/canary-shift.sh --target=blue --increments="75 50 25 0"

if [ $? -ne 0 ]; then
    echo "❌ Canary rollback failed"
    exit 1
fi

# Phase 2: Stop GREEN environment
echo ""
echo "Phase 2: Stopping GREEN environment"
docker-compose -p ollama-green down

# Phase 3: Cleanup GREEN
echo ""
echo "Phase 3: Cleaning up GREEN artifacts"
docker system prune -f
gsutil rm -r gs://ollama-deployments/green-v* || true

# Phase 4: Verify BLUE is fully operational
echo ""
echo "Phase 4: Verifying BLUE environment"
./scripts/smoke-tests.sh --env=blue

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ ROLLBACK COMPLETE"
    echo "   All traffic on BLUE (stable version)"
    echo "   GREEN environment cleaned up"
else
    echo "❌ BLUE verification failed"
    exit 1
fi
```

### Database Rollback

```bash
#!/bin/bash
# Rollback database to pre-deployment state

set -euo pipefail

echo "🔄 Rolling back database..."

# Get latest pre-deployment backup
BACKUP=$(gsutil ls gs://ollama-backups/ | grep "pre-deployment-" | sort | tail -1)

if [ -z "$BACKUP" ]; then
    echo "❌ No backup found!"
    exit 1
fi

echo "   Using backup: ${BACKUP}"

# Download and verify backup
echo "   Downloading backup..."
gsutil cp "${BACKUP}" /tmp/backup.sql.gz
gunzip /tmp/backup.sql.gz

# Verify backup integrity
echo "   Verifying backup..."
file /tmp/backup.sql | grep -q "SQL"
if [ $? -ne 0 ]; then
    echo "❌ Backup file appears corrupted"
    exit 1
fi

# Restore database
echo "   Restoring database..."
psql postgresql://user:pass@postgres:5432/ollama < /tmp/backup.sql

if [ $? -eq 0 ]; then
    echo "✅ Database restored from backup"

    # Verify data consistency
    echo "   Verifying data consistency..."
    psql postgresql://user:pass@postgres:5432/ollama -c "SELECT COUNT(*) FROM users;"
else
    echo "❌ Database restore failed"
    rm /tmp/backup.sql
    exit 1
fi

# Cleanup
rm /tmp/backup.sql
echo "✅ Database rollback complete"
```

---

## Emergency Procedures

### Circuit Breaker Activation

The circuit breaker automatically activates if:

1. **Inference failures**: > 5 failures in 60 seconds
2. **Database errors**: > 3 connection failures
3. **Cache unavailable**: > 2 timeouts
4. **API latency**: P99 > 10 seconds

```bash
#!/bin/bash
# Manual circuit breaker reset if needed

curl -X POST "http://api:8000/admin/circuit-breaker/reset" \
    -H "Authorization: Bearer admin-key" \
    -H "Content-Type: application/json" \
    -d '{"breaker": "inference"}'
```

### Emergency Communication

```bash
#!/bin/bash
# Send emergency notification

SERVICE_NOW_TOKEN="$(gcloud secrets versions access latest --secret=servicenow-token)"

curl -X POST "https://dev121212.service-now.com/api/now/table/incident" \
    -H "Authorization: Bearer ${SERVICE_NOW_TOKEN}" \
    -H "Content-Type: application/json" \
    -d '{
        "short_description": "Ollama Deployment Rollback Executed",
        "urgency": "1",
        "impact": "2",
        "assigned_to": "platform-team",
        "comments": "Deployment to v1.1.0 rolled back. Reverting to v1.0.0."
    }'
```

---

## Monitoring & Alerts

### Key Metrics During Deployment

```yaml
# Prometheus alert rules for deployment monitoring

groups:
  - name: deployment
    rules:
      - alert: DeploymentErrorRateHigh
        expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.01
        for: 2m
        annotations:
          summary: "Error rate {{ $value | humanizePercentage }} exceeds threshold"

      - alert: DeploymentLatencyHigh
        expr: histogram_quantile(0.99, http_request_duration_seconds) > 1.0
        for: 2m
        annotations:
          summary: "P99 latency {{ $value | humanize }}s exceeds threshold"

      - alert: DeploymentCacheHitLow
        expr: rate(cache_hits[5m]) / rate(cache_requests[5m]) < 0.7
        for: 5m
        annotations:
          summary: "Cache hit rate {{ $value | humanizePercentage }} below baseline"

      - alert: DatabaseConnectionErrors
        expr: rate(db_connection_errors[5m]) > 0.1
        for: 1m
        annotations:
          summary: "Database connection errors detected"
```

### Deployment Dashboard

```text
Dashboard: Ollama Deployment Status

┌─────────────────────────────────────────────────────────┐
│ Current Environment: GREEN (v1.1.0)                     │
│ Traffic Distribution: BLUE 0% | GREEN 100%              │
├─────────────────────────────────────────────────────────┤
│ Requests/sec      │ 125 req/s (↑ 5%)                    │
│ Error Rate        │ 0.02% (↓ 50%)                       │
│ P99 Latency       │ 245ms (↓ 40%)                       │
│ Cache Hit Rate    │ 82% (↑ 12%)                         │
├─────────────────────────────────────────────────────────┤
│ Last Update: 2026-01-18 14:30:00 UTC                    │
│ Status: ✅ HEALTHY                                       │
└─────────────────────────────────────────────────────────┘
```

---

## Runbooks

### Runbook: Deployment Failed at Smoke Test

**Problem**: Smoke tests failing on GREEN environment

**Solution**:

```bash
# 1. Get detailed logs
docker-compose -p ollama-green logs api | tail -100

# 2. Check application health
curl -v http://green.ollama.local:8000/health

# 3. Check dependencies
docker-compose -p ollama-green ps

# 4. If database issue:
docker-compose -p ollama-green exec postgres psql -U ollama -c "SELECT 1;"

# 5. If cache issue:
docker-compose -p ollama-green exec redis redis-cli ping

# 6. Abort deployment
./scripts/deployment-rollback.sh --immediate
```

### Runbook: Partial Traffic Switch

**Problem**: Traffic not switching completely to GREEN

**Solution**:

```bash
# 1. Check current LB configuration
gcloud compute backend-services describe ollama-backend --global

# 2. Check health of both backends
gcloud compute backend-services get-health ollama-blue-backend --global
gcloud compute backend-services get-health ollama-green-backend --global

# 3. Reset traffic to 100% BLUE
gcloud compute backend-services update ollama-backend \
    --global \
    --enable-cdn \
    --weight-rps-rules="[{target_pool: 'ollama-blue', weight: 100}]"

# 4. Investigate GREEN health
docker-compose -p ollama-green logs api --tail=50
```

### Runbook: Performance Degradation Post-Deployment

**Problem**: Response latency increased 5x after deployment

**Solution**:

```bash
# 1. Immediate action: Rollback
./scripts/deployment-rollback.sh --immediate

# 2. Investigate root cause
./scripts/profiler.sh --env=green --duration=300
snakeviz /tmp/profile.prof

# 3. Check for resource contention
docker stats ollama-green-api
df -h
free -h

# 4. Review slow queries
./scripts/analyze-slow-queries.sh --env=green

# 5. Check for N+1 query problems
# Review recent code changes and database query patterns
```

---

## Deployment Checklist

```
PRE-DEPLOYMENT
  □ All tests pass locally
  □ Code review approved
  □ Database migrations tested
  □ Performance benchmarks pass
  □ Security audit clean

DEPLOYMENT PREP
  □ Backup created and verified
  □ GREEN environment provisioned
  □ Monitoring dashboards created
  □ Alert thresholds configured
  □ Runbooks reviewed
  □ Team notified

BLUE-GREEN SWITCH
  □ All smoke tests pass
  □ Load test successful
  □ Canary phase 1 (10%) stable for 5 min
  □ Canary phase 2 (50%) stable for 5 min
  □ Canary phase 3 (100%) stable for 5 min

POST-DEPLOYMENT
  □ Error rates normal
  □ Latency at baseline or better
  □ Cache hit rates at target
  □ Database queries performing
  □ No alerts firing

PRODUCTION SIGN-OFF
  □ All metrics nominal
  □ Team confirms stability
  □ Green environment declared production
  □ Blue environment retained as backup
```

---

## References

- [GCP Load Balancer Documentation](https://cloud.google.com/load-balancing/docs)
- [Blue-Green Deployment Pattern](https://martinfowler.com/bliki/BlueGreenDeployment.html)
- [Zero-Downtime Deployments](https://landing.google.com/sre/books/)

---

**Document Version**: 2.0.0
**Last Updated**: 2026-01-18
**Author**: Ollama Platform Engineering
**Maintained By**: @kushin77

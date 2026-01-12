#!/bin/bash
# ============================================================================
# One-command deployment for Ollama Elite stack
# ============================================================================
set -e

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

COMPOSE_FILE="docker-compose.elite.yml"

step() { echo -e "\n➡️  $1"; }
success() { echo -e "✅ $1"; }
fail() { echo -e "❌ $1"; exit 1; }

# 1) Pre-flight checks
step "Running pre-flight checks"
if ! command -v docker &>/dev/null; then fail "Docker not installed"; fi
if ! command -v docker-compose &>/dev/null; then fail "Docker Compose not installed"; fi
if ! command -v nvidia-smi &>/dev/null; then echo "⚠️  GPU not detected (nvidia-smi missing)"; fi
if ! test -f .env.production; then fail ".env.production missing"; fi

# Required dirs
mkdir -p /mnt/data/ollama/models \
         /mnt/data/ollama/postgres \
         /mnt/data/ollama/qdrant \
         /mnt/backups/postgres \
         /mnt/backups/qdrant \
         /var/lib/ollama/logs

# 2) Pull images
step "Pulling images"
docker-compose -f $COMPOSE_FILE pull

# 3) Start stack
step "Starting stack"
docker-compose -f $COMPOSE_FILE up -d

# 4) Show status
step "Services status"
docker-compose -f $COMPOSE_FILE ps

# 5) Tail key logs (short)
step "Recent logs (ollama-api)"
docker-compose -f $COMPOSE_FILE logs --tail=50 ollama-api

success "Deployment complete. Stack is running on 192.168.168.42 (nginx 80/443, API 8000 internal)."

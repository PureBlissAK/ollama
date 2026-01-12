#!/bin/bash
# ============================================================================
# Pre-flight validation for Ollama Elite deployment
# ============================================================================
set -e

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

check_cmd() {
  if ! command -v "$1" &>/dev/null; then
    echo "❌ Missing: $1"; exit 1; fi
}

echo "➡️  Checking required commands"
check_cmd docker
check_cmd docker-compose
check_cmd curl
check_cmd openssl

if command -v nvidia-smi &>/dev/null; then
  echo "✅ GPU detected: $(nvidia-smi --query-gpu=name --format=csv,noheader | head -n1)"
else
  echo "⚠️  GPU not detected (nvidia-smi missing)"
fi

echo "➡️  Checking .env.production"
if [ ! -f .env.production ]; then
  echo "❌ .env.production missing"; exit 1; fi

echo "➡️  Checking secrets"
for f in secrets/db_password.txt secrets/redis_password.txt secrets/grafana_password.txt secrets/grafana_db_password.txt; do
  if [ ! -f "$f" ]; then echo "❌ Missing secret: $f"; exit 1; fi
done
if [ ! -f secrets/gcp-service-account.json ]; then
  echo "⚠️  Missing GCP service account key (required for GCS backups)"
fi

echo "➡️  Checking data directories"
for d in /mnt/data/ollama/models /mnt/data/ollama/postgres /mnt/data/ollama/qdrant /mnt/backups/postgres /mnt/backups/qdrant /var/lib/ollama/logs; do
  if [ ! -d "$d" ]; then
    echo "⚠️  Creating $d"; sudo mkdir -p "$d"; sudo chown $(id -u):$(id -g) "$d"; fi
done

echo "➡️  Network check (local host 192.168.168.42)"
if ! ping -c1 192.168.168.42 &>/dev/null; then
  echo "⚠️  Host IP 192.168.168.42 unreachable from current network"
fi

echo "✅ Pre-flight checks passed"

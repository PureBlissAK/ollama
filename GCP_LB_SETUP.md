# GCP Load Balancer Setup for Local Ollama

## Architecture Overview

```
Internet
    ↓
GCP Load Balancer (elevatediq.ai/ollama)
  - TLS Termination
  - Health Checks
  - Rate Limiting
    ↓
Local Docker Host (192.168.168.42)
  - Ollama API (port 8000)
  - PostgreSQL, Redis, Qdrant
  - Prometheus, Grafana, Jaeger
```

**Important**: Ollama runs locally on Docker. GCP provides ONLY the Load Balancer for public access.

---

## Prerequisites

- Local Docker host running at: `192.168.168.42`
- Ollama Docker stack running on port 8000
- GCP account with billing enabled
- Domain: `elevatediq.ai` (DNS managed)

---

## Step 1: Deploy Ollama Locally

```bash
# On local host (192.168.168.35)
cd /home/akushnir/ollama

# Start production stack
docker-compose -f docker-compose.prod.yml up -d

# Verify services running
docker-compose ps
curl http://localhost:8000/health
```

---

## Step 2: Configure Local Firewall

```bash
# Allow GCP Load Balancer health checks and traffic
# GCP health check IP ranges: 35.191.0.0/16, 130.211.0.0/22

sudo ufw allow from 35.191.0.0/16 to any port 8000
sudo ufw allow from 130.211.0.0/22 to any port 8000

# Or if using iptables
sudo iptables -A INPUT -p tcp --dport 8000 -s 35.191.0.0/16 -j ACCEPT
sudo iptables -A INPUT -p tcp --dport 8000 -s 130.211.0.0/22 -j ACCEPT
```

---

## Step 3: Create GCP Backend Service

```bash
# Create health check
gcloud compute health-checks create http ollama-health-check \
    --port=8000 \
    --request-path="/health" \
    --check-interval=10s \
    --timeout=5s \
    --unhealthy-threshold=3 \
    --healthy-threshold=2

# Create backend service (pointing to your local IP)
gcloud compute backend-services create ollama-backend \
    --protocol=HTTP \
    --health-checks=ollama-health-check \
    --port-name=http \
    --timeout=30s \
    --global

# Add your local Docker host as backend
# Note: Use Network Endpoint Group (NEG) for external endpoint
gcloud compute network-endpoint-groups create ollama-neg \
    --network-endpoint-type=NON_GCP_PRIVATE_IP_PORT \
    --zone=us-central1-a

gcloud compute network-endpoint-groups update ollama-neg \
    --zone=us-central1-a \
    --add-endpoint="ip=192.168.168.42,port=8000"

gcloud compute backend-services add-backend ollama-backend \
    --network-endpoint-group=ollama-neg \
    --network-endpoint-group-zone=us-central1-a \
    --global
```

---

## Step 4: Set Up Cloud Armor (Optional but Recommended)

```bash
# Create security policy
gcloud compute security-policies create ollama-security-policy

# Add rate limiting rule
gcloud compute security-policies rules create 1000 \
    --security-policy=ollama-security-policy \
    --expression="true" \
    --action=rate-based-ban \
    --rate-limit-threshold-count=100 \
    --rate-limit-threshold-interval-sec=60 \
    --ban-duration-sec=600

# Apply to backend service
gcloud compute backend-services update ollama-backend \
    --security-policy=ollama-security-policy \
    --global
```

---

## Step 5: Create URL Map

```bash
# Create URL map
gcloud compute url-maps create ollama-lb \
    --default-service=ollama-backend

# Add path matcher for /ollama
gcloud compute url-maps add-path-matcher ollama-lb \
    --path-matcher-name=ollama-paths \
    --default-service=ollama-backend \
    --path-rules="/ollama=ollama-backend,/ollama/*=ollama-backend"
```

---

## Step 6: Create SSL Certificate

```bash
# Option 1: Google-managed certificate (automatic renewal)
gcloud compute ssl-certificates create ollama-ssl-cert \
    --domains=elevatediq.ai \
    --global

# Option 2: Upload your own certificate
gcloud compute ssl-certificates create ollama-ssl-cert \
    --certificate=/path/to/cert.pem \
    --private-key=/path/to/key.pem \
    --global
```

---

## Step 7: Create Target HTTPS Proxy

```bash
gcloud compute target-https-proxies create ollama-https-proxy \
    --url-map=ollama-lb \
    --ssl-certificates=ollama-ssl-cert
```

---

## Step 8: Create Forwarding Rule

```bash
# Reserve static IP
gcloud compute addresses create ollama-ip --global

# Get the IP address
gcloud compute addresses describe ollama-ip --global --format="get(address)"

# Create forwarding rule
gcloud compute forwarding-rules create ollama-https-forwarding-rule \
    --address=ollama-ip \
    --global \
    --target-https-proxy=ollama-https-proxy \
    --ports=443
```

---

## Step 9: Configure DNS

```bash
# Get the Load Balancer IP
LB_IP=$(gcloud compute addresses describe ollama-ip --global --format="get(address)")

# Add DNS A record
# elevatediq.ai -> $LB_IP

# Using Cloud DNS (if DNS hosted in GCP)
gcloud dns record-sets create elevatediq.ai. \
    --zone=elevatediq-zone \
    --type=A \
    --ttl=300 \
    --rrdatas=$LB_IP
```

---

## Step 10: Test Configuration

```bash
# Wait for DNS propagation (up to 48 hours, usually <1 hour)
nslookup elevatediq.ai

# Test health check
curl https://elevatediq.ai/ollama/health

# Test API
curl https://elevatediq.ai/ollama/api/models

# Test with authentication
curl -H "Authorization: Bearer YOUR_API_KEY" \
    https://elevatediq.ai/ollama/api/generate \
    -d '{"model":"llama2","prompt":"Hello"}'
```

---

## Monitoring & Troubleshooting

### View Load Balancer Logs

```bash
# View access logs
gcloud logging read "resource.type=http_load_balancer" --limit=50

# View backend health
gcloud compute backend-services get-health ollama-backend --global
```

### Check Health Status

```bash
# Check backend health
gcloud compute backend-services get-health ollama-backend \
    --global \
    --format=json

# Expected output: HEALTHY status
```

### Common Issues

**Backend Unhealthy**
- Check firewall allows health check IPs (35.191.0.0/16, 130.211.0.0/22)
- Verify local Docker containers are running: `docker-compose ps`
- Test health endpoint locally: `curl http://localhost:8000/health`

**SSL Certificate Not Provisioning**
- Google-managed certs can take 15-60 minutes
- Verify DNS is pointing to LB IP
- Check domain ownership verification

**502 Bad Gateway**
- Backend is down or unreachable
- Check local Docker services are running
- Verify network connectivity from GCP to local host

---

## Architecture Details

### Traffic Flow

1. **Client** → `https://elevatediq.ai/ollama`
2. **GCP Load Balancer** → TLS termination, health checks, rate limiting
3. **Local Docker Host** (192.168.168.42:8000) → Ollama API
4. **Response** → Back through LB to client

### Security Layers

1. **GCP Layer**
   - TLS termination (HTTPS)
   - Cloud Armor (DDoS protection, rate limiting)
   - Health checks (only route to healthy backends)

2. **Local Layer**
   - Docker network isolation
   - API key authentication
   - Input validation
   - Audit logging

---

## Cost Estimates (Monthly)

| Component | Cost (USD) |
|-----------|-----------|
| Load Balancer | $18 base + traffic |
| SSL Certificate (managed) | Free |
| Cloud Armor | $6 + rules |
| Egress traffic (100GB) | ~$12 |
| **Total (estimated)** | **~$40-60/month** |

---

## Maintenance

### Update Backend IP

```bash
# If local Docker host IP changes
gcloud compute network-endpoint-groups update ollama-neg \
    --zone=us-central1-a \
    --remove-endpoint="ip=OLD_IP,port=8000"

gcloud compute network-endpoint-groups update ollama-neg \
    --zone=us-central1-a \
    --add-endpoint="ip=NEW_IP,port=8000"
```

### Renew SSL Certificate (manual cert only)

```bash
gcloud compute ssl-certificates create ollama-ssl-cert-new \
    --certificate=/path/to/new-cert.pem \
    --private-key=/path/to/new-key.pem \
    --global

gcloud compute target-https-proxies update ollama-https-proxy \
    --ssl-certificates=ollama-ssl-cert-new
```

---

## Summary

✅ **GCP provides**: Load Balancer, TLS termination, health checks, DDoS protection  
✅ **Local Docker provides**: Ollama API, databases, monitoring stack  
✅ **Public endpoint**: `https://elevatediq.ai/ollama`

This architecture keeps all AI workloads and data local while providing professional public access through GCP's infrastructure.

---

**Last Updated**: January 12, 2026  
**Local Host**: 192.168.168.42  
**Public Endpoint**: https://elevatediq.ai/ollama

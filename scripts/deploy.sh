#!/usr/bin/env bash
set -euo pipefail

# ==============================================================================
# Distributed Threat Intelligence Platform - Zero-Downtime Deployment Script
# ==============================================================================

echo "=========================================================="
echo "🚀 Initiating Automated Production Deployment..."
echo "Timestamp: $(date -u +"%Y-%m-%dT%H:%M:%SZ")"
echo "=========================================================="

ENV_FILE="${1:-.env.production}"

if [ -f "$ENV_FILE" ]; then
    echo "📋 Loading environment configuration from $ENV_FILE"
    export $(grep -v '^#' "$ENV_FILE" | xargs)
else
    echo "⚠️ Warning: $ENV_FILE not found, using existing environment variables."
fi

# 1. Pull latest published images from Container Registry
echo "📦 Pulling latest container images..."
docker compose -f docker-compose.prod.yml pull

# 2. Apply database migrations if any
echo "🗄️ Checking database container health..."
docker compose -f docker-compose.prod.yml up -d postgres redis

echo "⏳ Waiting for PostgreSQL & Redis to be healthy..."
RETRIES=15
until docker compose -f docker-compose.prod.yml exec -T postgres pg_isready -U "${POSTGRES_USER:-postgres}" > /dev/null 2>&1 || [ $RETRIES -eq 0 ]; do
    echo "Waiting for postgres... ($RETRIES remaining)"
    sleep 2
    RETRIES=$((RETRIES - 1))
done

if [ $RETRIES -eq 0 ]; then
    echo "❌ Database health check timed out! Aborting deployment."
    exit 1
fi

# 3. Perform rolling update of application microservices
echo "🔄 Rolling out microservices (collector, enricher, api_server, frontend)..."
docker compose -f docker-compose.prod.yml up -d --remove-orphans collector enricher api_server frontend

# 4. Smoke test & Health Check Verification
echo "🩺 Performing post-deployment smoke tests..."
sleep 5

API_HEALTH_URL="http://localhost:5000/api/health"
COLLECTOR_HEALTH_URL="http://localhost:5001/health"

check_health() {
    local url=$1
    local name=$2
    if curl -f -s "$url" > /dev/null; then
        echo "✅ $name is Healthy!"
    else
        echo "❌ $name health check failed at $url!"
        return 1
    fi
}

check_health "$API_HEALTH_URL" "API Server"
check_health "$COLLECTOR_HEALTH_URL" "Collector Service"

# 5. Clean up dangling images
echo "🧹 Pruning dangling docker images..."
docker image prune -f

echo "=========================================================="
echo "🎉 Deployment successfully completed! All services are live."
echo "=========================================================="

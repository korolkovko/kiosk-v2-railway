#!/bin/bash
# cleanup-docker.sh
# Script to clean up Docker containers and fix permission issues

set -e

echo "🧹 Cleaning up KIOSK Docker environment"
echo "======================================"

# Use docker compose (new) or docker-compose (legacy)
DOCKER_COMPOSE_CMD="docker-compose"
if docker compose version > /dev/null 2>&1; then
    DOCKER_COMPOSE_CMD="docker compose"
fi

echo "🛑 Stopping all KIOSK containers..."
$DOCKER_COMPOSE_CMD down --remove-orphans || true

echo "📦 Removing KIOSK images..."
docker rmi $(docker images | grep kiosk | awk '{print $3}') 2>/dev/null || true

echo "🔧 Fixing frontend permissions..."
sudo rm -rf frontend/node_modules 2>/dev/null || true
sudo rm -f frontend/package-lock.json 2>/dev/null || true

echo "🗂️  Cleaning data directories (optional)..."
read -p "Do you want to clean data directories? This will remove all database data! (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    sudo rm -rf data/uploads/* data/logs/* data/postgres/* 2>/dev/null || true
    echo "✅ Data directories cleaned"
else
    echo "⏭️  Data directories preserved"
fi

echo "🐳 Pruning Docker system..."
docker system prune -f

echo ""
echo "✅ Cleanup completed!"
echo ""
echo "🚀 You can now run: ./start-docker.sh"
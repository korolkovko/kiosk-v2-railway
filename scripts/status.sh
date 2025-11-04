#!/bin/bash

# KIOSK Application Status Script

echo "KIOSK Application Status"
echo "======================="

# Check if services are running
docker-compose ps

echo ""
echo "System Resources:"
echo "=================="
docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}" $(docker-compose ps -q) 2>/dev/null || echo "No containers running"
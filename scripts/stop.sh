#!/bin/bash

# KIOSK Application Stop Script

echo "Stopping KIOSK Application..."

# Stop all services
docker-compose down

echo "✅ KIOSK Application stopped successfully!"
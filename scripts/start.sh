#!/bin/bash

# KIOSK Application Start Script

echo "Starting KIOSK Application..."

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "Error: Docker is not running. Please start Docker first."
    exit 1
fi

# Check if docker-compose is available
if ! command -v docker-compose &> /dev/null; then
    echo "Error: docker-compose is not installed."
    exit 1
fi

# Create data directories if they don't exist
mkdir -p data/{postgres,logs,backups,uploads}

# Generate .env file from .env.example if it doesn't exist
if [ ! -f .env ]; then
    echo "Creating .env file from .env.example..."
    cp .env.example .env
    
    # Generate random secret keys
    SECRET_KEY=$(openssl rand -hex 32)
    JWT_SECRET_KEY=$(openssl rand -hex 32)
    
    # Replace placeholder values
    sed -i.bak "s/your-secret-key-here/$SECRET_KEY/g" .env
    sed -i.bak "s/your-jwt-secret-key-here/$JWT_SECRET_KEY/g" .env
    rm .env.bak
    
    echo "Generated .env file with random secret keys"
fi

# Start services
echo "Starting services..."
docker-compose up -d

# Wait for services to be ready
echo "Waiting for services to be ready..."
sleep 10

# Check if services are running
if docker-compose ps | grep -q "Up"; then
    echo "✅ KIOSK Application started successfully!"
    echo ""
    echo "Access URLs:"
    echo "- Backend API: http://localhost:8001"
    echo "- API Documentation: http://localhost:8001/docs"
    echo "- Kiosk Frontend: http://localhost:8080 (use --profile kiosk)"
    echo ""
    echo "To view logs: ./scripts/logs.sh"
    echo "To stop: ./scripts/stop.sh"
else
    echo "❌ Failed to start services. Check logs with: ./scripts/logs.sh"
    exit 1
fi
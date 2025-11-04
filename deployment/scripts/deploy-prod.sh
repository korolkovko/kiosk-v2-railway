#!/bin/bash
# deploy-prod.sh
# Production deployment script for KIOSK application
# Run this on production server after git pull

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}KIOSK Production Deployment${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# Check if running from correct directory
if [ ! -f "docker-compose.yml" ]; then
    echo -e "${RED}Error: docker-compose.yml not found${NC}"
    echo "Please run this script from /opt/kiosk directory"
    exit 1
fi

# Check if .env.prod exists
if [ ! -f "/opt/kiosk/secrets/.env.prod" ]; then
    echo -e "${RED}Error: /opt/kiosk/secrets/.env.prod not found${NC}"
    echo "Please run setup-secrets.sh first"
    exit 1
fi

echo -e "${YELLOW}Step 1: Pulling latest code from git...${NC}"
git pull origin main || {
    echo -e "${RED}Failed to pull from git${NC}"
    exit 1
}
echo -e "${GREEN}✓ Code updated${NC}"
echo ""

echo -e "${YELLOW}Step 2: Building Docker images...${NC}"
docker compose -f docker-compose.yml \
               -f docker-compose.prod.yml \
               --env-file /opt/kiosk/secrets/.env.prod \
               build --no-cache || {
    echo -e "${RED}Failed to build images${NC}"
    exit 1
}
echo -e "${GREEN}✓ Images built${NC}"
echo ""

echo -e "${YELLOW}Step 3: Stopping old containers...${NC}"
docker compose -f docker-compose.yml \
               -f docker-compose.prod.yml \
               down || {
    echo -e "${RED}Failed to stop containers${NC}"
    exit 1
}
echo -e "${GREEN}✓ Old containers stopped${NC}"
echo ""

echo -e "${YELLOW}Step 4: Starting new containers...${NC}"
docker compose -f docker-compose.yml \
               -f docker-compose.prod.yml \
               --env-file /opt/kiosk/secrets/.env.prod \
               up -d || {
    echo -e "${RED}Failed to start containers${NC}"
    exit 1
}
echo -e "${GREEN}✓ Containers started${NC}"
echo ""

echo -e "${YELLOW}Step 5: Waiting for services to be healthy...${NC}"
sleep 10
echo -e "${GREEN}✓ Services starting${NC}"
echo ""

echo -e "${YELLOW}Step 6: Running database migrations...${NC}"
docker compose exec -T backend alembic upgrade head || {
    echo -e "${RED}Failed to run migrations${NC}"
    exit 1
}
echo -e "${GREEN}✓ Migrations applied${NC}"
echo ""

echo -e "${YELLOW}Step 7: Checking service status...${NC}"
docker compose ps
echo ""

echo -e "${YELLOW}Step 8: Testing endpoints...${NC}"
# Test backend health
if curl -f -s http://localhost:8001/health > /dev/null; then
    echo -e "${GREEN}✓ Backend health check passed${NC}"
else
    echo -e "${RED}✗ Backend health check failed${NC}"
fi

# Test nginx
if curl -f -s http://localhost/ > /dev/null; then
    echo -e "${GREEN}✓ Nginx is responding${NC}"
else
    echo -e "${RED}✗ Nginx is not responding${NC}"
fi
echo ""

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Deployment completed successfully!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "Access your application:"
echo "  - Frontend: https://$(hostname -f)"
echo "  - API Docs: https://$(hostname -f)/docs"
echo ""
echo "View logs:"
echo "  docker compose logs -f"
echo ""
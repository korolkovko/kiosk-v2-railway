#!/bin/bash
# rollback.sh
# Emergency rollback script for KIOSK application
# Reverts to previous git commit and redeploys

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${RED}========================================${NC}"
echo -e "${RED}KIOSK Emergency Rollback${NC}"
echo -e "${RED}========================================${NC}"
echo ""

# Check if running from correct directory
if [ ! -f "docker-compose.yml" ]; then
    echo -e "${RED}Error: docker-compose.yml not found${NC}"
    echo "Please run this script from /opt/kiosk directory"
    exit 1
fi

# Show current commit
echo -e "${YELLOW}Current commit:${NC}"
git log -1 --oneline
echo ""

# Show previous commits
echo -e "${YELLOW}Recent commits:${NC}"
git log -5 --oneline
echo ""

# Ask for confirmation
read -p "Enter the commit hash to rollback to (or 'HEAD~1' for previous): " COMMIT_HASH

if [ -z "$COMMIT_HASH" ]; then
    echo -e "${RED}Error: Commit hash cannot be empty${NC}"
    exit 1
fi

echo ""
echo -e "${RED}⚠️  WARNING: This will:${NC}"
echo "  1. Revert code to commit: $COMMIT_HASH"
echo "  2. Rebuild and restart all containers"
echo "  3. Run database migrations (if any)"
echo ""
read -p "Are you sure you want to rollback? (type 'ROLLBACK' to confirm): " CONFIRM

if [ "$CONFIRM" != "ROLLBACK" ]; then
    echo "Rollback cancelled."
    exit 0
fi

echo ""
echo -e "${YELLOW}Step 1: Creating backup before rollback...${NC}"
BACKUP_DIR="/opt/kiosk/backups"
mkdir -p "$BACKUP_DIR"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
docker compose exec -T postgres pg_dump -U kiosk_user kiosk_db > "${BACKUP_DIR}/pre_rollback_${TIMESTAMP}.sql" || {
    echo -e "${RED}Failed to create backup${NC}"
    exit 1
}
gzip "${BACKUP_DIR}/pre_rollback_${TIMESTAMP}.sql"
echo -e "${GREEN}✓ Backup created: pre_rollback_${TIMESTAMP}.sql.gz${NC}"
echo ""

echo -e "${YELLOW}Step 2: Reverting code to commit: $COMMIT_HASH${NC}"
git reset --hard "$COMMIT_HASH" || {
    echo -e "${RED}Failed to revert code${NC}"
    exit 1
}
echo -e "${GREEN}✓ Code reverted${NC}"
echo ""

echo -e "${YELLOW}Step 3: Rebuilding containers...${NC}"
docker compose -f docker-compose.yml \
               -f docker-compose.prod.yml \
               --env-file /opt/kiosk/secrets/.env.prod \
               up -d --build || {
    echo -e "${RED}Failed to rebuild containers${NC}"
    exit 1
}
echo -e "${GREEN}✓ Containers rebuilt${NC}"
echo ""

echo -e "${YELLOW}Step 4: Running migrations...${NC}"
docker compose exec -T backend alembic upgrade head || {
    echo -e "${YELLOW}Warning: Migrations may have failed (check logs)${NC}"
}
echo -e "${GREEN}✓ Migrations attempted${NC}"
echo ""

echo -e "${YELLOW}Step 5: Checking service status...${NC}"
docker compose ps
echo ""

echo -e "${YELLOW}Step 6: Testing endpoints...${NC}"
sleep 5
if curl -f -s http://localhost:8001/health > /dev/null; then
    echo -e "${GREEN}✓ Backend health check passed${NC}"
else
    echo -e "${RED}✗ Backend health check failed${NC}"
fi
echo ""

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Rollback completed!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "Rolled back to: $(git log -1 --oneline)"
echo "Backup location: ${BACKUP_DIR}/pre_rollback_${TIMESTAMP}.sql.gz"
echo ""
echo "If issues persist:"
echo "  1. Check logs: docker compose logs -f"
echo "  2. Restore backup if needed"
echo "  3. Contact support"
echo ""
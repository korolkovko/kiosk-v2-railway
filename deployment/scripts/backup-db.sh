#!/bin/bash
# backup-db.sh
# Database backup script for KIOSK application
# Creates timestamped PostgreSQL backups

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
BACKUP_DIR="/opt/kiosk/backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="kiosk_db_backup_${TIMESTAMP}.sql"
RETENTION_DAYS=7  # Keep backups for 7 days

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}KIOSK Database Backup${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# Create backup directory if it doesn't exist
mkdir -p "$BACKUP_DIR"

# Check if PostgreSQL container is running
if ! docker compose ps postgres | grep -q "Up"; then
    echo -e "${RED}Error: PostgreSQL container is not running${NC}"
    echo "Start it with: docker compose up -d postgres"
    exit 1
fi

echo -e "${YELLOW}Creating backup: ${BACKUP_FILE}${NC}"

# Create backup
docker compose exec -T postgres pg_dump -U kiosk_user kiosk_db > "${BACKUP_DIR}/${BACKUP_FILE}" || {
    echo -e "${RED}Failed to create backup${NC}"
    exit 1
}

# Compress backup
gzip "${BACKUP_DIR}/${BACKUP_FILE}" || {
    echo -e "${RED}Failed to compress backup${NC}"
    exit 1
}

BACKUP_FILE_GZ="${BACKUP_FILE}.gz"
BACKUP_SIZE=$(du -h "${BACKUP_DIR}/${BACKUP_FILE_GZ}" | cut -f1)

echo -e "${GREEN}✓ Backup created: ${BACKUP_FILE_GZ} (${BACKUP_SIZE})${NC}"
echo ""

# Clean up old backups
echo -e "${YELLOW}Cleaning up backups older than ${RETENTION_DAYS} days...${NC}"
find "$BACKUP_DIR" -name "kiosk_db_backup_*.sql.gz" -mtime +${RETENTION_DAYS} -delete
REMAINING_BACKUPS=$(ls -1 "$BACKUP_DIR"/kiosk_db_backup_*.sql.gz 2>/dev/null | wc -l)
echo -e "${GREEN}✓ Cleanup complete. ${REMAINING_BACKUPS} backups remaining${NC}"
echo ""

# List recent backups
echo -e "${YELLOW}Recent backups:${NC}"
ls -lh "$BACKUP_DIR"/kiosk_db_backup_*.sql.gz 2>/dev/null | tail -5 || echo "No backups found"
echo ""

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Backup completed successfully!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "Backup location: ${BACKUP_DIR}/${BACKUP_FILE_GZ}"
echo ""
echo "To restore this backup:"
echo "  gunzip ${BACKUP_DIR}/${BACKUP_FILE_GZ}"
echo "  docker compose exec -T postgres psql -U kiosk_user -d kiosk_db < ${BACKUP_DIR}/${BACKUP_FILE}"
echo ""
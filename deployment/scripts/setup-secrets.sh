#!/bin/bash
# setup-secrets.sh
# Initialize production secrets for KIOSK application
# Run this ONCE on production server after cloning repository

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}KIOSK Production Secrets Setup${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# Check if .env.prod.example exists
if [ ! -f ".env.prod.example" ]; then
    echo -e "${RED}Error: .env.prod.example not found${NC}"
    echo "Please run this script from /opt/kiosk directory"
    exit 1
fi

# Check if secrets already exist
if [ -f "/opt/kiosk/secrets/.env.prod" ]; then
    echo -e "${YELLOW}Warning: /opt/kiosk/secrets/.env.prod already exists${NC}"
    read -p "Do you want to regenerate secrets? This will invalidate all current sessions (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Aborted. Existing secrets preserved."
        exit 0
    fi
fi

echo -e "${YELLOW}Step 1: Creating secrets directory...${NC}"
sudo mkdir -p /opt/kiosk/secrets
sudo chown $USER:$USER /opt/kiosk/secrets
chmod 700 /opt/kiosk/secrets
echo -e "${GREEN}✓ Directory created${NC}"
echo ""

echo -e "${YELLOW}Step 2: Generating random secrets...${NC}"
SECRET_KEY=$(openssl rand -hex 32)
JWT_SECRET_KEY=$(openssl rand -hex 32)
KIOSK_JWT_SECRET_KEY=$(openssl rand -hex 32)
DB_PASSWORD=$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-25)
echo -e "${GREEN}✓ Secrets generated${NC}"
echo ""

echo -e "${YELLOW}Step 3: Creating .env.prod file...${NC}"
cp .env.prod.example /opt/kiosk/secrets/.env.prod

# Replace placeholders
sed -i "s/GENERATE_RANDOM_64_CHAR_HEX_DIFFERENT_FROM_DEV/$SECRET_KEY/g" /opt/kiosk/secrets/.env.prod
sed -i "s/JWT_SECRET_KEY=GENERATE_RANDOM_64_CHAR_HEX_DIFFERENT_FROM_DEV/JWT_SECRET_KEY=$JWT_SECRET_KEY/g" /opt/kiosk/secrets/.env.prod
sed -i "s/KIOSK_JWT_SECRET_KEY=GENERATE_RANDOM_64_CHAR_HEX_DIFFERENT_FROM_DEV/KIOSK_JWT_SECRET_KEY=$KIOSK_JWT_SECRET_KEY/g" /opt/kiosk/secrets/.env.prod
sed -i "s/GENERATE_STRONG_PASSWORD_25_CHARS/$DB_PASSWORD/g" /opt/kiosk/secrets/.env.prod

echo -e "${GREEN}✓ File created${NC}"
echo ""

echo -e "${YELLOW}Step 4: Securing file permissions...${NC}"
chmod 600 /opt/kiosk/secrets/.env.prod
echo -e "${GREEN}✓ Permissions set (600)${NC}"
echo ""

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}⚠️  IMPORTANT: SAVE THESE SECRETS!${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
echo -e "${YELLOW}Copy these to your password manager:${NC}"
echo ""
echo "SECRET_KEY=$SECRET_KEY"
echo "JWT_SECRET_KEY=$JWT_SECRET_KEY"
echo "KIOSK_JWT_SECRET_KEY=$KIOSK_JWT_SECRET_KEY"
echo "DB_PASSWORD=$DB_PASSWORD"
echo ""
echo -e "${RED}⚠️  You will NOT see these again!${NC}"
echo ""
read -p "Press Enter after saving these secrets to continue..."
echo ""

echo -e "${YELLOW}Step 5: Configuring domain...${NC}"
read -p "Enter your domain (e.g., kiosk.yourdomain.com): " DOMAIN

if [ -z "$DOMAIN" ]; then
    echo -e "${RED}Error: Domain cannot be empty${NC}"
    exit 1
fi

# Update ALLOWED_ORIGINS in .env.prod
sed -i "s/kiosk.yourdomain.com/$DOMAIN/g" /opt/kiosk/secrets/.env.prod
sed -i "s/yourdomain.com/$DOMAIN/g" /opt/kiosk/secrets/.env.prod

echo -e "${GREEN}✓ Domain configured: $DOMAIN${NC}"
echo ""

echo -e "${YELLOW}Step 6: Verifying configuration...${NC}"
if grep -q "GENERATE_RANDOM" /opt/kiosk/secrets/.env.prod; then
    echo -e "${RED}Error: Some placeholders were not replaced${NC}"
    exit 1
fi
echo -e "${GREEN}✓ All placeholders replaced${NC}"
echo ""

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Secrets setup completed!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "Next steps:"
echo "  1. Update nginx config with your domain"
echo "  2. Obtain SSL certificate (Let's Encrypt)"
echo "  3. Deploy application: ./deployment/scripts/deploy-prod.sh"
echo ""
echo "Secrets location: /opt/kiosk/secrets/.env.prod"
echo "Permissions: $(ls -l /opt/kiosk/secrets/.env.prod | awk '{print $1}')"
echo ""
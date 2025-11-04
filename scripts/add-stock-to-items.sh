#!/bin/bash
# add-stock-to-items.sh
# Add stock to all items in the KIOSK application
# This script adds a specified quantity to each item's stock

set -e  # Exit on any error

# ============================================
# CONFIGURATION SECTION
# ============================================

# Backend API URL
API_URL="http://localhost:8000"

# Admin credentials
ADMIN_USERNAME="admin"
ADMIN_PASSWORD="Password123"

# Stock quantity to add to each item
STOCK_QUANTITY=30

# ============================================
# END OF CONFIGURATION
# ============================================

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}KIOSK Stock Replenishment${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "${BLUE}Configuration:${NC}"
echo -e "  API URL: ${API_URL}"
echo -e "  Stock quantity per item: ${STOCK_QUANTITY}"
echo ""

# ============================================
# Step 1: Login and get access token
# ============================================
echo -e "${YELLOW}Step 1: Logging in as admin...${NC}"

LOGIN_RESPONSE=$(curl -s -X POST "${API_URL}/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d "{\"username\":\"${ADMIN_USERNAME}\",\"password\":\"${ADMIN_PASSWORD}\"}")

# Check if login was successful
if echo "$LOGIN_RESPONSE" | grep -q "access_token"; then
    ACCESS_TOKEN=$(echo "$LOGIN_RESPONSE" | grep -o '"access_token":"[^"]*' | cut -d'"' -f4)
    echo -e "${GREEN}✓ Login successful${NC}"
else
    echo -e "${RED}✗ Login failed${NC}"
    echo "Response: $LOGIN_RESPONSE"
    exit 1
fi

echo ""

# ============================================
# Step 2: Get all items
# ============================================
echo -e "${YELLOW}Step 2: Fetching all items...${NC}"

ITEMS_RESPONSE=$(curl -s -X GET "${API_URL}/api/v1/getallitemlive/" \
  -H "Authorization: Bearer ${ACCESS_TOKEN}")

# Extract item IDs from response
ITEM_IDS=$(echo "$ITEMS_RESPONSE" | grep -o '"item_id":[0-9]*' | cut -d':' -f2 | sort -n)

if [ -z "$ITEM_IDS" ]; then
    echo -e "${RED}✗ No items found${NC}"
    exit 1
fi

TOTAL_ITEMS=$(echo "$ITEM_IDS" | wc -l | xargs)
echo -e "${GREEN}✓ Found ${TOTAL_ITEMS} items${NC}"
echo ""

# ============================================
# Step 3: Add stock to each item
# ============================================
echo -e "${YELLOW}Step 3: Adding stock to items...${NC}"
echo ""

TOTAL_SUCCESS=0
TOTAL_FAILED=0

for ITEM_ID in $ITEM_IDS; do
    # Create JSON payload
    PAYLOAD=$(cat <<EOF
{
  "item_id": ${ITEM_ID},
  "quantity": ${STOCK_QUANTITY}
}
EOF
)

    # Add stock via API
    RESPONSE=$(curl -s -X POST "${API_URL}/api/v1/replenish-or-remove/" \
      -H "Content-Type: application/json" \
      -H "Authorization: Bearer ${ACCESS_TOKEN}" \
      -d "$PAYLOAD")

    # Check if stock was added successfully
    if echo "$RESPONSE" | grep -q '"item_id"'; then
        # Extract stock quantity from response
        STOCK_QTY=$(echo "$RESPONSE" | grep -o '"stock_quantity":[0-9]*' | cut -d':' -f2)
        UNIT_NAME=$(echo "$RESPONSE" | grep -o '"unit_name_eng":"[^"]*' | cut -d'"' -f4)
        echo -e "  ${GREEN}✓${NC} Item ID ${ITEM_ID}: Stock now ${STOCK_QTY} ${UNIT_NAME}"
        TOTAL_SUCCESS=$((TOTAL_SUCCESS + 1))
    else
        echo -e "  ${RED}✗${NC} Failed to add stock to item ID: ${ITEM_ID}"
        echo "     Response: $RESPONSE"
        TOTAL_FAILED=$((TOTAL_FAILED + 1))
    fi
done

echo ""

# ============================================
# Summary
# ============================================
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Stock Replenishment Summary${NC}"
echo -e "${GREEN}========================================${NC}"
echo -e "Total items processed: ${TOTAL_ITEMS}"
echo -e "Successfully updated: ${GREEN}${TOTAL_SUCCESS}${NC}"
echo -e "Failed: ${RED}${TOTAL_FAILED}${NC}"
echo ""

if [ $TOTAL_FAILED -eq 0 ]; then
    echo -e "${GREEN}✓ All items updated successfully!${NC}"
else
    echo -e "${YELLOW}⚠ Some items failed to update. Check the output above for details.${NC}"
fi

echo ""
echo -e "Each item now has ${STOCK_QUANTITY} units added to stock."
echo ""

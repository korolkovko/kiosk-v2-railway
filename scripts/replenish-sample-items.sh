#!/bin/bash
# Script to replenish stock for all created items with random quantities (10-15)

TOKEN="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoyLCJ1c2VybmFtZSI6ImFkbWluIiwicm9sZV9uYW1lIjoiYWRtaW4iLCJleHAiOjE3NTkyNjY1MDYsImlhdCI6MTc1OTI2NDcwNiwidHlwZSI6ImFjY2Vzc190b2tlbiJ9.zoLqbn4gEu5Fkegrv5PnJXobSllHJJn4nn6ledBwqMM"
API_URL="http://localhost:8000/api/v1/replenish-or-remove/"

echo "Replenishing stock for all items..."
echo ""

# Item IDs 1-10
for item_id in {1..10}; do
    # Generate random quantity between 10 and 15
    quantity=$((RANDOM % 6 + 10))

    echo "Replenishing item $item_id with $quantity units..."

    curl -s -X POST "$API_URL" \
      -H "Content-Type: application/json" \
      -H "Authorization: Bearer $TOKEN" \
      -d "{\"item_id\":$item_id,\"quantity\":$quantity}" | jq -r '"  ✅ Item \(.item_id): \(.stock_quantity) units in stock"'

done

echo ""
echo "All items replenished successfully!"

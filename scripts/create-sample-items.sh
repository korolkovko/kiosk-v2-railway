#!/bin/bash
# Script to create random menu items via API

TOKEN="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoyLCJ1c2VybmFtZSI6ImFkbWluIiwicm9sZV9uYW1lIjoiYWRtaW4iLCJleHAiOjE3NTkyNjY1MDYsImlhdCI6MTc1OTI2NDcwNiwidHlwZSI6ImFjY2Vzc190b2tlbiJ9.zoLqbn4gEu5Fkegrv5PnJXobSllHJJn4nn6ledBwqMM"
API_URL="http://localhost:8000/api/v1/addliveitem/"

# Function to calculate VAT (20%)
calculate_prices() {
    local gross_kopeks=$1
    local gross=$(echo "scale=2; $gross_kopeks / 100" | bc)
    local net=$(echo "scale=2; $gross / 1.20" | bc)
    local vat=$(echo "scale=2; $gross - $net" | bc)
    echo "$net:$vat:$gross"
}

# Drinks category (7 items)
echo "Creating drinks..."

# 1. Coffee
GROSS_KOPEKS=25000
PRICES=$(calculate_prices $GROSS_KOPEKS)
NET=$(echo $PRICES | cut -d: -f1)
VAT=$(echo $PRICES | cut -d: -f2)
GROSS=$(echo $PRICES | cut -d: -f3)

curl -X POST "$API_URL" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d "{\"name_ru\":\"Кофе американо\",\"name_eng\":\"Americano Coffee\",\"description_ru\":\"Классический американо с горячей водой и эспрессо\",\"description_eng\":\"Classic americano with hot water and espresso\",\"unit_measure_name_eng\":\"piece\",\"food_category_name\":\"drinks\",\"day_category_name\":\"allday\",\"price_net\":\"$NET\",\"vat_rate\":\"20.00\",\"vat_amount\":\"$VAT\",\"price_gross\":\"$GROSS\",\"is_active\":true}"

# 2. Tea
GROSS_KOPEKS=30000
PRICES=$(calculate_prices $GROSS_KOPEKS)
NET=$(echo $PRICES | cut -d: -f1)
VAT=$(echo $PRICES | cut -d: -f2)
GROSS=$(echo $PRICES | cut -d: -f3)

curl -X POST "$API_URL" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d "{\"name_ru\":\"Чай зеленый\",\"name_eng\":\"Green Tea\",\"description_ru\":\"Свежезаваренный зеленый чай с жасмином\",\"description_eng\":\"Freshly brewed green tea with jasmine\",\"unit_measure_name_eng\":\"piece\",\"food_category_name\":\"drinks\",\"day_category_name\":\"allday\",\"price_net\":\"$NET\",\"vat_rate\":\"20.00\",\"vat_amount\":\"$VAT\",\"price_gross\":\"$GROSS\",\"is_active\":true}"

# 3. Juice
GROSS_KOPEKS=35000
PRICES=$(calculate_prices $GROSS_KOPEKS)
NET=$(echo $PRICES | cut -d: -f1)
VAT=$(echo $PRICES | cut -d: -f2)
GROSS=$(echo $PRICES | cut -d: -f3)

curl -X POST "$API_URL" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d "{\"name_ru\":\"Апельсиновый сок\",\"name_eng\":\"Orange Juice\",\"description_ru\":\"Свежевыжатый апельсиновый сок из спелых апельсинов\",\"description_eng\":\"Freshly squeezed orange juice from ripe oranges\",\"unit_measure_name_eng\":\"piece\",\"food_category_name\":\"drinks\",\"day_category_name\":\"allday\",\"price_net\":\"$NET\",\"vat_rate\":\"20.00\",\"vat_amount\":\"$VAT\",\"price_gross\":\"$GROSS\",\"is_active\":true}"

# 4. Latte
GROSS_KOPEKS=40000
PRICES=$(calculate_prices $GROSS_KOPEKS)
NET=$(echo $PRICES | cut -d: -f1)
VAT=$(echo $PRICES | cut -d: -f2)
GROSS=$(echo $PRICES | cut -d: -f3)

curl -X POST "$API_URL" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d "{\"name_ru\":\"Латте\",\"name_eng\":\"Latte\",\"description_ru\":\"Нежный кофейный напиток с молочной пенкой\",\"description_eng\":\"Smooth coffee drink with milk foam\",\"unit_measure_name_eng\":\"piece\",\"food_category_name\":\"drinks\",\"day_category_name\":\"allday\",\"price_net\":\"$NET\",\"vat_rate\":\"20.00\",\"vat_amount\":\"$VAT\",\"price_gross\":\"$GROSS\",\"is_active\":true}"

# 5. Cappuccino
GROSS_KOPEKS=38000
PRICES=$(calculate_prices $GROSS_KOPEKS)
NET=$(echo $PRICES | cut -d: -f1)
VAT=$(echo $PRICES | cut -d: -f2)
GROSS=$(echo $PRICES | cut -d: -f3)

curl -X POST "$API_URL" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d "{\"name_ru\":\"Капучино\",\"name_eng\":\"Cappuccino\",\"description_ru\":\"Итальянский кофе с густой молочной пеной\",\"description_eng\":\"Italian coffee with thick milk foam\",\"unit_measure_name_eng\":\"piece\",\"food_category_name\":\"drinks\",\"day_category_name\":\"allday\",\"price_net\":\"$NET\",\"vat_rate\":\"20.00\",\"vat_amount\":\"$VAT\",\"price_gross\":\"$GROSS\",\"is_active\":true}"

# 6. Mineral Water
GROSS_KOPEKS=20000
PRICES=$(calculate_prices $GROSS_KOPEKS)
NET=$(echo $PRICES | cut -d: -f1)
VAT=$(echo $PRICES | cut -d: -f2)
GROSS=$(echo $PRICES | cut -d: -f3)

curl -X POST "$API_URL" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d "{\"name_ru\":\"Минеральная вода\",\"name_eng\":\"Mineral Water\",\"description_ru\":\"Газированная минеральная вода из природных источников\",\"description_eng\":\"Sparkling mineral water from natural springs\",\"unit_measure_name_eng\":\"piece\",\"food_category_name\":\"drinks\",\"day_category_name\":\"allday\",\"price_net\":\"$NET\",\"vat_rate\":\"20.00\",\"vat_amount\":\"$VAT\",\"price_gross\":\"$GROSS\",\"is_active\":true}"

# 7. Smoothie
GROSS_KOPEKS=45000
PRICES=$(calculate_prices $GROSS_KOPEKS)
NET=$(echo $PRICES | cut -d: -f1)
VAT=$(echo $PRICES | cut -d: -f2)
GROSS=$(echo $PRICES | cut -d: -f3)

curl -X POST "$API_URL" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d "{\"name_ru\":\"Смузи ягодный\",\"name_eng\":\"Berry Smoothie\",\"description_ru\":\"Полезный смузи из свежих ягод и йогурта\",\"description_eng\":\"Healthy smoothie from fresh berries and yogurt\",\"unit_measure_name_eng\":\"piece\",\"food_category_name\":\"drinks\",\"day_category_name\":\"allday\",\"price_net\":\"$NET\",\"vat_rate\":\"20.00\",\"vat_amount\":\"$VAT\",\"price_gross\":\"$GROSS\",\"is_active\":true}"

echo ""
echo "Creating main dishes..."

# Main category (2 items)
# 1. Burger
GROSS_KOPEKS=50000
PRICES=$(calculate_prices $GROSS_KOPEKS)
NET=$(echo $PRICES | cut -d: -f1)
VAT=$(echo $PRICES | cut -d: -f2)
GROSS=$(echo $PRICES | cut -d: -f3)

curl -X POST "$API_URL" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d "{\"name_ru\":\"Бургер классический\",\"name_eng\":\"Classic Burger\",\"description_ru\":\"Сочный бургер с говяжьей котлетой, салатом и томатами\",\"description_eng\":\"Juicy burger with beef patty, lettuce and tomatoes\",\"unit_measure_name_eng\":\"piece\",\"food_category_name\":\"main\",\"day_category_name\":\"lunch\",\"price_net\":\"$NET\",\"vat_rate\":\"20.00\",\"vat_amount\":\"$VAT\",\"price_gross\":\"$GROSS\",\"is_active\":true}"

# 2. Pasta
GROSS_KOPEKS=48000
PRICES=$(calculate_prices $GROSS_KOPEKS)
NET=$(echo $PRICES | cut -d: -f1)
VAT=$(echo $PRICES | cut -d: -f2)
GROSS=$(echo $PRICES | cut -d: -f3)

curl -X POST "$API_URL" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d "{\"name_ru\":\"Паста карбонара\",\"name_eng\":\"Pasta Carbonara\",\"description_ru\":\"Итальянская паста с беконом, сливками и сыром пармезан\",\"description_eng\":\"Italian pasta with bacon, cream and parmesan cheese\",\"unit_measure_name_eng\":\"piece\",\"food_category_name\":\"main\",\"day_category_name\":\"dinner\",\"price_net\":\"$NET\",\"vat_rate\":\"20.00\",\"vat_amount\":\"$VAT\",\"price_gross\":\"$GROSS\",\"is_active\":true}"

echo ""
echo "Creating sides..."

# Sides category (1 item)
# 1. French Fries
GROSS_KOPEKS=28000
PRICES=$(calculate_prices $GROSS_KOPEKS)
NET=$(echo $PRICES | cut -d: -f1)
VAT=$(echo $PRICES | cut -d: -f2)
GROSS=$(echo $PRICES | cut -d: -f3)

curl -X POST "$API_URL" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d "{\"name_ru\":\"Картофель фри\",\"name_eng\":\"French Fries\",\"description_ru\":\"Хрустящий золотистый картофель фри с морской солью\",\"description_eng\":\"Crispy golden french fries with sea salt\",\"unit_measure_name_eng\":\"piece\",\"food_category_name\":\"sides\",\"day_category_name\":\"allday\",\"price_net\":\"$NET\",\"vat_rate\":\"20.00\",\"vat_amount\":\"$VAT\",\"price_gross\":\"$GROSS\",\"is_active\":true}"

echo ""
echo "All items created successfully!"

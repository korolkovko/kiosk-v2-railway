#!/bin/bash
# seed-items.sh
# Create sample menu items for KIOSK application
# This script creates items across multiple categories with randomized prices

set -e  # Exit on any error

# ============================================
# CONFIGURATION SECTION
# ============================================

# Backend API URL
API_URL="http://localhost:8000"

# Admin credentials
ADMIN_USERNAME="admin"
ADMIN_PASSWORD="Password123"

# Categories to populate (space-separated)
# Note: These categories must already exist in the database
CATEGORIES=("hotdrinks" "coldrinks" "main" "sides")

# Number of items to create per category
# Total items will be: ITEMS_PER_CATEGORY * number of categories
# For 50 total items across 4 categories: 50 / 4 = 12.5, so use 13 per category (52 total)
ITEMS_PER_CATEGORY=13

# Price range in kopecks (1 ruble = 100 kopecks)
# Examples: 20000 kopecks = 200 rubles, 50000 kopecks = 500 rubles
MIN_PRICE_KOPECKS=20000
MAX_PRICE_KOPECKS=50000

# VAT rate (as string, e.g., "20.0" for 20%)
VAT_RATE="20.0"

# Unit of measure (must exist in database)
UNIT_MEASURE="piece"

# Item defaults
DEFAULT_IS_ACTIVE=true
DEFAULT_IS_PROMOTED=false
DEFAULT_STOP_LIST=false

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
echo -e "${GREEN}KIOSK Menu Items Seeder${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "${BLUE}Configuration:${NC}"
echo -e "  API URL: ${API_URL}"
echo -e "  Categories: ${CATEGORIES[@]}"
echo -e "  Items per category: ${ITEMS_PER_CATEGORY}"
echo -e "  Price range: ${MIN_PRICE_KOPECKS}-${MAX_PRICE_KOPECKS} kopecks"
echo -e "  VAT rate: ${VAT_RATE}%"
echo ""

# Function to calculate random price
random_price() {
    echo $(( RANDOM % (MAX_PRICE_KOPECKS - MIN_PRICE_KOPECKS + 1) + MIN_PRICE_KOPECKS ))
}

# Function to calculate VAT amount
calculate_vat() {
    local gross_price=$1
    # VAT = (gross_price * vat_rate) / (100 + vat_rate)
    # For 20% VAT: VAT = gross_price * 20 / 120
    echo $(( gross_price * 20 / 120 ))
}

# Function to calculate net price
calculate_net() {
    local gross_price=$1
    local vat_amount=$2
    echo $(( gross_price - vat_amount ))
}

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
# Step 2: Item name templates
# ============================================

# Hot Drinks
HOTDRINKS_NAMES_RU=(
    "Эспрессо"
    "Американо"
    "Капучино"
    "Латте"
    "Флэт Уайт"
    "Макиато"
    "Мокко"
    "Горячий шоколад"
    "Чай черный"
    "Чай зеленый"
    "Раф кофе"
    "Матча латте"
    "Какао"
)

HOTDRINKS_NAMES_EN=(
    "Espresso"
    "Americano"
    "Cappuccino"
    "Latte"
    "Flat White"
    "Macchiato"
    "Mocha"
    "Hot Chocolate"
    "Black Tea"
    "Green Tea"
    "Raf Coffee"
    "Matcha Latte"
    "Cocoa"
)

HOTDRINKS_DESC_RU=(
    "Классический итальянский эспрессо"
    "Двойной эспрессо с горячей водой"
    "Эспрессо с молочной пенкой"
    "Эспрессо с молоком"
    "Эспрессо с бархатистым молоком"
    "Эспрессо с капелькой молока"
    "Эспрессо с шоколадом и молоком"
    "Насыщенный горячий шоколад"
    "Крепкий черный чай"
    "Освежающий зеленый чай"
    "Кофе со сливками и ванилью"
    "Зеленый чай матча с молоком"
    "Классическое какао на молоке"
)

HOTDRINKS_DESC_EN=(
    "Classic Italian espresso"
    "Double espresso with hot water"
    "Espresso with milk foam"
    "Espresso with steamed milk"
    "Espresso with velvety milk"
    "Espresso with a dash of milk"
    "Espresso with chocolate and milk"
    "Rich hot chocolate"
    "Strong black tea"
    "Refreshing green tea"
    "Coffee with cream and vanilla"
    "Matcha green tea with milk"
    "Classic cocoa with milk"
)

# Cold Drinks
COLDDRINKS_NAMES_RU=(
    "Кола"
    "Спрайт"
    "Фанта"
    "Вода негазированная"
    "Вода газированная"
    "Сок апельсиновый"
    "Сок яблочный"
    "Лимонад"
    "Холодный чай"
    "Смузи ягодный"
    "Милкшейк ванильный"
    "Милкшейк шоколадный"
    "Айс латте"
)

COLDDRINKS_NAMES_EN=(
    "Cola"
    "Sprite"
    "Fanta"
    "Still Water"
    "Sparkling Water"
    "Orange Juice"
    "Apple Juice"
    "Lemonade"
    "Iced Tea"
    "Berry Smoothie"
    "Vanilla Milkshake"
    "Chocolate Milkshake"
    "Iced Latte"
)

COLDDRINKS_DESC_RU=(
    "Классическая кола"
    "Освежающий лимонный напиток"
    "Апельсиновый газированный напиток"
    "Минеральная вода без газа"
    "Минеральная вода с газом"
    "Свежевыжатый апельсиновый сок"
    "Натуральный яблочный сок"
    "Домашний лимонад"
    "Холодный черный чай"
    "Смузи из свежих ягод"
    "Молочный коктейль с ванилью"
    "Молочный коктейль с шоколадом"
    "Холодный кофе с молоком"
)

COLDDRINKS_DESC_EN=(
    "Classic cola"
    "Refreshing lemon drink"
    "Orange carbonated drink"
    "Still mineral water"
    "Sparkling mineral water"
    "Freshly squeezed orange juice"
    "Natural apple juice"
    "Homemade lemonade"
    "Iced black tea"
    "Fresh berry smoothie"
    "Vanilla milk shake"
    "Chocolate milk shake"
    "Iced coffee with milk"
)

# Main Dishes
MAIN_NAMES_RU=(
    "Бургер классический"
    "Чизбургер"
    "Бургер с беконом"
    "Куриный бургер"
    "Вегетарианский бургер"
    "Пицца Маргарита"
    "Пицца Пепперони"
    "Паста Карбонара"
    "Паста Болоньезе"
    "Лазанья"
    "Ризотто с грибами"
    "Стейк из говядины"
    "Филе лосося"
)

MAIN_NAMES_EN=(
    "Classic Burger"
    "Cheeseburger"
    "Bacon Burger"
    "Chicken Burger"
    "Veggie Burger"
    "Margherita Pizza"
    "Pepperoni Pizza"
    "Carbonara Pasta"
    "Bolognese Pasta"
    "Lasagna"
    "Mushroom Risotto"
    "Beef Steak"
    "Salmon Fillet"
)

MAIN_DESC_RU=(
    "Говяжья котлета с овощами"
    "Бургер с сыром чеддер"
    "Бургер с хрустящим беконом"
    "Сочная куриная грудка"
    "Котлета из бобовых с овощами"
    "Томатный соус, моцарелла, базилик"
    "Томатный соус, моцарелла, пепперони"
    "Паста со сливочным соусом и беконом"
    "Паста с мясным томатным соусом"
    "Слоеная запеканка с мясом"
    "Кремовое ризотто с лесными грибами"
    "Сочный стейк из мраморной говядины"
    "Филе лосося на гриле"
)

MAIN_DESC_EN=(
    "Beef patty with vegetables"
    "Burger with cheddar cheese"
    "Burger with crispy bacon"
    "Juicy chicken breast"
    "Bean patty with vegetables"
    "Tomato sauce, mozzarella, basil"
    "Tomato sauce, mozzarella, pepperoni"
    "Pasta with creamy sauce and bacon"
    "Pasta with meat tomato sauce"
    "Layered baked pasta with meat"
    "Creamy risotto with wild mushrooms"
    "Juicy marbled beef steak"
    "Grilled salmon fillet"
)

# Sides
SIDES_NAMES_RU=(
    "Картофель фри"
    "Картофельные дольки"
    "Луковые кольца"
    "Куриные наггетсы"
    "Куриные крылышки"
    "Салат Цезарь"
    "Салат Греческий"
    "Овощи гриль"
    "Чесночные гренки"
    "Моцарелла стикс"
    "Картофельное пюре"
    "Кукуруза гриль"
    "Соус сырный"
)

SIDES_NAMES_EN=(
    "French Fries"
    "Potato Wedges"
    "Onion Rings"
    "Chicken Nuggets"
    "Chicken Wings"
    "Caesar Salad"
    "Greek Salad"
    "Grilled Vegetables"
    "Garlic Bread"
    "Mozzarella Sticks"
    "Mashed Potatoes"
    "Grilled Corn"
    "Cheese Sauce"
)

SIDES_DESC_RU=(
    "Хрустящий картофель фри"
    "Запеченные картофельные дольки"
    "Луковые кольца в кляре"
    "Куриные кусочки в панировке"
    "Острые куриные крылышки"
    "Салат с курицей и соусом Цезарь"
    "Свежие овощи с сыром фета"
    "Овощи на гриле"
    "Хрустящие гренки с чесноком"
    "Палочки из моцареллы в панировке"
    "Нежное картофельное пюре"
    "Кукуруза на гриле с маслом"
    "Сливочный сырный соус"
)

SIDES_DESC_EN=(
    "Crispy French fries"
    "Baked potato wedges"
    "Battered onion rings"
    "Breaded chicken pieces"
    "Spicy chicken wings"
    "Salad with chicken and Caesar dressing"
    "Fresh vegetables with feta cheese"
    "Grilled vegetables"
    "Crispy garlic bread"
    "Breaded mozzarella sticks"
    "Creamy mashed potatoes"
    "Grilled corn with butter"
    "Creamy cheese sauce"
)

# ============================================
# Step 3: Create items for each category
# ============================================

TOTAL_CREATED=0
TOTAL_FAILED=0

for CATEGORY in "${CATEGORIES[@]}"; do
    echo -e "${YELLOW}Creating items for category: ${CATEGORY}${NC}"

    # Select appropriate item arrays based on category
    case "$CATEGORY" in
        "hotdrinks")
            NAMES_RU=("${HOTDRINKS_NAMES_RU[@]}")
            NAMES_EN=("${HOTDRINKS_NAMES_EN[@]}")
            DESC_RU=("${HOTDRINKS_DESC_RU[@]}")
            DESC_EN=("${HOTDRINKS_DESC_EN[@]}")
            ;;
        "coldrinks")
            NAMES_RU=("${COLDDRINKS_NAMES_RU[@]}")
            NAMES_EN=("${COLDDRINKS_NAMES_EN[@]}")
            DESC_RU=("${COLDDRINKS_DESC_RU[@]}")
            DESC_EN=("${COLDDRINKS_DESC_EN[@]}")
            ;;
        "main")
            NAMES_RU=("${MAIN_NAMES_RU[@]}")
            NAMES_EN=("${MAIN_NAMES_EN[@]}")
            DESC_RU=("${MAIN_DESC_RU[@]}")
            DESC_EN=("${MAIN_DESC_EN[@]}")
            ;;
        "sides")
            NAMES_RU=("${SIDES_NAMES_RU[@]}")
            NAMES_EN=("${SIDES_NAMES_EN[@]}")
            DESC_RU=("${SIDES_DESC_RU[@]}")
            DESC_EN=("${SIDES_DESC_EN[@]}")
            ;;
        *)
            echo -e "${RED}Unknown category: ${CATEGORY}${NC}"
            continue
            ;;
    esac

    # Create items
    for i in $(seq 0 $((ITEMS_PER_CATEGORY - 1))); do
        # Get item data
        NAME_RU="${NAMES_RU[$i]}"
        NAME_EN="${NAMES_EN[$i]}"
        DESC_RU="${DESC_RU[$i]}"
        DESC_EN="${DESC_EN[$i]}"

        # Calculate prices
        PRICE_GROSS=$(random_price)
        VAT_AMOUNT=$(calculate_vat $PRICE_GROSS)
        PRICE_NET=$(calculate_net $PRICE_GROSS $VAT_AMOUNT)

        # Create JSON payload
        PAYLOAD=$(cat <<EOF
{
  "name_ru": "${NAME_RU}",
  "name_eng": "${NAME_EN}",
  "description_ru": "${DESC_RU}",
  "description_eng": "${DESC_EN}",
  "food_category_name": "${CATEGORY}",
  "price_gross_kopecks": ${PRICE_GROSS},
  "price_net_kopecks": ${PRICE_NET},
  "vat_amount_kopecks": ${VAT_AMOUNT},
  "vat_rate": "${VAT_RATE}",
  "unit_measure_name_eng": "${UNIT_MEASURE}",
  "is_active": ${DEFAULT_IS_ACTIVE}
}
EOF
)

        # Create item via API
        RESPONSE=$(curl -s -X POST "${API_URL}/api/v1/addliveitem/" \
          -H "Content-Type: application/json" \
          -H "Authorization: Bearer ${ACCESS_TOKEN}" \
          -d "$PAYLOAD")

        # Check if creation was successful
        if echo "$RESPONSE" | grep -q '"item_id"'; then
            ITEM_ID=$(echo "$RESPONSE" | grep -o '"item_id":[0-9]*' | cut -d':' -f2)
            echo -e "  ${GREEN}✓${NC} Created: ${NAME_EN} (${PRICE_GROSS} kopecks, ID: ${ITEM_ID})"
            TOTAL_CREATED=$((TOTAL_CREATED + 1))
        else
            echo -e "  ${RED}✗${NC} Failed: ${NAME_EN}"
            echo "     Response: $RESPONSE"
            TOTAL_FAILED=$((TOTAL_FAILED + 1))
        fi
    done

    echo ""
done

# ============================================
# Summary
# ============================================
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Item Creation Summary${NC}"
echo -e "${GREEN}========================================${NC}"
echo -e "Total items created: ${GREEN}${TOTAL_CREATED}${NC}"
echo -e "Total items failed: ${RED}${TOTAL_FAILED}${NC}"
echo ""

if [ $TOTAL_FAILED -eq 0 ]; then
    echo -e "${GREEN}✓ All items created successfully!${NC}"
else
    echo -e "${YELLOW}⚠ Some items failed to create. Check the output above for details.${NC}"
fi

echo ""
echo -e "View items at: ${BLUE}${API_URL}/docs${NC}"
echo ""

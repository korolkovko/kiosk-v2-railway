#!/bin/bash
# reset-data-and-sequences.sh
# Script to delete all data and reset sequences to start from 1
# Preserves database schema/structure for fresh data start

set -euo pipefail

echo "🔄 KIOSK Database Data Reset Script"
echo "==================================="
echo ""
echo "ℹ️  This script will:"
echo "   🧹 DELETE all data from all tables"
echo "   🔢 RESET all sequences (auto-increment keys) to start from 1"
echo "   ✅ PRESERVE database schema and table structure"
echo "   ✅ PRESERVE database indexes and constraints"
echo ""
echo "⚠️  This WILL DELETE:"
echo "   🗑️  ALL user data (superadmin, admin, etc.)"
echo "   🗑️  ALL business data (orders, payments, items, etc.)"
echo "   🗑️  ALL configuration data (roles, categories, devices, etc.)"
echo "   🗑️  ALL session data"
echo ""
echo "✅ This will PRESERVE:"
echo "   📋 Database tables and their structure"
echo "   🔗 Foreign key constraints and relationships"
echo "   📊 Indexes and database performance optimizations"
echo "   🏗️  Database schema (you won't need to run migrations)"
echo ""

# Check if KIOSK containers are running
echo "🔍 Checking for KIOSK project containers..."
docker ps --format "table {{.Names}}\t{{.Status}}" | grep "kiosk_" || echo "No KIOSK containers found"

# Check specifically for KIOSK PostgreSQL container
if ! docker ps --format "{{.Names}}" | grep -q "^kiosk_postgres$"; then
    echo "❌ KIOSK PostgreSQL container 'kiosk_postgres' is not running!"
    echo ""
    echo "Available containers:"
    docker ps --format "{{.Names}}"
    echo ""
    echo "❗ This script only works with the KIOSK project database."
    echo "Please start KIOSK containers first: docker-compose up -d"
    exit 1
fi
echo "✅ Found KIOSK PostgreSQL container: kiosk_postgres"

# Check database connectivity and verify KIOSK database
echo "🔍 Verifying KIOSK database connection..."
if ! docker exec kiosk_postgres pg_isready -U kiosk_user -d kiosk_db >/dev/null 2>&1; then
    echo "❌ Cannot connect to KIOSK database (kiosk_db)!"
    echo "Please ensure the KIOSK database is running and accessible."
    exit 1
fi

# Double-check we're connecting to the right database
DB_NAME=$(docker exec kiosk_postgres psql -U kiosk_user -d kiosk_db -t -c "SELECT current_database();" 2>/dev/null | xargs)
if [ "$DB_NAME" != "kiosk_db" ]; then
    echo "❌ Connected to wrong database: $DB_NAME (expected: kiosk_db)"
    echo "❗ Safety check failed - aborting to protect other databases"
    exit 1
fi
echo "✅ Connected to KIOSK database: $DB_NAME"

echo "🔍 Current database status:"
echo "----------------------------------------"

# Get current data counts
DATA_CHECK="
SELECT
    'roles' as table_name, COUNT(*) as record_count FROM roles
UNION ALL SELECT 'users', COUNT(*) FROM users
UNION ALL SELECT 'sessions', COUNT(*) FROM sessions
UNION ALL SELECT 'known_customers', COUNT(*) FROM known_customers
UNION ALL SELECT 'orders', COUNT(*) FROM orders
UNION ALL SELECT 'payments', COUNT(*) FROM payments
UNION ALL SELECT 'items_live', COUNT(*) FROM items_live
UNION ALL SELECT 'devices', COUNT(*) FROM devices
UNION ALL SELECT 'branches', COUNT(*) FROM branches
UNION ALL SELECT 'food_categories', COUNT(*) FROM food_categories
UNION ALL SELECT 'menus', COUNT(*) FROM menus
UNION ALL SELECT 'menu_categories', COUNT(*) FROM menu_categories
UNION ALL SELECT 'menu_items', COUNT(*) FROM menu_items
ORDER BY record_count DESC;
"

echo "$DATA_CHECK" | docker exec -i kiosk_postgres psql -U kiosk_user -d kiosk_db -t | while read -r line; do
    echo "   📊 $line"
done

echo ""
echo "⚠️  CONFIRMATION REQUIRED ⚠️"
echo ""
echo "This will DELETE ALL DATA but keep the database structure intact."
echo "After this operation, you can immediately run alembic_init_and_migrate.sh"
echo "to populate default data and create fresh users."
echo ""
echo "To proceed with DATA RESET, type: RESET ALL DATA"
echo "Any other input will cancel this operation."
echo ""
echo -n "Enter confirmation: "
read -r confirmation

if [ "$confirmation" != "RESET ALL DATA" ]; then
    echo ""
    echo "❌ Operation cancelled. Data reset aborted."
    echo "✅ Your data is safe."
    exit 0
fi

echo ""
echo "🔄 Proceeding with data reset and sequence reset..."
echo "=================================================="

# Create comprehensive data reset SQL
RESET_SQL="
-- Log the reset start
SELECT 'Starting data reset at ' || CURRENT_TIMESTAMP as reset_log;

-- Disable triggers and foreign key checks temporarily for faster processing
SET session_replication_role = replica;

-- Truncate all tables in proper order (handles foreign key dependencies)
-- Using TRUNCATE for better performance and automatic sequence reset

-- First, truncate dependent tables
TRUNCATE TABLE payments CASCADE;
TRUNCATE TABLE items_live_stock_replenishment CASCADE;
TRUNCATE TABLE orders CASCADE;
TRUNCATE TABLE sessions CASCADE;
TRUNCATE TABLE fiscal_devices CASCADE;
TRUNCATE TABLE pos_terminals CASCADE;
TRUNCATE TABLE items_live_available CASCADE;

-- Then truncate main tables
TRUNCATE TABLE items_live CASCADE;
TRUNCATE TABLE users CASCADE;
TRUNCATE TABLE known_customers CASCADE;
TRUNCATE TABLE devices CASCADE;
TRUNCATE TABLE payment_methods CASCADE;

-- Truncate menu configuration tables
TRUNCATE TABLE menu_items CASCADE;
TRUNCATE TABLE menu_categories CASCADE;
TRUNCATE TABLE menus CASCADE;

-- Finally truncate reference/lookup tables
TRUNCATE TABLE branches CASCADE;
TRUNCATE TABLE food_categories CASCADE;
TRUNCATE TABLE units_of_measure CASCADE;
TRUNCATE TABLE roles CASCADE;

-- Re-enable triggers and foreign key checks
SET session_replication_role = DEFAULT;

-- Explicitly reset all sequences to start from 1
-- (TRUNCATE should handle this, but we'll be extra sure)
DO \$\$
DECLARE 
    seq_record RECORD;
    reset_count INTEGER := 0;
BEGIN 
    FOR seq_record IN 
        SELECT schemaname, sequencename 
        FROM pg_sequences 
        WHERE schemaname = 'public'
    LOOP
        EXECUTE 'ALTER SEQUENCE ' || quote_ident(seq_record.schemaname) || '.' || quote_ident(seq_record.sequencename) || ' RESTART WITH 1';
        reset_count := reset_count + 1;
        RAISE NOTICE 'Reset sequence: %.% to start from 1', seq_record.schemaname, seq_record.sequencename;
    END LOOP;
    
    RAISE NOTICE 'Total sequences reset: %', reset_count;
END \$\$;

-- Final verification - show all tables are empty
SELECT 'Data reset completed at ' || CURRENT_TIMESTAMP as reset_log;

SELECT 
    'Verification - All tables should show 0 records:' as verification_header;

-- Check that all major tables are empty
SELECT
    'roles' as table_name, COUNT(*) as record_count FROM roles
UNION ALL SELECT 'users', COUNT(*) FROM users
UNION ALL SELECT 'sessions', COUNT(*) FROM sessions
UNION ALL SELECT 'known_customers', COUNT(*) FROM known_customers
UNION ALL SELECT 'orders', COUNT(*) FROM orders
UNION ALL SELECT 'payments', COUNT(*) FROM payments
UNION ALL SELECT 'items_live', COUNT(*) FROM items_live
UNION ALL SELECT 'devices', COUNT(*) FROM devices
UNION ALL SELECT 'branches', COUNT(*) FROM branches
UNION ALL SELECT 'food_categories', COUNT(*) FROM food_categories
UNION ALL SELECT 'menus', COUNT(*) FROM menus
UNION ALL SELECT 'menu_categories', COUNT(*) FROM menu_categories
UNION ALL SELECT 'menu_items', COUNT(*) FROM menu_items
UNION ALL SELECT 'units_of_measure', COUNT(*) FROM units_of_measure
UNION ALL SELECT 'payment_methods', COUNT(*) FROM payment_methods
ORDER BY table_name;
"

echo "🗄️  Executing data reset and sequence reset..."
echo ""

# Execute the reset with detailed output
echo "$RESET_SQL" | docker exec -i kiosk_postgres psql -U kiosk_user -d kiosk_db

echo ""
echo "✅ Data reset completed successfully!"
echo ""
echo "📋 What was reset:"
echo "   🧹 ALL table data deleted (using TRUNCATE for speed)"
echo "   🔢 ALL sequences reset to start from 1"
echo "   🔄 Foreign key constraints properly handled"
echo "   ⚡ Database performance optimized during operation"
echo ""
echo "✅ What was preserved:"
echo "   📋 All database tables and their structure"
echo "   🔗 All foreign key relationships and constraints"
echo "   📊 All indexes and database optimizations"
echo "   🏗️  Complete database schema"
echo ""
echo "💡 Next steps:"
echo "   1. Database structure is intact - no migrations needed"
echo "   2. Run: ./alembic_init_and_migrate.sh (will populate default data)"
echo "   3. Create SuperAdmin: Use /api/v1/setup/superadmin endpoint"
echo "   4. Add your fresh data as needed"
echo ""
echo "🚀 Database is clean with fresh sequences starting from 1!"
#!/bin/bash
# drop-database-completely.sh
# Script to completely drop database schema, tables, and all dependencies
# WARNING: This is a DESTRUCTIVE operation that cannot be undone!

set -euo pipefail

echo "💥 KIOSK Database Complete Destruction Script"
echo "============================================="
echo ""
echo "🚨 EXTREME WARNING: DESTRUCTIVE OPERATION! 🚨"
echo ""
echo "This script will COMPLETELY DESTROY:"
echo "   💀 ALL database tables and their data"
echo "   💀 ALL indexes, constraints, and foreign keys"
echo "   💀 ALL sequences and auto-increment counters"
echo "   💀 ALL database schemas (public schema will be recreated empty)"
echo "   💀 ALL views, functions, and stored procedures"
echo "   💀 ALL triggers and database objects"
echo "   💀 Alembic migration history"
echo ""
echo "After this operation:"
echo "   ✅ Database will exist but be completely empty"
echo "   ✅ You'll need to run alembic_init_and_migrate.sh to recreate schema"
echo "   ✅ You'll need to create users from scratch"
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
# Show current tables
TABLES=$(docker exec kiosk_postgres psql -U kiosk_user -d kiosk_db -t -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public';")
SEQUENCES=$(docker exec kiosk_postgres psql -U kiosk_user -d kiosk_db -t -c "SELECT COUNT(*) FROM information_schema.sequences WHERE sequence_schema = 'public';")
echo "   📊 Tables in public schema: $(echo $TABLES | xargs)"
echo "   🔢 Sequences in public schema: $(echo $SEQUENCES | xargs)"

if [ "$(echo $TABLES | xargs)" = "0" ]; then
    echo ""
    echo "✅ Database is already empty - nothing to destroy!"
    exit 0
fi

echo ""
echo "⚠️  FINAL CONFIRMATION REQUIRED ⚠️"
echo ""
echo "To proceed with COMPLETE DATABASE DESTRUCTION, you must:"
echo "1. Type exactly: DESTROY EVERYTHING"
echo "2. Press Enter"
echo ""
echo "Any other input will cancel this operation."
echo ""
echo -n "Enter confirmation: "
read -r confirmation

if [ "$confirmation" != "DESTROY EVERYTHING" ]; then
    echo ""
    echo "❌ Operation cancelled. Database destruction aborted."
    echo "✅ Your data is safe."
    exit 0
fi

echo ""
echo "💥 Proceeding with COMPLETE database destruction..."
echo "=================================================="

# Create comprehensive destruction SQL
DESTRUCTION_SQL="
-- Log the destruction start
SELECT 'Starting complete database destruction at ' || CURRENT_TIMESTAMP as destruction_log;

-- Disconnect all active connections to the database (except our own)
SELECT pg_terminate_backend(pid) 
FROM pg_stat_activity 
WHERE datname = 'kiosk_db' 
  AND pid <> pg_backend_pid()
  AND state = 'active';

-- Drop all tables with CASCADE to handle dependencies
DO \$\$
DECLARE 
    rec RECORD;
BEGIN 
    FOR rec IN 
        SELECT tablename 
        FROM pg_tables 
        WHERE schemaname = 'public'
    LOOP
        EXECUTE 'DROP TABLE IF EXISTS public.' || quote_ident(rec.tablename) || ' CASCADE';
        RAISE NOTICE 'Dropped table: %', rec.tablename;
    END LOOP;
END \$\$;

-- Drop all sequences
DO \$\$
DECLARE 
    rec RECORD;
BEGIN 
    FOR rec IN 
        SELECT sequencename 
        FROM pg_sequences 
        WHERE schemaname = 'public'
    LOOP
        EXECUTE 'DROP SEQUENCE IF EXISTS public.' || quote_ident(rec.sequencename) || ' CASCADE';
        RAISE NOTICE 'Dropped sequence: %', rec.sequencename;
    END LOOP;
END \$\$;

-- Drop all views
DO \$\$
DECLARE 
    rec RECORD;
BEGIN 
    FOR rec IN 
        SELECT viewname 
        FROM pg_views 
        WHERE schemaname = 'public'
    LOOP
        EXECUTE 'DROP VIEW IF EXISTS public.' || quote_ident(rec.viewname) || ' CASCADE';
        RAISE NOTICE 'Dropped view: %', rec.viewname;
    END LOOP;
END \$\$;

-- Drop all functions and procedures
DO \$\$
DECLARE 
    rec RECORD;
BEGIN 
    FOR rec IN 
        SELECT proname, oidvectortypes(proargtypes) as argtypes
        FROM pg_proc 
        INNER JOIN pg_namespace ON pg_proc.pronamespace = pg_namespace.oid 
        WHERE pg_namespace.nspname = 'public'
    LOOP
        EXECUTE 'DROP FUNCTION IF EXISTS public.' || quote_ident(rec.proname) || '(' || rec.argtypes || ') CASCADE';
        RAISE NOTICE 'Dropped function: %(%)', rec.proname, rec.argtypes;
    END LOOP;
END \$\$;

-- Drop all types
DO \$\$
DECLARE 
    rec RECORD;
BEGIN 
    FOR rec IN 
        SELECT typname 
        FROM pg_type 
        INNER JOIN pg_namespace ON pg_type.typnamespace = pg_namespace.oid 
        WHERE pg_namespace.nspname = 'public' 
          AND pg_type.typtype = 'e'  -- Only enum types
    LOOP
        EXECUTE 'DROP TYPE IF EXISTS public.' || quote_ident(rec.typname) || ' CASCADE';
        RAISE NOTICE 'Dropped type: %', rec.typname;
    END LOOP;
END \$\$;

-- Finally, drop and recreate the public schema to ensure complete cleanup
DROP SCHEMA IF EXISTS public CASCADE;
CREATE SCHEMA public;

-- Grant necessary permissions on the new schema
GRANT ALL ON SCHEMA public TO kiosk_user;
GRANT ALL ON SCHEMA public TO public;

-- Final verification
SELECT 
    'Database destruction completed at ' || CURRENT_TIMESTAMP as destruction_log,
    (SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public') as remaining_tables,
    (SELECT COUNT(*) FROM information_schema.sequences WHERE sequence_schema = 'public') as remaining_sequences;
"

echo "🗄️  Executing complete database destruction..."
echo ""

# Execute the destruction with detailed output
echo "$DESTRUCTION_SQL" | docker exec -i kiosk_postgres psql -U kiosk_user -d kiosk_db

echo ""
echo "💀 Database destruction completed!"
echo ""
echo "📋 What was destroyed:"
echo "   💥 ALL tables and their data"
echo "   💥 ALL indexes and constraints" 
echo "   💥 ALL sequences and auto-increment counters"
echo "   💥 ALL views and functions"
echo "   💥 ALL custom types and enums"
echo "   💥 Entire public schema (recreated empty)"
echo "   💥 Alembic migration tracking"
echo ""
echo "✅ Database is now completely empty and ready for fresh schema creation."
echo ""
echo "💡 Next steps:"
echo "   1. Run: ./alembic_init_and_migrate.sh"
echo "   2. This will recreate schema from models.py"
echo "   3. Create your SuperAdmin user again"
echo "   4. Set up your system from scratch"
echo ""
echo "🚀 Complete database destruction finished!"
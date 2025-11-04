-- 01-init.sql
-- PostgreSQL initialization script for KIOSK database

-- This script runs automatically when the PostgreSQL container starts for the first time

-- Create extensions if needed
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Grant all privileges to the application user
GRANT ALL ON SCHEMA public TO kiosk_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO kiosk_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO kiosk_user;

-- Set default privileges for future tables and sequences
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO kiosk_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO kiosk_user;
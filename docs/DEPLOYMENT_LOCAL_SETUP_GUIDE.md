# KIOSK Application Setup Guide

This project uses a modular monorepo architecture: each service and frontend application lives in its own folder within a single repository.

This comprehensive guide covers everything you need to deploy, configure, and manage the KIOSK application using Docker.

---

## 🆕 First Time Setup From Scratch

**Use this guide if you're setting up the project for the first time or after a complete cleanup.**

Follow these steps in exact order:

### Step 1: Start Docker Services
```bash
# Run from: KIOSK project root directory
./scripts/start-docker.sh
```

**What happens:**
- ✅ Starts PostgreSQL container (port 5433)
- ✅ Starts backend container (keeps alive but doesn't serve HTTP)
- ⚠️ You may see "❌ Backend is not responding" - **This is EXPECTED!**

**Why the backend warning?** The backend container is designed to stay alive without serving HTTP requests. You'll run the actual FastAPI server locally (Step 4) for development with hot reload.

### Step 2: Create Database Schema (**REQUIRED**)
```bash
# Run from: KIOSK project root directory
./scripts/alembic-schema-only.sh
```

**When prompted:**
- Type: `CREATE SCHEMA` and press Enter

**What this creates:**
- ✅ All 28 database tables from models.py
- ✅ All foreign key relationships
- ✅ All indexes and constraints

### Step 3: Populate Lookup Data (**REQUIRED** - Cannot skip!)
```bash
# Run from: KIOSK project root directory
./scripts/alembic-sql-changes-scripts.sh
```

**When prompted:**
1. Type: `START PROCESSING` and press Enter
2. For each SQL script, type: `E` (Execute)

**What this creates:**
- ✅ **Roles** (superadmin, admin, customer, kiosk, etc.) - **REQUIRED for user creation**
- ✅ **Payment methods** (Card, NFC, QR) - **REQUIRED for orders**
- ✅ **Units of measure** (piece) - **REQUIRED for items**
- ✅ **Branches** (ZeroPoint) - **REQUIRED for devices**
- ✅ **Promoted labels** (NEW!/НОВИНКИ!) - For UI display

**⚠️ WARNING:** Without this step, you **CANNOT** create users or process orders!

### Step 4: Start Backend Locally
```bash
# Run from: KIOSK project root directory
cd backend
python -m app.main
```

**Expected output:**
```
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
```

✅ **Leave this terminal running** - backend is now serving on port 8000

### Step 5: Verify Backend is Working

**Open a new terminal** and test:
```bash
# Health check
curl http://localhost:8000/health
# Expected: {"status":"healthy","version":"0.1.0"}

# Setup status
curl http://localhost:8000/api/v1/setup/status
# Expected: {"setup_required":true,"has_superadmin":false,...}
```

**Or open in browser:**
- API Docs: http://localhost:8000/docs (Swagger UI)

### Step 6: Start Frontend Locally
```bash
# Run from: KIOSK project root directory (in a new terminal)
cd frontend/apps/kiosk
pnpm install  # First time only
pnpm dev
```

**Expected output:**
```
VITE v6.x.x  ready in xxx ms
➜  Local:   http://localhost:3000/  (or 4000 if 3000 is busy)
```

✅ **Leave this terminal running** - frontend is now serving

### Step 7: Create SuperAdmin User (First Time Only)
```bash
# Run from: Any terminal
curl -X POST http://localhost:8000/api/v1/setup/superadmin \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin",
    "password": "Admin123!",
    "email": "admin@test.com"
  }'
```

**Response:**
```json
{
  "user_id": 1,
  "username": "admin",
  "email": "admin@test.com",
  "role": "superadmin",
  "message": "SuperAdmin created successfully"
}
```

### Step 8: Access Your Application

**You now have:**
- 🌐 **Frontend:** http://localhost:3000 (or 4000)
- 📚 **API Docs:** http://localhost:8000/docs
- 🏥 **Health Check:** http://localhost:8000/health
- 🔐 **SuperAdmin:** username: `admin`, password: `Admin123!`

**Next steps:**
- Use Swagger UI to create more users, items, menus
- Or use the frontend to manage data
- Start developing!

---

## 🚀 Quick Start (Daily Development)

## 🖥️ Local Frontend Development (No Docker)

Each frontend application can be developed and tested independently using pnpm:

Kiosk (http://localhost:3000):
```bash
cd frontend/apps/kiosk
pnpm install
pnpm dev
```
### Prerequisites
- Docker and Docker Compose installed
- No services running on ports: 8001, 5433

### One-Command Deployment
```bash
# Run from: KIOSK project root directory
./scripts/start-docker.sh
```

This script will:
- ✅ Check Docker is running  
- ✅ Create necessary directories
- ✅ Stop any existing containers
- ✅ Build and start all services
- ✅ Wait for services to be healthy
- ✅ Test backend and database connectivity

## 🧹 Complete Cleanup & Fresh Installation

### Full System Cleanup
```bash
# Run from: KIOSK project root directory
# Clean up everything - containers, images, data
./scripts/cleanup-docker.sh

# Remove all Docker artifacts
docker system prune -a -f --volumes

# Remove data directories (WARNING: All data will be lost!)
sudo rm -rf data/uploads/* data/logs/* data/postgres/*
```

### Additional Cleanup Commands
```bash
# Run from: KIOSK project root directory
# Remove only KIOSK containers and images
docker-compose down -v --remove-orphans --rmi all

# Clean Docker system cache
docker builder prune -f

# Remove unused networks
docker network prune -f
```

### Database Data Cleanup Options

#### Option 1: Clean Business Data Only (Preserve Users)
```bash
# Run from: KIOSK project root directory (containers must be running)
# Keeps users, roles, sessions - removes business data
./scripts/cleanup-data-from-db.sh
```

This script will:
- ✅ Preserve all users (superadmin, admin, staff)
- ✅ Preserve all roles and permissions
- ✅ Preserve active user sessions
- 🗑️ Delete all orders, payments, customers
- 🗑️ Delete all inventory items and devices
- 🗑️ Delete all categories
- ✅ Reset business data sequences to start from 1

#### Option 2: Complete Database Cleanup (Nuclear Option)
```bash
# Run from: KIOSK project root directory (containers must be running)
# ⚠️ WARNING: This deletes ALL data while preserving roles
./scripts/cleanup-complete-data-from-db.sh
```

This script will:
- ✅ Delete all users (including superadmin)
- ✅ Delete all orders, payments, customers
- ✅ Delete all sessions and inventory
- ✅ Delete all devices and categories
- ✅ Reset all ID sequences to start from 1
- ✅ Preserve roles for system functionality
- ⚠️ Require explicit confirmation ("DELETE ALL")

## 🔧 Deployment Options

### Basic Backend Only (Recommended)
```bash
# Run from: KIOSK project root directory
./scripts/start-docker.sh
```

### With kiosk frontend
```bash
# Run from: KIOSK project root directory
./scripts/start-docker.sh --kiosk
```

### Clean Start (Removes All Data)
```bash
# Run from: KIOSK project root directory
./scripts/start-docker.sh --clean
```

## 🗄️ Database Migration with Alembic

### Interactive Migration Script (Recommended)
```bash
# Run from: KIOSK project root directory
# Make sure containers are running first
./scripts/start-docker.sh

# Run migration scripts
# Option 1: Schema changes only
./scripts/alembic-schema-only.sh

# Option 2: SQL data changes only
./scripts/alembic-sql-changes-scripts.sh
```

Available migration scripts:
- [`alembic-schema-only.sh`](../scripts/alembic-schema-only.sh) - Apply schema migrations from models.py
- [`alembic-sql-changes-scripts.sh`](../scripts/alembic-sql-changes-scripts.sh) - Execute SQL scripts from DBchangesscripts/

### Managing Database Changes

#### Schema Changes
1. Modify [`backend/app/database/models.py`](../backend/app/database/models.py)
2. Run `./scripts/alembic-schema-only.sh`
3. Review and confirm changes

#### API Structure
- All API endpoints are in [`backend/app/api/`](../backend/app/api/)
- No versioning folders - direct files: `auth.py`, `users.py`
- Simple import structure for rapid development

#### Data Changes (Like Adding Roles)
1. Create SQL file in [`backend/DBchangesscripts/`](../backend/DBchangesscripts/)
2. Run `./scripts/alembic-sql-changes-scripts.sh`
3. Script will find and execute your SQL files

#### Current Default Roles
The system includes these roles (populated via `default_roles.sql`):
- `superadmin` - Full system access
- `admin` - Administrative access
- `customer` - Customer/end-user access
- `pos-terminal` - POS terminal device
- `kkt` - KKT device
- `externalDisplay` - External display device
- `externalKitchen` - Kitchen display system
- `externalPostBox` - Post/delivery system
- `externalPaymentGate` - Payment gateway
- `externalEmailService` - Email service integration
- `externalSMSService` - SMS service integration

### Manual Migration Commands (Advanced)
```bash
# Run from: KIOSK project root directory (containers must be running)
# Generate new migration
docker exec kiosk_backend alembic revision --autogenerate -m "Migration description"

# Apply migrations
docker exec kiosk_backend alembic upgrade head

# Check migration status
docker exec kiosk_backend alembic current

# Downgrade to previous migration
docker exec kiosk_backend alembic downgrade -1

# Execute SQL script manually
docker exec -i kiosk_postgres psql -U kiosk_user -d kiosk_db < backend/DBchangesscripts/your_script.sql
```

## 🌐 Service Endpoints & Health Checks

### Available Endpoints

| Service | Local URL | Docker URL | Purpose | Status |
|---------|-----------|------------|---------|--------|
| API Docs (Swagger) | http://localhost:8000/docs | http://localhost:8001/docs | Interactive API documentation | ✅ Working |
| Health Check | http://localhost:8000/health | http://localhost:8001/health | Service health status | ✅ Working |
| Server Info | http://localhost:8000/ | http://localhost:8001/ | Basic server information | ✅ Working |
| Setup Status | http://localhost:8000/api/v1/setup/status | http://localhost:8001/api/v1/setup/status | Check if SuperAdmin setup needed | ✅ Working |
| Setup SuperAdmin | http://localhost:8000/api/v1/setup/superadmin | http://localhost:8001/api/v1/setup/superadmin | First-time SuperAdmin creation (race-safe) | ✅ Working |
| Frontend (Kiosk) | http://localhost:3000 | http://localhost:8080 | Kiosk React application (if --kiosk flag used) | Status depends on whether started |

**Note**: The `/api/v1` prefix is configured in main.py, while the folder structure is simplified (no v1 folders).

### Health Check Commands
```bash
# Run from: Any terminal (containers must be running)
# Backend health - Local
curl http://localhost:8000/health
# Backend health - Docker
curl http://localhost:8001/health
# Expected: {"status": "healthy", "version": "0.1.0"}

# Backend info - Local
curl http://localhost:8000/
# Backend info - Docker
curl http://localhost:8001/
# Expected: {"message": "KIOSK Application Backend API", "version": "0.1.0"}

# Run from: KIOSK project root directory
# Database health
docker-compose exec postgres pg_isready -U kiosk_user -d kiosk_db

# Check all services status
docker-compose ps

# Check backend container logs
docker-compose logs backend | tail -10
```

## 👥 User Management & Authentication

### Initial Setup - Creating SuperAdmin

First, check if setup is required:
```bash
# Run from: Any terminal (containers must be running)
# Local backend
curl http://localhost:8000/api/v1/setup/status
# Docker backend
curl http://localhost:8001/api/v1/setup/status
```

Create SuperAdmin (first-time setup only):
```bash
# Run from: Any terminal (containers must be running)
# Note: This endpoint has race condition protection for safe concurrent access

# Local backend
curl -X POST http://localhost:8000/api/v1/setup/superadmin \
  -H "Content-Type: application/json" \
  -d '{"username": "superadmin", "password": "SuperPassword123", "email": "super@admin.com"}'

# Docker backend
curl -X POST http://localhost:8001/api/v1/setup/superadmin \
  -H "Content-Type: application/json" \
  -d '{"username": "superadmin", "password": "SuperPassword123", "email": "super@admin.com"}'
```

### SuperAdmin Login
```bash
# Run from: Any terminal (containers must be running)
# Local backend
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "superadmin", "password": "SuperPassword123"}'

# Docker backend
curl -X POST http://localhost:8001/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "superadmin", "password": "SuperPassword123"}'
```

**Save the `access_token` from the response for creating other users!**

### Creating Admin Users

Using the SuperAdmin token:
```bash
# Run from: Any terminal (containers must be running)
# Using JSON body (role_id field is ignored - admin role assigned automatically)

# Local backend
curl -X POST http://localhost:8000/api/v1/users/create-admin \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_SUPERADMIN_TOKEN_HERE" \
  -d '{"username": "admin_user", "password": "AdminPass123", "email": "admin@test.com"}'

# Docker backend
curl -X POST http://localhost:8001/api/v1/users/create-admin \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_SUPERADMIN_TOKEN_HERE" \
  -d '{"username": "admin_user", "password": "AdminPass123", "email": "admin@test.com"}'
```

### User Roles Setup (SQL Script)

If you need to manually populate the roles table, connect to the database and run:

```bash
# Run from: KIOSK project root directory (containers must be running)
# Connect to database
docker-compose exec postgres psql -U kiosk_user -d kiosk_db
```

Then execute this SQL:
```sql
-- Insert default roles
INSERT INTO roles (role_id, name, permissions, created_at) VALUES 
(1, 'superadmin', '{"all_permissions": true, "can_create_admins": true, "can_manage_system": true}', NOW()),
(2, 'admin', '{"can_create_users": true, "can_manage_inventory": true, "can_view_reports": true, "can_manage_devices": true}', NOW()),
(3, 'customer', '{"can_use_kiosk": true, "can_view_own_transactions": true}', NOW())
ON CONFLICT (role_id) DO NOTHING;
```

### User Authentication Workflow
```bash
# Run from: Any terminal (containers must be running)

# 1. Get current user info
# Local backend
curl -X GET http://localhost:8000/api/v1/auth/me \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN_HERE"
# Docker backend
curl -X GET http://localhost:8001/api/v1/auth/me \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN_HERE"

# 2. Logout
# Local backend
curl -X POST http://localhost:8000/api/v1/auth/logout \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN_HERE"
# Docker backend
curl -X POST http://localhost:8001/api/v1/auth/logout \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN_HERE"

# 3. List all users (SuperAdmin only)
# Local backend
curl -X GET http://localhost:8000/api/v1/users/ \
  -H "Authorization: Bearer YOUR_SUPERADMIN_TOKEN_HERE"
# Docker backend
curl -X GET http://localhost:8001/api/v1/users/ \
  -H "Authorization: Bearer YOUR_SUPERADMIN_TOKEN_HERE"
```

## 🔍 Service Ports & Database Access

### Port Configuration
| Service | Internal Port | External Port | Local URL | Docker URL | Purpose |
|---------|---------------|---------------|-----------|------------|---------|
| Backend | 8000 | 8001 | http://localhost:8000 | http://localhost:8001 | FastAPI application |
| PostgreSQL | 5432 | 5433 | localhost:5433 | localhost:5433 | Database |
| Frontend (Kiosk) | 3000 | 8080 | http://localhost:3000 | http://localhost:8080 | React application |

**Note**:
- Local backend runs on port 8000 when using `python -m app.main`
- Docker backend maps port 8001 (host) → 8000 (container)

### Database Access Methods

#### Via Docker
```bash
# Run from: KIOSK project root directory (containers must be running)
docker exec -it kiosk_postgres psql -U kiosk_user -d kiosk_db
```

#### Via External Client
- **Host:** localhost
- **Port:** 5433
- **Database:** kiosk_db
- **Username:** kiosk_user
- **Password:** kiosk_secure_password_2025

### PostgreSQL Initialization Script (Note)

There's a PostgreSQL initialization script at `data/postgres-init/01-init.sql` that creates extensions and sets permissions. However, this script is currently not being used because:

- **Current mount:** `docker-compose.yml` mounts `./data/postgres/` to `/docker-entrypoint-initdb.d/`
- **File location:** The init script is in `./data/postgres-init/` (wrong folder)

**Impact:** None - the application works fine without this script because:
- Your code uses Python's `uuid.uuid4()` (doesn't need PostgreSQL's `uuid-ossp` extension)
- Permissions are set via Docker Compose environment variables
- Everything functions normally

**To fix (optional):**
```bash
# If you want to use the init script in future fresh installations:
cp data/postgres-init/01-init.sql data/postgres/
# Then clean and restart Docker for it to run on next fresh start
```

## 🚨 Troubleshooting

### Common Issues & Solutions

#### Backend Not Starting
```bash
# Run from: KIOSK project root directory
# Check logs
docker-compose logs backend

# Common fixes:
docker-compose restart backend  # Restart backend
./scripts/start-docker.sh --clean      # Clean start
```

#### Database Connection Issues
```bash
# Run from: KIOSK project root directory
# Check database status
docker-compose exec postgres pg_isready -U kiosk_user -d kiosk_db

# Reset database
docker-compose down -v
./scripts/start-docker.sh
```

#### Port Conflicts
```bash
# Run from: Any terminal
# Check what's using ports
lsof -i :8001  # Backend (Docker)
lsof -i :8000  # Backend (local)
lsof -i :5433  # PostgreSQL
lsof -i :3000  # Frontend (local)
lsof -i :8080  # Frontend (Docker)

# Kill processes if needed
sudo kill -9 PID
```

#### Permission Issues (macOS/Linux)
```bash
# Run from: KIOSK project root directory
# Fix permissions
sudo rm -rf frontend/node_modules 2>/dev/null || true
sudo rm -f frontend/package-lock.json 2>/dev/null || true
./scripts/cleanup-docker.sh
```

### Service Monitoring

#### View Logs
```bash
# Run from: KIOSK project root directory
# All services
docker-compose logs -f

# Specific services
docker-compose logs -f backend
docker-compose logs -f postgres
```

#### Restart Services
```bash
# Run from: KIOSK project root directory
# Restart all
docker-compose restart

# Restart specific service
docker-compose restart backend
docker-compose restart postgres
```

## ✅ Verification Checklist

After deployment, verify these indicators:

1. **All containers healthy:** `docker compose ps` shows "Up (healthy)"
2. **Health endpoint:**
   - Local: `curl http://localhost:8000/health` returns 200
   - Docker: `curl http://localhost:8001/health` returns 200
3. **Database accessible:** Can connect and query tables
4. **Authentication works:** SuperAdmin creation and login successful
5. **API documentation:**
   - Local: http://localhost:8000/docs loads correctly
   - Docker: http://localhost:8001/docs loads correctly
6. **User creation:** SuperAdmin can create admin users
7. **Migrations applied:** Database schema is up-to-date

### Automated Testing
```bash
# Run from: KIOSK project root directory, then navigate to backend
cd backend
python test_auth_apis.py
```

## 🎯 Expected Final State

Successfully deployed KIOSK application should have:

- ✅ PostgreSQL running on port 5433 with KIOSK database
- ✅ FastAPI backend accessible:
  - Local: port 8000 (`python -m app.main`)
  - Docker: port 8001 (container port 8000 mapped to host 8001)
- ✅ Database tables auto-created with proper schema
- ✅ Default roles (superadmin, admin, customer, kiosk_user) in database
- ✅ SuperAdmin user created and authenticated
- ✅ JWT authentication system working (both admin and kiosk tokens)
- ✅ All API endpoints responding correctly
- ✅ Optional kiosk frontend:
  - Local: port 3000 (`pnpm dev`)
  - Docker: port 8080 (if --kiosk flag used)

## 📋 Maintenance Commands

### Regular Maintenance
```bash
# Run from: KIOSK project root directory
# Update and restart services
./scripts/start-docker.sh --clean

# View system resource usage
docker stats

# Backup database
docker-compose exec postgres pg_dump -U kiosk_user kiosk_db > backup.sql

# Restore database
docker-compose exec -T postgres psql -U kiosk_user -d kiosk_db < backup.sql
```

### Production Considerations
```bash
# Run from: KIOSK project root directory
# Monitor logs continuously
docker-compose logs -f --tail=100

# Check disk usage
docker system df

# Clean up old logs
docker system prune -f --filter "until=24h"
```

This setup provides a complete, isolated, and production-ready KIOSK authentication system using Docker!
## App locations, ports, docs, and how to launch (local and VS Code)

This project uses a single source of truth per app for configuration.

- Backend (FastAPI)
  - Location: backend app root at [backend/app](backend/app/main.py)
  - Centralized config for backend: backend/.env (loaded by [Settings loader](backend/app/config.py:10))
    - Key settings:
      - HOST: bind address for uvicorn (local default: 127.0.0.1; Docker container: 0.0.0.0 via compose)
      - PORT: server port (default: 8000)
      - API_V1_STR: API prefix (default: /api/v1)
    - Override path to env file if needed via BACKEND_ENV_FILE
  - How it starts
    - Entrypoint module: [uvicorn.run(...)](backend/app/main.py:72)
    - OpenAPI path: set by openapi_url=f"{settings.API_V1_STR}/openapi.json" in [FastAPI app config](backend/app/main.py:18)
  - API documentation URLs (by environment)
    - Local run: http://127.0.0.1:8000/docs
    - Local OpenAPI JSON: http://127.0.0.1:8000/api/v1/openapi.json
    - Docker (host via port mapping 8001 -> 8000): http://localhost:8001/docs
  - Launch commands
    - From a regular terminal:
      ```bash
      # Repo root -> run backend locally
      cd backend
      python -m app.main
      ```
    - From VS Code integrated terminal:
      - Open the integrated terminal, ensure the working directory is the repository root or backend/
      - Run the same commands as above
    - Via Docker Compose (container already configured to read backend/.env):
      ```bash
      # From repo root: start dependencies and backend container
      docker compose up -d postgres
      docker compose up -d backend

      # Start the backend server inside the container (manual, by design)
      docker compose exec backend python -m app.main
      ```
      Notes:
      - Container bind address is forced to 0.0.0.0 via HOST in docker-compose.
      - External access is through host port 8001 mapped to container 8000.

- Frontend app
  - Kiosk app: frontend/apps/kiosk
  - API base URL configuration: VITE_API_URL and VITE_WS_URL (kept in .env.local)
    - Local backend (no Docker): VITE_API_URL=http://localhost:8000
    - Backend via Docker (host mapping 8001 -> 8000): VITE_API_URL=http://localhost:8001
  - Typical dev run:
    ```bash
    cd frontend/apps/kiosk
    pnpm install
    pnpm dev
    ```

- Where things live
  - Backend service code and API routes: [backend/app](backend/app/main.py)
  - API docs (Swagger UI): /docs on the backend host/port
  - OpenAPI JSON: {API_V1_STR}/openapi.json (default /api/v1/openapi.json)
  - Docker Compose services and port mappings: [docker-compose.yml](docker-compose.yml)
  - Backend container image definition: [backend/Dockerfile](backend/Dockerfile)

- Changing ports and addresses
  - Backend:
    - Local run: edit HOST and PORT in [backend/.env](backend/.env)
    - Docker run: adjust the host port mapping in [docker-compose.yml](docker-compose.yml) (e.g., "8001:8000") and ensure HOST=0.0.0.0 (already set)
  - Frontends:
    - Update VITE_API_URL and VITE_WS_URL in repo-root [.env] (or per-frontend env) to point to the backend’s host:port

Quick reference:
- Default local backend: http://127.0.0.1:8000 (Docs at /docs)
- Default Docker host mapping: http://localhost:8001 (Docs at /docs)
- OpenAPI JSON: http://HOST:PORT/api/v1/openapi.json
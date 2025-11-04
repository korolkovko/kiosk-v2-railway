# DEPLOYMENT_DOCKER_STRATEGY.md
# Development/Production Docker Deployment Strategy

## 📚 Related Documentation

This document is part of the KIOSK deployment documentation suite:

- **[DEPLOYMENT_LOCAL_SETUP_GUIDE.md](./DEPLOYMENT_LOCAL_SETUP_GUIDE.md)** - Complete local setup guide (current workflow)
- **[DEPLOYMENT_PROD_SETUP_GUIDE.md](./DEPLOYMENT_PROD_SETUP_GUIDE.md)** - Production server deployment guide
- **[DEPLOYMENT_SECRETS_MANAGEMENT.md](./DEPLOYMENT_SECRETS_MANAGEMENT.md)** - Secrets storage and management

---

## 🎯 Goal: Same Setup, Different Environments

This document follows the **12-Factor App** methodology where development and production environments are as similar as possible, differing only in configuration.

**Key Principle:**
- ✅ Same Docker images for dev and prod
- ✅ Same application code
- ✅ Only configuration differs (.env files, docker-compose overrides)

---

## 🏠 Your Current Development Workflow

### Daily Development (Hybrid Mode)

**What you do now:**
```bash
# 1. Start Docker services (PostgreSQL + optionally backend)
./scripts/start-docker.sh

# 2. Run backend locally for faster iteration
cd backend
python -m app.main

# 3. Run frontend locally with hot reload
cd frontend/apps/kiosk
pnpm dev
```

**What runs where:**
- ✅ **PostgreSQL**: Docker (kiosk_postgres container on port 5433)
- ✅ **Backend**: Local Python (port 8000, hot reload)
- ✅ **Frontend**: Local pnpm dev (port 3000, hot reload)

**Why this works well:**
- Fast hot reload for backend and frontend
- No Docker overhead for code changes
- Reliable database in Docker
- Flexible - you control what runs where

### Alternative: Full Docker Mode (Sometimes)

**When you want to test containerized setup:**
```bash
# Start everything in Docker including frontend
./scripts/start-docker.sh --kiosk

# Access:
# - Backend: http://localhost:8001
# - Frontend: http://localhost:8080
```

**What runs where:**
- ✅ **PostgreSQL**: Docker (kiosk_postgres)
- ✅ **Backend**: Docker (kiosk_backend, built from Dockerfile)
- ✅ **Frontend**: Docker (kiosk_frontend_kiosk, profile: kiosk)

**Use cases:**
- Testing production-like setup locally
- Debugging Docker-specific issues
- Validating Dockerfiles before production

---

## 📁 Current File Structure

```
KIOSK/
├── docs/
│   ├── DEPLOYMENT_LOCAL_SETUP_GUIDE.md      # Your setup process (renamed from SETUP_GUIDE.md)
│   ├── DEPLOYMENT_DOCKER_STRATEGY.md        # This file
│   ├── DEPLOYMENT_PROD_SETUP_GUIDE.md       # TODO: Production deployment
│   └── DEPLOYMENT_SECRETS_MANAGEMENT.md     # TODO: Secrets guide
│
├── scripts/
│   ├── start-docker.sh                      # ✅ Your daily startup script
│   ├── start.sh                             # ✅ Alternative startup
│   ├── stop.sh                              # Stop Docker services
│   ├── logs.sh                              # View logs
│   └── ... (other utility scripts)
│
├── docker-compose.yml                        # ✅ Current development setup
│
├── backend/
│   ├── .env                                  # ✅ Your dev secrets (gitignored)
│   ├── Dockerfile                            # ✅ Exists (used by docker-compose)
│   └── app/
│       └── main.py                           # ✅ Your local run: python -m app.main
│
└── frontend/apps/kiosk/
    ├── .env.local                            # ✅ Your dev secrets (gitignored)
    ├── Dockerfile.pnpm                       # ✅ Exists (used by docker-compose)
    └── package.json                          # ✅ Your local run: pnpm dev
```

---

## 🔧 Current Docker Configuration (docker-compose.yml)

### Your Existing Setup (No Changes)

```yaml
services:
  # PostgreSQL - Always runs in Docker
  postgres:
    image: postgres:15-alpine
    container_name: kiosk_postgres
    ports:
      - "5433:5432"  # Port 5433 to avoid conflicts
    volumes:
      - postgres_data:/var/lib/postgresql/data
    # Always healthy and ready for local python/pnpm connections

  # Backend - Optional Docker (you prefer local python)
  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    container_name: kiosk_backend
    ports:
      - "8001:8000"
    volumes:
      - ./backend:/app  # Hot reload support
    depends_on:
      - postgres
    # You usually DON'T use this, run python -m app.main instead

  # Frontend - Optional Docker with profile
  kiosk-frontend:
    build:
      context: ./frontend/apps/kiosk
      dockerfile: Dockerfile.pnpm
    container_name: kiosk_frontend_kiosk
    ports:
      - "8080:80"
    profiles:
      - kiosk  # Only runs with --profile kiosk flag
    # You usually DON'T use this, run pnpm dev instead
```

**Key Features:**
- PostgreSQL on port **5433** (avoids conflicts with system postgres on 5432)
- Backend **CAN** run in Docker, but you prefer local python
- Frontend requires `--profile kiosk` flag (optional)
- Hot reload support via volume mounts (`./backend:/app`)

---

## 📋 Proposed Production Structure (NEW)

### Files to Add (Won't Affect Your Dev Workflow)

```
KIOSK/
├── docker-compose.yml                        # ✅ KEEP: Your current dev setup
├── docker-compose.prod.yml                   # 🆕 ADD: Production overrides
│
├── .env.example                              # 🆕 ADD: Safe template for git
├── .env.prod.example                         # 🆕 ADD: Production template
│
├── .gitignore                                # 🔧 UPDATE: Protect secrets
│
├── backend/
│   ├── .env                                  # ✅ KEEP: Your dev secrets (gitignored)
│   └── Dockerfile                            # ✅ KEEP: Already production-ready
│
├── frontend/apps/kiosk/
│   ├── .env                                  # ✅ KEEP: Your dev secrets (gitignored)
│   ├── .env.example                          # 🆕 ADDED: Safe template for git
│   └── Dockerfile.pnpm                       # ✅ KEEP: Already production-ready
│
└── deployment/                               # 🆕 ADD: Production deployment
    ├── scripts/
    │   ├── deploy-prod.sh                   # Deploy to production
    │   ├── backup-db.sh                     # Database backup
    │   └── setup-secrets.sh                 # Initialize secrets
    └── nginx/
        └── nginx.prod.conf                  # Reverse proxy config
```

---

## 🆕 Production Configuration (docker-compose.prod.yml)

### NEW File - Production Overrides

**Location:** `docker-compose.prod.yml`
**Purpose:** Production-specific settings (doesn't change your dev setup)

```yaml
# docker-compose.prod.yml
# Production overrides for docker-compose.yml
# Usage: docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d

services:
  postgres:
    # Remove port exposure (internal only for security)
    ports: []
    restart: always
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 2G

  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile  # Production-optimized Dockerfile
    # No volume mounts (no hot reload in production)
    volumes:
      - /var/kiosk/uploads:/app/uploads
      - /var/kiosk/logs:/app/logs
    environment:
      - ENVIRONMENT=production
      - DEBUG=false
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
    restart: always
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 2G

  kiosk-frontend:
    build:
      context: ./frontend/apps/kiosk
      dockerfile: Dockerfile.pnpm  # Production build
    restart: always
    profiles: []  # Remove profile requirement (always runs in prod)

  # Add nginx reverse proxy
  nginx:
    image: nginx:alpine
    container_name: kiosk_nginx
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./deployment/nginx/nginx.prod.conf:/etc/nginx/nginx.conf:ro
      - ./deployment/ssl:/etc/nginx/ssl:ro
      - /var/kiosk/media:/var/kiosk/media:ro
    depends_on:
      - backend
      - kiosk-frontend
    restart: always
    networks:
      - kiosk_network
```

---

## 🔐 Environment Files Strategy

### Development (Your Current Setup)

**Location:** `backend/.env`
**Status:** ✅ Keep as-is (gitignored)
**Usage:** Loaded by python-dotenv when you run `python -m app.main`

```bash
# backend/.env (your current file - NO CHANGES)
HOST=127.0.0.1
PORT=8000
ENVIRONMENT=development
DEBUG=false
SECRET_KEY=a1b2c3d4e5f6g7h8...
DATABASE_URL=postgresql://kiosk_user:kiosk_secure_password_2025@127.0.0.1:5433/kiosk_db
MEDIA_PATH=/var/kiosk/media
```

### Production Templates (NEW)

**File 1:** `.env.example` (safe to commit)
```bash
# .env.example - Safe template for git
# Copy to backend/.env and fill in real values

HOST=127.0.0.1
PORT=8000
ENVIRONMENT=development
DEBUG=false

# CHANGE THESE - Generate random secrets
SECRET_KEY=GENERATE_RANDOM_SECRET_HERE
JWT_SECRET_KEY=GENERATE_RANDOM_JWT_SECRET_HERE
KIOSK_JWT_SECRET_KEY=GENERATE_RANDOM_KIOSK_JWT_SECRET_HERE

# Database connection
DATABASE_URL=postgresql://kiosk_user:YOUR_PASSWORD_HERE@127.0.0.1:5433/kiosk_db

# Paths
UPLOAD_PATH=./uploads
MEDIA_PATH=/var/kiosk/media
LOG_FILE_PATH=./logs/app.log

# CORS
ALLOWED_ORIGINS=["http://localhost","http://localhost:3000"]
```

**File 2:** `.env.prod.example` (safe to commit)
```bash
# .env.prod.example - Production template
# Copy to /opt/kiosk/secrets/.env.prod on production server

ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=INFO

# Database (use strong password)
DATABASE_URL=postgresql://kiosk_user:STRONG_RANDOM_PASSWORD@postgres:5432/kiosk_db

# Security (MUST generate new random secrets)
SECRET_KEY=GENERATE_64_CHAR_RANDOM_SECRET
JWT_SECRET_KEY=GENERATE_64_CHAR_RANDOM_SECRET
KIOSK_JWT_SECRET_KEY=GENERATE_64_CHAR_RANDOM_SECRET
KIOSK_JWT_KEY_ID=kiosk-prod-2025-v1

# CORS (restrict to your domain)
ALLOWED_ORIGINS=["https://yourdomain.com"]

# Production paths (absolute)
UPLOAD_PATH=/var/kiosk/uploads
MEDIA_PATH=/var/kiosk/media
LOG_FILE_PATH=/var/log/kiosk/app.log
```

---

## 📋 .gitignore Update (REQUIRED)

**Add to your `.gitignore`:**

```gitignore
# Environment files with secrets (NEVER commit)
.env
.env.local
.env.dev
.env.prod
*.env

# Allow templates only (safe to commit)
!.env.example
!.env.dev.example
!.env.prod.example

# Logs and runtime data
logs/
*.log
uploads/
media/

# Database data
data/postgres/
postgres_data/

# Docker volumes
data/

# Node modules
node_modules/
.pnpm-store/
```

---

## 🚀 Usage Workflows

### Development Workflow (Current - No Changes)

```bash
# Daily workflow (what you do now)
./scripts/start-docker.sh          # Start PostgreSQL in Docker
cd backend && python -m app.main   # Backend locally
cd frontend/apps/kiosk && pnpm dev # Frontend locally
```

### Full Docker Development (Optional)

```bash
# Sometimes test everything in Docker
./scripts/start-docker.sh --kiosk  # All services in Docker

# Or manually
docker-compose up -d               # Postgres + backend
docker-compose --profile kiosk up -d  # + frontend
```

### Production Deployment (NEW)

```bash
# On production server
cd /opt/kiosk

# Load secrets from secure location
docker-compose -f docker-compose.yml \
               -f docker-compose.prod.yml \
               --env-file /opt/kiosk/secrets/.env.prod \
               up -d

# Or use deployment script
./deployment/scripts/deploy-prod.sh
```

---

## 📦 What Will Be Created (Incremental Plan)

### Phase 1: Documentation ✅ (Current)
- ✅ Renamed SETUP_GUIDE.md → DEPLOYMENT_LOCAL_SETUP_GUIDE.md
- ✅ Created DEPLOYMENT_DOCKER_STRATEGY.md (this file)
- ⏳ TODO: DEPLOYMENT_PROD_SETUP_GUIDE.md
- ⏳ TODO: DEPLOYMENT_SECRETS_MANAGEMENT.md

### Phase 2: Environment Files (Small Changes)
**Impact:** Minimal - just adds templates, doesn't touch your .env
1. Create `.env.example` (safe template for git)
2. Create `.env.prod.example` (production template)
3. Update `.gitignore` (protect secrets)

**Your workflow:** No changes, keep using backend/.env as-is

### Phase 3: Production Docker Files
**Impact:** None on your daily workflow
1. ✅ Created `docker-compose.prod.yml` (production overrides)
2. ✅ Current `backend/Dockerfile` already production-ready (no changes needed)
3. ✅ Current `frontend/apps/kiosk/Dockerfile.pnpm` already production-ready (no changes needed)
4. ✅ Created `deployment/nginx/nginx.prod.conf`

**Your workflow:** No changes, scripts/start-docker.sh still works

**Note:** Your existing Dockerfiles are already well-optimized:
- Backend: Uses non-root user, health checks, minimal base image
- Frontend: Multi-stage build with nginx serving
- No separate `.dev` versions needed

### Phase 4: Deployment Scripts (Production Only)
**Impact:** None - these are for production server only
1. `deployment/scripts/deploy-prod.sh`
2. `deployment/scripts/backup-db.sh`
3. `deployment/scripts/setup-secrets.sh`
4. `deployment/scripts/rollback.sh`

**Your workflow:** No changes

### Phase 5: Testing & Validation
**Impact:** Voluntary testing
1. Test production config locally (optional)
2. Verify dev workflow still works (automated)
3. Document production deployment process

---

## ✅ Success Criteria

### Your Development Environment (Must Preserve)
- ✅ `./scripts/start-docker.sh` still works
- ✅ `python -m app.main` still works
- ✅ `pnpm dev` still works
- ✅ PostgreSQL on port 5433 still works
- ✅ No changes to your daily workflow
- ✅ All your existing scripts functional

### Production Environment (New Capabilities)
- ✅ One-command production deployment
- ✅ Secrets properly secured and separate
- ✅ Health checks and monitoring
- ✅ Resource limits enforced
- ✅ Easy rollback capability
- ✅ HTTPS with nginx reverse proxy

---

## 🔄 Development vs Production Comparison

| Aspect | Development (Current) | Production (New) |
|--------|----------------------|------------------|
| **PostgreSQL** | Docker, port 5433 | Docker, internal only |
| **Backend** | Local python -m app.main | Docker, 4 workers |
| **Frontend** | Local pnpm dev | Docker, nginx static |
| **Hot Reload** | ✅ Yes (volume mounts) | ❌ No (baked into image) |
| **Secrets** | backend/.env (local) | /opt/kiosk/secrets/.env.prod |
| **Ports** | 5433, 8000, 3000 | 80, 443 (nginx proxy) |
| **Resource Limits** | ❌ None | ✅ CPU/memory limits |
| **Restart Policy** | unless-stopped | always |
| **SSL/HTTPS** | ❌ Not needed | ✅ Let's Encrypt |
| **Reverse Proxy** | ❌ Direct access | ✅ Nginx |
| **Monitoring** | Manual | Health checks + logs |

---

## 🤔 Discussion Points for Implementation

Before we start implementing, let's discuss these questions:

### 1. Production Server Environment
- **What's your target?** (AWS, DigitalOcean, Hetzner, VPS, dedicated?)
- **Operating System?** (Ubuntu 22.04 LTS recommended)
- **Server specs?** (How many concurrent kiosks expected?)

### 2. Docker Image Strategy
**Option A:** Build on production server (simpler, your case)
```bash
# On server: docker-compose up builds locally
# Pros: Simple, no registry needed
# Cons: Build time on deployment
```

**Option B:** Build locally, push to registry
```bash
# Locally: docker build and push to registry
# Server: docker pull and run
# Pros: Faster deployment, version control
# Cons: Needs Docker registry (Docker Hub, GitHub, etc.)
```

**Recommendation for you:** Option A (build on server) - simpler for single deployment

### 3. SSL Certificate
**Option A:** Let's Encrypt (free, automatic renewal)
- Uses certbot in nginx container
- Auto-renewal every 90 days

**Option B:** Cloudflare (free, zero-config)
- Proxy through Cloudflare
- SSL terminates at Cloudflare edge

**Recommendation:** Let's Encrypt (more control, industry standard)

### 4. Database Backups
```bash
# Daily automated backup script
docker exec kiosk_postgres pg_dump -U kiosk_user kiosk_db > backup.sql
```
**Questions:**
- Backup frequency? (Daily, hourly?)
- Retention? (Keep last 7 days, 30 days?)
- Storage? (Local disk, S3, offsite?)

### 5. Secrets Management on Production
**Option A:** Single .env.prod file (simple, your case)
```
/opt/kiosk/secrets/.env.prod
chmod 600
```

**Option B:** Docker secrets (more secure)
```
echo "secret_value" | docker secret create db_password -
```

**Recommendation for you:** Option A (simpler, sufficient for single server)

### 6. Deployment Process
**Option A:** Manual deployment (simple, full control)
```bash
ssh production-server
cd /opt/kiosk
git pull
./deployment/scripts/deploy-prod.sh
```

**Option B:** CI/CD pipeline (automated)
- GitHub Actions deploys on push to main
- Automated testing before deployment

**Recommendation for you:** Start with Option A, add CI/CD later if needed

---

## 🚀 Next Steps - Let's Discuss

**Before I start implementing, please answer:**

1. **Do you approve this strategy?** (preserves your dev workflow, adds production)
2. **What's your production server environment?** (helps me tailor the docs)
3. **Which options do you prefer?** (image strategy, SSL, backups, deployment)

**Once you provide answers, I'll:**
1. ✅ Create DEPLOYMENT_PROD_SETUP_GUIDE.md (tailored to your answers)
2. ✅ Create DEPLOYMENT_SECRETS_MANAGEMENT.md (with your chosen strategy)
3. ✅ Plan incremental implementation (phase by phase)
4. ✅ Ensure nothing breaks your current workflow

**Ready to discuss the questions above?** 🎯

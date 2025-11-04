# DEPLOYMENT_SECRETS_MANAGEMENT.md
# Secrets and Environment Variables Management Guide

## 📚 Related Documentation

- **[DEPLOYMENT_LOCAL_SETUP_GUIDE.md](./DEPLOYMENT_LOCAL_SETUP_GUIDE.md)** - Local development setup
- **[DEPLOYMENT_DOCKER_STRATEGY.md](./DEPLOYMENT_DOCKER_STRATEGY.md)** - Docker strategy overview
- **[DEPLOYMENT_PROD_SETUP_GUIDE.md](./DEPLOYMENT_PROD_SETUP_GUIDE.md)** - Production deployment guide

---

## 🎯 Overview

This guide explains where secrets are stored, how to manage them, and what goes in git vs what stays local/server-only.

**Key Principles:**
- ✅ **Never commit secrets to git** (.env files with actual secrets)
- ✅ **Commit templates to git** (.env.example files without secrets)
- ✅ **Different secrets for dev and prod** (prevents accidents)
- ✅ **Secure file permissions** (600 for secret files)

---

## 🗂️ File Organization

### What Goes Where

```
KIOSK/
├── .env.example                      # ✅ COMMIT TO GIT (template)
├── .env.prod.example                 # ✅ COMMIT TO GIT (template)
│
├── backend/
│   └── .env                          # ❌ NEVER COMMIT (your local secrets)
│
├── frontend/apps/kiosk/
│   └── .env.local                    # ❌ NEVER COMMIT (your local secrets)
│
└── .gitignore                        # ✅ COMMIT TO GIT (protects secrets)
```

**Production Server:**
```
/opt/kiosk/secrets/
└── .env.prod                         # ❌ NEVER IN GIT (production secrets)
```

---

## 🔐 Secret Types

### 1. Application Secrets (Critical)

**What they are:** Random strings for security
**Where used:** JWT tokens, session encryption, API signatures

```bash
SECRET_KEY=a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6...           # 64 chars
JWT_SECRET_KEY=z9y8x7w6v5u4t3s2r1q0p9o8n7m6l5k4...       # 64 chars
KIOSK_JWT_SECRET_KEY=k1i2o3s4k5_6s7e8c9r0e1t2_3k4e5y6... # 64 chars
```

**How to generate:**
```bash
# Method 1: OpenSSL (recommended)
openssl rand -hex 32

# Method 2: Python
python3 -c "import secrets; print(secrets.token_hex(32))"

# Method 3: Online (less secure)
# Visit: https://www.random.org/strings/
```

**⚠️ Critical Rules:**
- ❌ Never reuse between dev and prod
- ❌ Never share in Slack, email, etc.
- ❌ Never commit to git
- ✅ Generate fresh for each environment
- ✅ Store in password manager

---

### 2. Database Credentials

**What they are:** PostgreSQL connection details

**Development:**
```bash
DATABASE_URL=postgresql://kiosk_user:YOUR_DEV_PASSWORD@127.0.0.1:5433/kiosk_db
```
- Simple password OK for local development only
- Port 5433 (avoids conflicts with system PostgreSQL)
- Connects to Docker PostgreSQL container

**Production:**
```bash
DATABASE_URL=postgresql://kiosk_user:Xy9Kp2mN7wQz4vBr8@postgres:5432/kiosk_db
```
- ✅ Strong random password (25+ chars)
- ✅ Port 5432 (internal Docker network)
- ✅ Host is `postgres` (container name)

**How to generate strong password:**
```bash
# Generate 25-character password
openssl rand -base64 32 | tr -d "=+/" | cut -c1-25
```

---

### 3. CORS Origins

**What they are:** Allowed frontend domains

**Development:**
```bash
ALLOWED_ORIGINS=["http://localhost","http://localhost:3000","http://localhost:8001"]
```
- Multiple localhost ports for flexibility

**Production:**
```bash
ALLOWED_ORIGINS=["https://kiosk.yourdomain.com","https://yourdomain.com"]
```
- ✅ Only your production domain
- ✅ HTTPS only (no HTTP)
- ❌ Don't use wildcards in production

---

### 4. File Paths

**Development (Mac):**
```bash
UPLOAD_PATH=./uploads              # Relative path
MEDIA_PATH=/var/kiosk/media       # Absolute path
LOG_FILE_PATH=./logs/app.log      # Relative path
```

**Production (Server):**
```bash
UPLOAD_PATH=/var/kiosk/uploads    # Absolute path
MEDIA_PATH=/var/kiosk/media       # Absolute path
LOG_FILE_PATH=/var/log/kiosk/app.log  # Absolute path
```

**Rule:** Production always uses absolute paths

---

### 5. External API Keys (Optional)

**If you integrate payment/POS systems:**
```bash
POS_API_URL=https://pos-provider.com/api
POS_API_KEY=sk_live_xxxxxxxxxxxx

PAYMENT_API_URL=https://payment-provider.com/api
PAYMENT_API_KEY=pk_live_xxxxxxxxxxxx
```

**⚠️ Test vs Live Keys:**
- Development: Use test/sandbox keys
- Production: Use live keys
- Never mix test keys in production!

---

## 📄 Environment File Templates

### .env.example (For Git)

**Location:** `KIOSK/.env.example`
**Purpose:** Template for new developers
**Git:** ✅ Safe to commit

```bash
# .env.example
# Copy this to backend/.env and fill in real values

# Server Configuration
HOST=127.0.0.1
PORT=8000

# Application
PROJECT_NAME=KIOSK Application
API_V1_STR=/api/v1
ENVIRONMENT=development
DEBUG=false

# Security Keys (GENERATE NEW RANDOM VALUES)
SECRET_KEY=GENERATE_RANDOM_64_CHAR_HEX
JWT_SECRET_KEY=GENERATE_RANDOM_64_CHAR_HEX
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# Kiosk Authentication (GENERATE NEW RANDOM VALUES)
KIOSK_JWT_SECRET_KEY=GENERATE_RANDOM_64_CHAR_HEX
KIOSK_JWT_ALGORITHM=HS256
KIOSK_ACCESS_TOKEN_EXPIRE_DAYS=30
KIOSK_REFRESH_TOKEN_EXPIRE_DAYS=90
KIOSK_JWT_KEY_ID=kiosk-dev-2025-v1

# Database (local Docker)
DATABASE_URL=postgresql://kiosk_user:YOUR_PASSWORD_HERE@127.0.0.1:5433/kiosk_db

# File Storage (development)
MAX_FILE_SIZE=10485760
UPLOAD_PATH=./uploads
MEDIA_PATH=/var/kiosk/media
LOG_FILE_PATH=./logs/app.log

# Logging
LOG_LEVEL=INFO

# CORS (local development)
ALLOWED_ORIGINS=["http://localhost","http://localhost:3000","http://localhost:8001"]

# External APIs (optional - leave empty if not used)
POS_API_URL=
POS_API_KEY=
PAYMENT_API_URL=
PAYMENT_API_KEY=
```

---

### .env.prod.example (For Git)

**Location:** `KIOSK/.env.prod.example`
**Purpose:** Template for production deployment
**Git:** ✅ Safe to commit

```bash
# .env.prod.example
# Copy to /opt/kiosk/secrets/.env.prod on production server
# IMPORTANT: Change all GENERATE_* placeholders

# Server Configuration
HOST=0.0.0.0
PORT=8000

# Application
PROJECT_NAME=KIOSK Application
API_V1_STR=/api/v1
ENVIRONMENT=production
DEBUG=false

# Security Keys (MUST GENERATE FRESH RANDOM VALUES)
SECRET_KEY=GENERATE_RANDOM_64_CHAR_HEX_DIFFERENT_FROM_DEV
JWT_SECRET_KEY=GENERATE_RANDOM_64_CHAR_HEX_DIFFERENT_FROM_DEV
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# Kiosk Authentication (MUST GENERATE FRESH RANDOM VALUES)
KIOSK_JWT_SECRET_KEY=GENERATE_RANDOM_64_CHAR_HEX_DIFFERENT_FROM_DEV
KIOSK_JWT_ALGORITHM=HS256
KIOSK_ACCESS_TOKEN_EXPIRE_DAYS=30
KIOSK_REFRESH_TOKEN_EXPIRE_DAYS=90
KIOSK_JWT_KEY_ID=kiosk-prod-2025-v1

# Database (Docker internal network)
DATABASE_URL=postgresql://kiosk_user:GENERATE_STRONG_PASSWORD_25_CHARS@postgres:5432/kiosk_db

# File Storage (production - absolute paths)
MAX_FILE_SIZE=10485760
UPLOAD_PATH=/var/kiosk/uploads
MEDIA_PATH=/var/kiosk/media
LOG_FILE_PATH=/var/log/kiosk/app.log

# Logging
LOG_LEVEL=INFO

# CORS (production domain only)
ALLOWED_ORIGINS=["https://kiosk.yourdomain.com","https://yourdomain.com"]

# External APIs (use LIVE keys in production)
POS_API_URL=https://pos-provider.com/api
POS_API_KEY=LIVE_KEY_HERE_IF_USED
PAYMENT_API_URL=https://payment-provider.com/api
PAYMENT_API_KEY=LIVE_KEY_HERE_IF_USED
```

---

## 🔧 Setup Instructions

### Development Setup (Your Mac)

**First time setup:**

```bash
# 1. Copy template
cp .env.example backend/.env

# 2. Generate secrets
SECRET_KEY=$(openssl rand -hex 32)
JWT_SECRET_KEY=$(openssl rand -hex 32)
KIOSK_JWT_SECRET_KEY=$(openssl rand -hex 32)

# 3. Replace placeholders
sed -i.bak "s/GENERATE_RANDOM_64_CHAR_HEX/$SECRET_KEY/g" backend/.env
sed -i.bak "s/JWT_SECRET_KEY=.*/JWT_SECRET_KEY=$JWT_SECRET_KEY/g" backend/.env
sed -i.bak "s/KIOSK_JWT_SECRET_KEY=.*/KIOSK_JWT_SECRET_KEY=$KIOSK_JWT_SECRET_KEY/g" backend/.env
rm backend/.env.bak

# 4. Verify file
cat backend/.env | grep "SECRET_KEY"

# 5. Start development
./scripts/start-docker.sh
cd backend && python -m app.main
```

**If you already have backend/.env:**
- ✅ Keep it! Don't regenerate secrets
- ✅ Just ensure it's gitignored
- ❌ Don't share it with anyone

---

### Production Setup (VPS Server)

**First time production setup:**

```bash
# SSH to production server
ssh kiosk@YOUR_SERVER_IP

# 1. Create secrets directory
sudo mkdir -p /opt/kiosk/secrets
sudo chown kiosk:kiosk /opt/kiosk/secrets
chmod 700 /opt/kiosk/secrets

# 2. Copy template from repository
cp /opt/kiosk/.env.prod.example /opt/kiosk/secrets/.env.prod

# 3. Generate fresh production secrets
SECRET_KEY=$(openssl rand -hex 32)
JWT_SECRET_KEY=$(openssl rand -hex 32)
KIOSK_JWT_SECRET_KEY=$(openssl rand -hex 32)
DB_PASSWORD=$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-25)

# 4. Display secrets (SAVE THESE IN PASSWORD MANAGER!)
echo "=== PRODUCTION SECRETS - SAVE THESE ==="
echo "SECRET_KEY=$SECRET_KEY"
echo "JWT_SECRET_KEY=$JWT_SECRET_KEY"
echo "KIOSK_JWT_SECRET_KEY=$KIOSK_JWT_SECRET_KEY"
echo "DB_PASSWORD=$DB_PASSWORD"
echo "======================================="

# 5. Replace placeholders in .env.prod
sed -i "s/GENERATE_RANDOM_64_CHAR_HEX_DIFFERENT_FROM_DEV/$SECRET_KEY/g" /opt/kiosk/secrets/.env.prod
sed -i "s/JWT_SECRET_KEY=.*/JWT_SECRET_KEY=$JWT_SECRET_KEY/g" /opt/kiosk/secrets/.env.prod
sed -i "s/KIOSK_JWT_SECRET_KEY=.*/KIOSK_JWT_SECRET_KEY=$KIOSK_JWT_SECRET_KEY/g" /opt/kiosk/secrets/.env.prod
sed -i "s/GENERATE_STRONG_PASSWORD_25_CHARS/$DB_PASSWORD/g" /opt/kiosk/secrets/.env.prod

# 6. Update domain name
nano /opt/kiosk/secrets/.env.prod
# Change: ALLOWED_ORIGINS=["https://kiosk.yourdomain.com"]
# To your actual domain

# 7. Secure permissions
chmod 600 /opt/kiosk/secrets/.env.prod

# 8. Verify file (check secrets are filled in)
grep "SECRET_KEY" /opt/kiosk/secrets/.env.prod
# Should NOT contain "GENERATE_RANDOM"

# 9. Deploy application
cd /opt/kiosk
docker compose -f docker-compose.yml \
               -f docker-compose.prod.yml \
               --env-file /opt/kiosk/secrets/.env.prod \
               up -d --build
```

---

## 🔒 Security Best Practices

### File Permissions

**Development (Mac):**
```bash
# Your .env file
chmod 600 backend/.env
# Only you can read/write

# Check permissions
ls -la backend/.env
# Expected: -rw------- (600)
```

**Production (Server):**
```bash
# Secrets directory
chmod 700 /opt/kiosk/secrets
# Only kiosk user can access

# .env.prod file
chmod 600 /opt/kiosk/secrets/.env.prod
# Only kiosk user can read/write

# Check permissions
ls -la /opt/kiosk/secrets/
# Expected: drwx------ (700) for directory
# Expected: -rw------- (600) for .env.prod
```

---

### Git Protection (.gitignore)

**Ensure your `.gitignore` includes:**

```gitignore
# Environment files with secrets (NEVER COMMIT)
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
```

**Verify nothing is committed:**
```bash
# Check git status
git status

# Should NOT see:
# - backend/.env
# - frontend/apps/kiosk/.env.local
# - Any file with real secrets

# Should see (if you added templates):
# - .env.example
# - .env.prod.example
```

---

### Password Manager Storage

**What to save in password manager:**

```
Entry: KIOSK Production Server
Username: kiosk
Server IP: YOUR_SERVER_IP
SSH Key: (path to private key)

--- Production Secrets ---
SECRET_KEY: [64-char hex]
JWT_SECRET_KEY: [64-char hex]
KIOSK_JWT_SECRET_KEY: [64-char hex]
DB_PASSWORD: [25-char password]

--- SuperAdmin Credentials ---
Username: admin
Password: [strong password]
Email: admin@yourdomain.com

--- Domain & SSL ---
Domain: kiosk.yourdomain.com
SSL Email: your-email@example.com
```

---

## 🔄 Rotating Secrets

**When to rotate:**
- Security breach or suspected compromise
- Employee leaves with access
- Every 12 months (best practice)
- After major security audit

**How to rotate (production):**

```bash
# 1. SSH to server
ssh kiosk@YOUR_SERVER_IP

# 2. Generate new secrets
NEW_SECRET_KEY=$(openssl rand -hex 32)
NEW_JWT_SECRET_KEY=$(openssl rand -hex 32)
NEW_KIOSK_JWT_SECRET_KEY=$(openssl rand -hex 32)

# 3. Update .env.prod file
nano /opt/kiosk/secrets/.env.prod
# Replace old secrets with new ones

# 4. Restart application
cd /opt/kiosk
docker compose restart backend

# 5. Test login still works
curl https://kiosk.yourdomain.com/api/v1/health

# 6. Update password manager
# Save new secrets in password manager

# 7. Invalidate old sessions (users need to re-login)
# This happens automatically when secrets change
```

**⚠️ Warning:** Changing secrets will log out all users!

---

## ❌ Common Mistakes to Avoid

### 1. Committing Secrets to Git

**Wrong:**
```bash
git add backend/.env
git commit -m "Add environment config"
git push
# ❌ SECRETS NOW IN GIT HISTORY FOREVER!
```

**If this happens:**
```bash
# Remove from git history (requires force push)
git rm --cached backend/.env
echo "backend/.env" >> .gitignore
git commit -m "Remove secrets from git"
git push

# IMPORTANT: Rotate all exposed secrets immediately!
```

---

### 2. Using Same Secrets for Dev and Prod

**Wrong:**
```bash
# backend/.env (dev)
SECRET_KEY=abc123

# /opt/kiosk/secrets/.env.prod (prod)
SECRET_KEY=abc123  # ❌ SAME AS DEV!
```

**Why dangerous:**
- Dev environment less secure (open ports, debug mode)
- If dev secrets leak, prod is compromised
- Can't rotate dev secrets without affecting prod

**Right:**
```bash
# Each environment has unique secrets
# Dev: openssl rand -hex 32 → abc123...
# Prod: openssl rand -hex 32 → xyz789...  # Different!
```

---

### 3. Weak Database Passwords

**Wrong:**
```bash
DATABASE_URL=postgresql://user:password@localhost/db  # ❌ Too weak
DATABASE_URL=postgresql://user:12345@localhost/db     # ❌ Too weak
```

**Right:**
```bash
DATABASE_URL=postgresql://user:Xy9Kp2mN7wQz4vBr8Lm3T@localhost/db  # ✅ Strong
```

**Rule:** 25+ characters, random, alphanumeric

---

### 4. Wrong File Permissions

**Wrong:**
```bash
chmod 644 backend/.env  # ❌ Anyone can read secrets!
chmod 755 /opt/kiosk/secrets/  # ❌ Anyone can enter directory!
```

**Right:**
```bash
chmod 600 backend/.env  # ✅ Only you can read
chmod 700 /opt/kiosk/secrets/  # ✅ Only you can access
```

---

### 5. Sharing Secrets Insecurely

**Wrong:**
- ❌ Email secrets to team
- ❌ Paste in Slack/Discord
- ❌ Share via Google Docs
- ❌ Write on paper and photograph

**Right:**
- ✅ Use password manager (1Password, Bitwarden)
- ✅ Encrypted file transfer (if needed)
- ✅ Separate secrets per team member
- ✅ Each person generates their own dev secrets

---

## ✅ Verification Checklist

### Development Environment

- [ ] `backend/.env` exists with real secrets
- [ ] `backend/.env` is in `.gitignore`
- [ ] `backend/.env` is NOT in git (`git status` doesn't show it)
- [ ] File permissions: `ls -la backend/.env` shows `-rw-------` (600)
- [ ] Secrets are different from production
- [ ] Application starts successfully (`python -m app.main`)

### Production Environment

- [ ] `/opt/kiosk/secrets/.env.prod` exists
- [ ] Directory permissions: `ls -ld /opt/kiosk/secrets` shows `drwx------` (700)
- [ ] File permissions: `ls -la /opt/kiosk/secrets/.env.prod` shows `-rw-------` (600)
- [ ] Secrets are different from development
- [ ] No "GENERATE_RANDOM" placeholders remain
- [ ] ALLOWED_ORIGINS matches your domain
- [ ] DATABASE_URL uses strong password
- [ ] Application deploys successfully
- [ ] Secrets saved in password manager

### Git Repository

- [ ] `.env.example` committed to git
- [ ] `.env.prod.example` committed to git
- [ ] `.gitignore` includes `.env` and `*.env`
- [ ] No real secrets in git history (`git log --all --full-history -- "*env"`)
- [ ] GitHub doesn't show any secrets in code search

---

## 🆘 Emergency: Secrets Exposed

**If secrets are leaked (committed to git, sent in email, etc.):**

### Immediate Actions (Do Within 1 Hour)

1. **Rotate ALL secrets immediately:**
```bash
# Production server
ssh kiosk@YOUR_SERVER_IP
cd /opt/kiosk
# Generate new secrets and update .env.prod
# Restart services
docker compose restart
```

2. **Change database password:**
```bash
# Connect to PostgreSQL
docker compose exec postgres psql -U kiosk_user -d kiosk_db

# Change password
ALTER USER kiosk_user WITH PASSWORD 'NEW_STRONG_PASSWORD';
\q

# Update .env.prod with new password
# Restart backend
docker compose restart backend
```

3. **If secrets in git history:**
```bash
# Remove from git (requires force push)
git filter-branch --force --index-filter \
  "git rm --cached --ignore-unmatch backend/.env" \
  --prune-empty --tag-name-filter cat -- --all

git push origin --force --all
```

4. **Notify team:**
- Everyone must pull latest code
- Everyone must regenerate dev secrets
- All production users must re-login

---

## 📚 Summary

### Golden Rules

1. ✅ **Generate unique secrets per environment** (dev ≠ prod)
2. ✅ **Never commit real secrets to git** (only .example files)
3. ✅ **Use strong random secrets** (64-char hex minimum)
4. ✅ **Secure file permissions** (600 for files, 700 for directories)
5. ✅ **Store in password manager** (backup for disasters)
6. ✅ **Rotate regularly** (every 12 months minimum)

### Quick Reference

| Secret Type | Where | Permissions | Git |
|------------|-------|-------------|-----|
| backend/.env (dev) | Your Mac | 600 | ❌ No |
| .env.example | Repository | 644 | ✅ Yes |
| .env.prod (prod) | /opt/kiosk/secrets/ | 600 | ❌ No |
| .env.prod.example | Repository | 644 | ✅ Yes |

**You're all set!** Your secrets are now properly managed. 🔒

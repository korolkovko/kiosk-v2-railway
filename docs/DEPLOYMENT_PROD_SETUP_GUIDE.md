# DEPLOYMENT_PROD_SETUP_GUIDE.md
# Production Server Setup and Deployment Guide

## 📚 Related Documentation

- **[DEPLOYMENT_LOCAL_SETUP_GUIDE.md](./DEPLOYMENT_LOCAL_SETUP_GUIDE.md)** - Local development setup
- **[DEPLOYMENT_DOCKER_STRATEGY.md](./DEPLOYMENT_DOCKER_STRATEGY.md)** - Docker strategy overview
- **[DEPLOYMENT_SECRETS_MANAGEMENT.md](./DEPLOYMENT_SECRETS_MANAGEMENT.md)** - Secrets management guide

---

## 🎯 Overview

This guide walks you through deploying your KIOSK application to a production VPS server from scratch.

**What you'll set up:**
- ✅ Ubuntu 22.04 LTS server
- ✅ Docker + Docker Compose
- ✅ PostgreSQL in Docker
- ✅ Backend API in Docker
- ✅ Frontend in Docker
- ✅ Nginx reverse proxy
- ✅ HTTPS with Let's Encrypt (free SSL)
- ✅ Automatic deployment from GitHub

**Time required:** 1-2 hours (first time)

---

## 📋 Prerequisites

### 1. VPS Server

**Recommended Providers:**
- **Hetzner Cloud** (Europe, cheapest) - €4-20/month
- **DigitalOcean** (Popular, easy) - $6-20/month
- **Vultr** (Global locations) - $6-20/month

**Minimum Server Specs:**
| Kiosks | CPU | RAM | Storage | Monthly Cost |
|--------|-----|-----|---------|--------------|
| 1-5 | 2 cores | 4 GB | 50 GB | ~$12 |
| 5-20 | 4 cores | 8 GB | 100 GB | ~$24 |
| 20+ | 8 cores | 16 GB | 200 GB | ~$48 |

**Operating System:** Ubuntu 22.04 LTS (choose this when creating server)

### 2. Domain Name (Required for SSL)

You need a domain pointing to your server:
```
Example: kiosk.yourdomain.com → Server IP address
```

**How to set up DNS:**
1. Buy domain (Namecheap, Cloudflare, any registrar)
2. Add A record:
   ```
   Type: A
   Name: kiosk (or @)
   Value: Your server IP address
   TTL: 3600
   ```
3. Wait 10-60 minutes for DNS propagation

### 3. GitHub Repository

Your code must be in a GitHub repository (private or public).

---

## 🚀 Step-by-Step Production Setup

### Step 1: Server Initial Setup (15 minutes)

#### 1.1 Connect to Your Server

```bash
# Replace YOUR_SERVER_IP with actual IP
ssh root@YOUR_SERVER_IP

# First login will ask to accept fingerprint, type "yes"
```

#### 1.2 Create Non-Root User (Security)

```bash
# Create user 'kiosk'
adduser kiosk
# Enter password when prompted (save this password!)

# Give sudo privileges
usermod -aG sudo kiosk

# Allow SSH for this user
mkdir -p /home/kiosk/.ssh
cp ~/.ssh/authorized_keys /home/kiosk/.ssh/
chown -R kiosk:kiosk /home/kiosk/.ssh
chmod 700 /home/kiosk/.ssh
chmod 600 /home/kiosk/.ssh/authorized_keys

# Switch to kiosk user
su - kiosk
```

**From now on, use:** `ssh kiosk@YOUR_SERVER_IP`

#### 1.3 Update System

```bash
# Update package lists
sudo apt update

# Upgrade installed packages
sudo apt upgrade -y

# Install essential tools
sudo apt install -y curl wget git vim ufw
```

#### 1.4 Configure Firewall

```bash
# Allow SSH (port 22)
sudo ufw allow 22/tcp

# Allow HTTP (port 80)
sudo ufw allow 80/tcp

# Allow HTTPS (port 443)
sudo ufw allow 443/tcp

# Enable firewall
sudo ufw enable

# Check status
sudo ufw status
```

Expected output:
```
Status: active

To                         Action      From
--                         ------      ----
22/tcp                     ALLOW       Anywhere
80/tcp                     ALLOW       Anywhere
443/tcp                     ALLOW       Anywhere
```

---

### Step 2: Install Docker (10 minutes)

#### 2.1 Install Docker

```bash
# Remove old versions (if any)
sudo apt remove docker docker-engine docker.io containerd runc || true

# Install dependencies
sudo apt install -y apt-transport-https ca-certificates curl software-properties-common

# Add Docker's official GPG key
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg

# Add Docker repository
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# Install Docker
sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# Add current user to docker group (no sudo needed)
sudo usermod -aG docker $USER

# Apply group changes (re-login)
newgrp docker
```

#### 2.2 Verify Docker Installation

```bash
# Check Docker version
docker --version
# Expected: Docker version 24.x.x or higher

# Check Docker Compose version
docker compose version
# Expected: Docker Compose version v2.x.x or higher

# Test Docker
docker run hello-world
# Should download and run successfully
```

#### 2.3 Configure Docker (Optional Performance Tuning)

```bash
# Create Docker daemon config
sudo mkdir -p /etc/docker
sudo tee /etc/docker/daemon.json <<EOF
{
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "10m",
    "max-file": "3"
  },
  "storage-driver": "overlay2"
}
EOF

# Restart Docker
sudo systemctl restart docker
```

---

### Step 3: Clone Your Repository (5 minutes)

#### 3.1 Set Up SSH Key for GitHub (Recommended)

```bash
# Generate SSH key on server
ssh-keygen -t ed25519 -C "your-email@example.com"
# Press Enter for all prompts (default location, no passphrase for automation)

# Display public key
cat ~/.ssh/id_ed25519.pub
```

**Copy the output** and add to GitHub:
1. Go to GitHub → Settings → SSH and GPG keys
2. Click "New SSH key"
3. Paste the public key
4. Save

#### 3.2 Clone Repository

```bash
# Create application directory
sudo mkdir -p /opt/kiosk
sudo chown kiosk:kiosk /opt/kiosk
cd /opt/kiosk

# Clone your repository
git clone git@github.com:YOUR_USERNAME/YOUR_REPO.git .

# Verify files
ls -la
# Should see: backend/, frontend/, scripts/, docker-compose.yml, etc.
```

---

### Step 4: Set Up Production Secrets (10 minutes)

See [DEPLOYMENT_SECRETS_MANAGEMENT.md](./DEPLOYMENT_SECRETS_MANAGEMENT.md) for detailed guide.

#### 4.1 Create Secrets Directory

```bash
# Create secure directory for secrets
sudo mkdir -p /opt/kiosk/secrets
sudo chown kiosk:kiosk /opt/kiosk/secrets
chmod 700 /opt/kiosk/secrets
```

#### 4.2 Generate Production Secrets

```bash
# Generate random secrets
SECRET_KEY=$(openssl rand -hex 32)
JWT_SECRET_KEY=$(openssl rand -hex 32)
KIOSK_JWT_SECRET_KEY=$(openssl rand -hex 32)
DB_PASSWORD=$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-25)

# Display generated secrets (SAVE THESE!)
echo "SECRET_KEY=$SECRET_KEY"
echo "JWT_SECRET_KEY=$JWT_SECRET_KEY"
echo "KIOSK_JWT_SECRET_KEY=$KIOSK_JWT_SECRET_KEY"
echo "DB_PASSWORD=$DB_PASSWORD"
```

**⚠️ IMPORTANT:** Copy these values somewhere safe (password manager, secure note)

#### 4.3 Create .env.prod File

```bash
# Create production environment file
cat > /opt/kiosk/secrets/.env.prod <<'EOF'
# KIOSK Production Environment

# Application
HOST=0.0.0.0
PORT=8000
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=INFO

# Database
DATABASE_URL=postgresql://kiosk_user:REPLACE_DB_PASSWORD@postgres:5432/kiosk_db

# Security Keys
SECRET_KEY=REPLACE_SECRET_KEY
JWT_SECRET_KEY=REPLACE_JWT_SECRET_KEY
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# Kiosk Authentication
KIOSK_JWT_SECRET_KEY=REPLACE_KIOSK_JWT_SECRET_KEY
KIOSK_JWT_ALGORITHM=HS256
KIOSK_ACCESS_TOKEN_EXPIRE_DAYS=30
KIOSK_REFRESH_TOKEN_EXPIRE_DAYS=90
KIOSK_JWT_KEY_ID=kiosk-prod-2025-v1

# File Uploads
MAX_FILE_SIZE=10485760
UPLOAD_PATH=/var/kiosk/uploads

# Media Storage
MEDIA_PATH=/var/kiosk/media

# Logging
LOG_FILE_PATH=/var/log/kiosk/app.log

# CORS (replace with your domain)
ALLOWED_ORIGINS=["https://kiosk.yourdomain.com","https://yourdomain.com"]

# External Integrations (optional)
POS_API_URL=
POS_API_KEY=
PAYMENT_API_URL=
PAYMENT_API_KEY=
EOF

# Replace placeholders with generated secrets
sed -i "s|REPLACE_DB_PASSWORD|$DB_PASSWORD|g" /opt/kiosk/secrets/.env.prod
sed -i "s|REPLACE_SECRET_KEY|$SECRET_KEY|g" /opt/kiosk/secrets/.env.prod
sed -i "s|REPLACE_JWT_SECRET_KEY|$JWT_SECRET_KEY|g" /opt/kiosk/secrets/.env.prod
sed -i "s|REPLACE_KIOSK_JWT_SECRET_KEY|$KIOSK_JWT_SECRET_KEY|g" /opt/kiosk/secrets/.env.prod

# Secure file permissions
chmod 600 /opt/kiosk/secrets/.env.prod

# Verify file
cat /opt/kiosk/secrets/.env.prod
```

**Update ALLOWED_ORIGINS** with your actual domain:
```bash
# Edit the file
nano /opt/kiosk/secrets/.env.prod

# Change this line:
ALLOWED_ORIGINS=["https://kiosk.yourdomain.com","https://yourdomain.com"]
# To your actual domain:
ALLOWED_ORIGINS=["https://kiosk.example.com","https://example.com"]

# Save: Ctrl+O, Enter, Ctrl+X
```

---

### Step 5: Create Production Directories (2 minutes)

```bash
# Create data directories
sudo mkdir -p /var/kiosk/{uploads,media,logs}
sudo mkdir -p /var/lib/postgresql/data

# Set ownership
sudo chown -R kiosk:kiosk /var/kiosk
sudo chmod -R 755 /var/kiosk

# Create log directory with proper permissions
sudo mkdir -p /var/log/kiosk
sudo chown -R kiosk:kiosk /var/log/kiosk
sudo chmod 755 /var/log/kiosk
```

---

### Step 6: Deploy Application (10 minutes)

#### 6.1 First Deployment

```bash
cd /opt/kiosk

# Build and start all services
docker compose -f docker-compose.yml \
               -f docker-compose.prod.yml \
               --env-file /opt/kiosk/secrets/.env.prod \
               up -d --build

# This will:
# 1. Build backend Docker image (2-3 minutes)
# 2. Build frontend Docker image (2-3 minutes)
# 3. Start PostgreSQL
# 4. Start backend (4 workers)
# 5. Start frontend
# 6. Start nginx reverse proxy

# Wait for build to complete...
```

#### 6.2 Check Deployment Status

```bash
# Check running containers
docker ps

# Expected output (4 containers):
# kiosk_postgres
# kiosk_backend
# kiosk_frontend_kiosk
# kiosk_nginx

# Check container logs
docker compose logs -f

# Press Ctrl+C to exit logs
```

#### 6.3 Verify Services

```bash
# Test backend health
curl http://localhost:8001/health
# Expected: {"status":"ok"}

# Test nginx is running
curl http://localhost
# Expected: HTML content or proxy response

# Check PostgreSQL
docker exec kiosk_postgres pg_isready -U kiosk_user -d kiosk_db
# Expected: accepting connections
```

---

### Step 7: Set Up SSL/HTTPS with Let's Encrypt (15 minutes)

#### 7.1 Install Certbot

```bash
# Install Certbot
sudo apt install -y certbot python3-certbot-nginx
```

#### 7.2 Stop Nginx Temporarily

```bash
# Stop nginx container to free port 80
docker compose -f docker-compose.prod.yml stop nginx
```

#### 7.3 Obtain SSL Certificate

```bash
# Request certificate (replace with your domain)
sudo certbot certonly --standalone \
  -d kiosk.yourdomain.com \
  --email your-email@example.com \
  --agree-tos \
  --no-eff-email

# Follow prompts
# Certificate will be saved to:
# /etc/letsencrypt/live/kiosk.yourdomain.com/fullchain.pem
# /etc/letsencrypt/live/kiosk.yourdomain.com/privkey.pem
```

#### 7.4 Copy Certificates to Application Directory

```bash
# Create SSL directory
mkdir -p /opt/kiosk/deployment/ssl

# Copy certificates
sudo cp /etc/letsencrypt/live/kiosk.yourdomain.com/fullchain.pem \
        /opt/kiosk/deployment/ssl/
sudo cp /etc/letsencrypt/live/kiosk.yourdomain.com/privkey.pem \
        /opt/kiosk/deployment/ssl/

# Fix permissions
sudo chown -R kiosk:kiosk /opt/kiosk/deployment/ssl
sudo chmod 644 /opt/kiosk/deployment/ssl/fullchain.pem
sudo chmod 600 /opt/kiosk/deployment/ssl/privkey.pem
```

#### 7.5 Update Nginx Configuration for HTTPS

Create nginx production config:
```bash
mkdir -p /opt/kiosk/deployment/nginx

cat > /opt/kiosk/deployment/nginx/nginx.prod.conf <<'EOF'
events {
    worker_connections 1024;
}

http {
    include /etc/nginx/mime.types;
    default_type application/octet-stream;

    # Logging
    access_log /var/log/nginx/access.log;
    error_log /var/log/nginx/error.log;

    # Performance
    sendfile on;
    tcp_nopush on;
    tcp_nodelay on;
    keepalive_timeout 65;
    types_hash_max_size 2048;

    # Gzip compression
    gzip on;
    gzip_vary on;
    gzip_proxied any;
    gzip_comp_level 6;
    gzip_types text/plain text/css text/xml text/javascript
               application/json application/javascript application/xml+rss;

    # HTTP to HTTPS redirect
    server {
        listen 80;
        server_name kiosk.yourdomain.com;  # CHANGE THIS

        location / {
            return 301 https://$server_name$request_uri;
        }
    }

    # HTTPS server
    server {
        listen 443 ssl http2;
        server_name kiosk.yourdomain.com;  # CHANGE THIS

        # SSL certificates
        ssl_certificate /etc/nginx/ssl/fullchain.pem;
        ssl_certificate_key /etc/nginx/ssl/privkey.pem;

        # SSL configuration
        ssl_protocols TLSv1.2 TLSv1.3;
        ssl_ciphers HIGH:!aNULL:!MD5;
        ssl_prefer_server_ciphers on;

        # Security headers
        add_header X-Frame-Options "SAMEORIGIN" always;
        add_header X-Content-Type-Options "nosniff" always;
        add_header X-XSS-Protection "1; mode=block" always;

        # Serve frontend
        location / {
            proxy_pass http://kiosk-frontend:80;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }

        # Backend API
        location /api/ {
            proxy_pass http://backend:8000/api/;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;

            # WebSocket support (for SSE)
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection "upgrade";
            proxy_read_timeout 86400;
        }

        # API documentation
        location /docs {
            proxy_pass http://backend:8000/docs;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
        }

        # Media files
        location /media/ {
            alias /var/kiosk/media/;
            expires 30d;
            add_header Cache-Control "public, immutable";
        }
    }
}
EOF

# Replace domain name
read -p "Enter your domain (e.g., kiosk.yourdomain.com): " DOMAIN
sed -i "s/kiosk.yourdomain.com/$DOMAIN/g" /opt/kiosk/deployment/nginx/nginx.prod.conf
```

#### 7.6 Restart Services with SSL

```bash
cd /opt/kiosk

# Restart all services
docker compose -f docker-compose.yml \
               -f docker-compose.prod.yml \
               --env-file /opt/kiosk/secrets/.env.prod \
               restart

# Check nginx logs
docker compose logs nginx

# Should see: "nginx: configuration file ... test is successful"
```

#### 7.7 Set Up Automatic Certificate Renewal

```bash
# Test renewal (dry run)
sudo certbot renew --dry-run

# If successful, certbot will auto-renew every 60 days
# Check renewal timer
sudo systemctl status certbot.timer
```

---

### Step 8: Run Database Migrations (5 minutes)

```bash
cd /opt/kiosk

# Run migrations inside backend container
docker compose exec backend alembic upgrade head

# Expected output: migrations applied successfully
```

---

### Step 9: Create SuperAdmin User (2 minutes)

```bash
# Use the backend API to create superadmin
# Option 1: Via curl
curl -X POST https://kiosk.yourdomain.com/api/v1/setup/superadmin \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin",
    "password": "YourSecurePassword123!",
    "email": "admin@yourdomain.com"
  }'

# Option 2: Via browser
# Visit: https://kiosk.yourdomain.com/docs
# Find POST /setup/superadmin endpoint
# Click "Try it out"
# Fill in credentials and execute
```

**Save the admin credentials securely!**

---

### Step 10: Verify Production Deployment (5 minutes)

#### 10.1 Check All Services

```bash
# Check containers
docker ps

# All 4 containers should be running:
# ✅ kiosk_postgres (Up)
# ✅ kiosk_backend (Up, healthy)
# ✅ kiosk_frontend_kiosk (Up)
# ✅ kiosk_nginx (Up)

# Check logs
docker compose logs --tail=50

# No errors should be present
```

#### 10.2 Test HTTPS Access

```bash
# Test redirect (HTTP → HTTPS)
curl -I http://kiosk.yourdomain.com
# Expected: 301 Moved Permanently, Location: https://...

# Test HTTPS
curl -I https://kiosk.yourdomain.com
# Expected: 200 OK

# Test backend API
curl https://kiosk.yourdomain.com/api/v1/health
# Expected: {"status":"ok"}

# Test API docs
curl https://kiosk.yourdomain.com/docs
# Expected: HTML content (Swagger UI)
```

#### 10.3 Test from Browser

Open in browser:
- ✅ https://kiosk.yourdomain.com (frontend should load)
- ✅ https://kiosk.yourdomain.com/docs (API documentation)
- ✅ Verify SSL certificate (padlock icon in browser)

---

## 🔄 Deployment Workflow

### Manual Deployment (SSH)

When you have code changes to deploy:

```bash
# 1. SSH to server
ssh kiosk@YOUR_SERVER_IP

# 2. Navigate to application directory
cd /opt/kiosk

# 3. Pull latest code
git pull origin main

# 4. Rebuild and restart services
docker compose -f docker-compose.yml \
               -f docker-compose.prod.yml \
               --env-file /opt/kiosk/secrets/.env.prod \
               up -d --build

# 5. Run migrations (if any)
docker compose exec backend alembic upgrade head

# 6. Check status
docker compose ps
docker compose logs --tail=100

# Done!
```

### Automated Deployment with GitHub Actions (Optional)

See section below for setting up automatic deployment on every push.

---

## 🤖 Optional: GitHub Actions Auto-Deployment

### Benefits
- ✅ Automatic deployment on push to main branch
- ✅ No manual SSH needed
- ✅ Deployment history in GitHub

### Setup (30 minutes)

#### 1. Create Deployment Key on Server

```bash
# On your server
cd /opt/kiosk

# Generate deployment SSH key (no passphrase)
ssh-keygen -t ed25519 -f ~/.ssh/github_deploy -C "github-actions-deploy"

# Display public key
cat ~/.ssh/github_deploy.pub
# Copy this, we'll use it in GitHub
```

#### 2. Add Deploy Key to GitHub Repository

1. Go to your GitHub repository
2. Settings → Deploy keys → Add deploy key
3. Title: "GitHub Actions Deploy"
4. Key: Paste the public key from above
5. ✅ Check "Allow write access"
6. Click "Add key"

#### 3. Add Server SSH Key to GitHub Secrets

```bash
# On your server, display private key
cat ~/.ssh/github_deploy
# Copy entire content including -----BEGIN and -----END lines
```

1. Go to GitHub repository → Settings → Secrets and variables → Actions
2. Click "New repository secret"
3. Name: `SSH_PRIVATE_KEY`
4. Value: Paste the private key
5. Click "Add secret"

Add more secrets:
- `SSH_HOST` = your server IP address
- `SSH_USER` = `kiosk`
- `SSH_PORT` = `22`

#### 4. Create GitHub Actions Workflow

Create file `.github/workflows/deploy.yml`:

```yaml
name: Deploy to Production

on:
  push:
    branches:
      - main

jobs:
  deploy:
    runs-on: ubuntu-latest

    steps:
      - name: Deploy to production server
        uses: appleboy/ssh-action@v1.0.0
        with:
          host: ${{ secrets.SSH_HOST }}
          username: ${{ secrets.SSH_USER }}
          key: ${{ secrets.SSH_PRIVATE_KEY }}
          port: ${{ secrets.SSH_PORT }}
          script: |
            cd /opt/kiosk
            git pull origin main
            docker compose -f docker-compose.yml \
                           -f docker-compose.prod.yml \
                           --env-file /opt/kiosk/secrets/.env.prod \
                           up -d --build
            docker compose exec -T backend alembic upgrade head
            docker compose ps
            echo "✅ Deployment completed successfully!"
```

#### 5. Test Auto-Deployment

```bash
# On your Mac, make a small change and push
git add .
git commit -m "Test auto-deployment"
git push origin main

# Watch GitHub Actions run
# GitHub → Your repo → Actions tab
# Should see "Deploy to Production" workflow running

# After ~3-5 minutes, deployment completes automatically!
```

---

## 🔧 Useful Commands

### View Logs
```bash
# All services
docker compose logs -f

# Specific service
docker compose logs -f backend
docker compose logs -f postgres
docker compose logs -f nginx

# Last 100 lines
docker compose logs --tail=100
```

### Restart Services
```bash
# Restart all
docker compose restart

# Restart specific service
docker compose restart backend
docker compose restart nginx
```

### Stop/Start Services
```bash
# Stop all
docker compose down

# Start all
docker compose -f docker-compose.yml \
               -f docker-compose.prod.yml \
               --env-file /opt/kiosk/secrets/.env.prod \
               up -d
```

### Database Operations
```bash
# PostgreSQL shell
docker compose exec postgres psql -U kiosk_user -d kiosk_db

# Run SQL query
docker compose exec -T postgres psql -U kiosk_user -d kiosk_db -c "SELECT COUNT(*) FROM users;"

# Database backup
docker compose exec -T postgres pg_dump -U kiosk_user kiosk_db > backup_$(date +%Y%m%d).sql
```

### Check Resource Usage
```bash
# Container resource usage
docker stats

# Disk usage
docker system df

# Clean up unused images/containers
docker system prune -a
```

---

## 🔒 Security Checklist

After deployment, verify:

- ✅ Firewall enabled (only ports 22, 80, 443 open)
- ✅ SSH key authentication (disable password login)
- ✅ Non-root user for application
- ✅ .env.prod file permissions (chmod 600)
- ✅ HTTPS with valid SSL certificate
- ✅ Strong passwords for database and admin users
- ✅ Regular backups configured
- ✅ Application logs monitored

---

## 🐛 Troubleshooting

### Container Won't Start
```bash
# Check logs
docker compose logs backend

# Common issues:
# - Port already in use: Check with `sudo lsof -i :8000`
# - Permission denied: Check volume permissions
# - Database not ready: Wait longer, check postgres logs
```

### SSL Certificate Issues
```bash
# Test certificate renewal
sudo certbot renew --dry-run

# If failed, manually renew
sudo certbot renew --force-renewal

# Copy new certificates
sudo cp /etc/letsencrypt/live/*/fullchain.pem /opt/kiosk/deployment/ssl/
sudo cp /etc/letsencrypt/live/*/privkey.pem /opt/kiosk/deployment/ssl/
sudo chown kiosk:kiosk /opt/kiosk/deployment/ssl/*
docker compose restart nginx
```

### Database Connection Issues
```bash
# Check PostgreSQL is running
docker compose ps postgres

# Check connection from backend
docker compose exec backend python -c "from app.database import engine; engine.connect(); print('✅ Database connected')"

# Check DATABASE_URL in .env.prod
grep DATABASE_URL /opt/kiosk/secrets/.env.prod
```

### Can't Access Application
```bash
# Check nginx is running
docker compose ps nginx

# Check nginx config
docker compose exec nginx nginx -t

# Check DNS
nslookup kiosk.yourdomain.com

# Check firewall
sudo ufw status
```

---

## 📈 Monitoring & Maintenance

### Daily Checks
```bash
# Check all containers are running
docker compose ps

# Check logs for errors
docker compose logs --since 24h | grep -i error
```

### Weekly Maintenance
```bash
# Update system packages
sudo apt update && sudo apt upgrade -y

# Clean up Docker
docker system prune -f

# Check disk space
df -h
```

### Monthly Tasks
- Review application logs
- Check SSL certificate expiry (should auto-renew)
- Test backups restore
- Update dependencies (if needed)

---

## ✅ Success!

Your KIOSK application is now running in production! 🎉

**Access your application:**
- 🌐 Frontend: https://kiosk.yourdomain.com
- 📚 API Docs: https://kiosk.yourdomain.com/docs
- 🔐 Admin: Use credentials created in Step 9

**Next steps:**
1. Test all features thoroughly
2. Set up database backups (see backup scripts)
3. Configure monitoring (optional)
4. Document any custom configurations

**Need help?** Review the troubleshooting section or check related documentation guides.

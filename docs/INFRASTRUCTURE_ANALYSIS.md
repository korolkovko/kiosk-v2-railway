# INFRASTRUCTURE_ANALYSIS.md
# Infrastructure Components Analysis for Production Deployment

## 📊 Current Docker Services Overview

### 1. **PostgreSQL** (postgres:15-alpine)
**Purpose**: Primary relational database for application data
**Current Usage**: 
- Stores all application data (users, items, orders, categories, menus, etc.)
- Used by backend via SQLAlchemy ORM
- Database migrations managed by Alembic

**Production Necessity**: ✅ **CRITICAL - REQUIRED**
- Cannot run application without database
- All business logic depends on it
- Contains persistent state

**Kubernetes Strategy**: 
- Deploy as StatefulSet with persistent volume
- OR use managed database service (AWS RDS, Google Cloud SQL)

**Docker on Server Strategy**:
- Keep as separate container with named volume
- Use Docker volume for persistence
- Implement backup strategy (pg_dump scheduled via cron)

---

### 2. **Redis** (redis:7-alpine)
**Purpose**: Caching and session storage
**Current Usage**: 
- ❌ **NOT ACTUALLY USED** - Only configured in settings but no implementation found
- REDIS_URL defined in config.py but no redis client initialization
- No cache decorators or session storage found in codebase

**Production Necessity**: ❌ **NOT REQUIRED - CAN BE REMOVED**
- Application works without it
- No performance impact from removal
- Can be added later if caching is needed

**Recommendation**: 
- **Remove from docker-compose.yml**
- Remove REDIS_URL from backend/.env
- Remove redis from requirements.txt
- Can add back later when implementing caching

---

### 3. **Backend** (FastAPI Python Application)
**Purpose**: REST API server and business logic
**Current Usage**:
- FastAPI application with multiple endpoints
- Authentication (JWT for admin, extended JWT for kiosks)
- Database operations via SQLAlchemy
- SSE (Server-Sent Events) for real-time updates using in-memory event bus
- External integrations (payment, fiscal, printer, KDS)
- File serving (uploads, media)

**Production Necessity**: ✅ **CRITICAL - REQUIRED**
- Core application logic
- API endpoints for frontend
- Business rules and data processing

**Kubernetes Strategy**:
- Deploy as Deployment with 2-10 replicas
- Horizontal Pod Autoscaler based on CPU/memory
- Health checks and readiness probes

**Docker on Server Strategy**:
- Single container (or 2-3 for redundancy with load balancer)
- Restart policy: always
- Health checks via Docker HEALTHCHECK
- Bind to internal network only (not exposed directly)

**Important Notes**:
- Uses **in-memory event bus** for SSE (not Redis)
- Event bus is process-local, so SSE connections tied to specific pod/container
- Need sticky sessions or Redis pub/sub for multi-instance SSE in production

---

### 4. **Frontend - Kiosk** (React/Vite + Nginx)
**Purpose**: Customer-facing kiosk interface
**Current Usage**:
- React 19 application with TypeScript
- Vite for build tooling
- Nginx for serving static files
- Connects to backend API

**Production Necessity**: ✅ **CRITICAL - REQUIRED**
- Primary user interface
- Customer interaction point

**Kubernetes Strategy**:
- Deploy as Deployment with 2-5 replicas
- Nginx serves static files
- No persistent storage needed (stateless)

**Docker on Server Strategy**:
- Single Nginx container serving static files
- Restart policy: always
- Can run multiple instances behind load balancer if needed
- Very lightweight, minimal resources

---

### 5. **Frontend - Admin** (Not in current docker-compose)
**Purpose**: Admin interface for managing kiosk
**Current Status**: 
- Directory exists in frontend/apps/admin
- Not currently deployed in docker-compose
- Profile-based deployment available

**Production Necessity**: ⚠️ **OPTIONAL - DEPENDS ON REQUIREMENTS**
- Needed if admin management is required
- Can be deployed separately

---

### 6. **Frontend - SuperAdmin** (Not in current docker-compose)
**Purpose**: Super admin interface
**Current Status**:
- Directory exists in frontend/apps/super-admin
- Not currently deployed in docker-compose
- Profile-based deployment available

**Production Necessity**: ⚠️ **OPTIONAL - DEPENDS ON REQUIREMENTS**
- Needed if super admin features are required
- Can be deployed separately

---

### 7. **pgAdmin** (dpage/pgadmin4)
**Purpose**: Database management GUI tool
**Current Usage**:
- Development tool for database inspection
- Runs on profile "tools"

**Production Necessity**: ❌ **NOT REQUIRED - DEVELOPMENT ONLY**
- Only for development/debugging
- Should NOT be deployed to production
- Use database client tools or cloud provider console instead

**Recommendation**: 
- **Remove from production deployment**
- Keep in docker-compose for local development only

---

## 📋 Summary: What to Keep vs Remove

### ✅ KEEP FOR PRODUCTION:
1. **PostgreSQL** - Critical database
2. **Backend API** - Core application
3. **Frontend Kiosk** - Primary UI

### ❌ REMOVE FROM PRODUCTION:
1. **Redis** - Not used, can remove entirely
2. **pgAdmin** - Development tool only

### ⚠️ DECIDE BASED ON REQUIREMENTS:
1. **Admin Frontend** - If admin features needed
2. **SuperAdmin Frontend** - If super admin features needed

---

## 🔍 Critical Finding: SSE Event Bus Architecture

**Current Implementation**:
```python
# backend/app/websockets/event_bus.py
# In-memory event bus for single process
class EventBus:
    def __init__(self):
        self._subs: Dict[str, Set[asyncio.Queue]] = defaultdict(set)
```

**Problem for Multi-Instance Deployment**:
- Event bus is **in-memory** and **process-local**
- SSE connections are tied to specific backend pod/container
- If pod/container restarts or scales, connections lost
- Events published to one instance won't reach clients connected to other instances

**Solutions for Production**:
1. **Sticky Sessions** (simplest):
   - Configure load balancer with session affinity
   - Clients always connect to same instance
   - Limitation: No cross-instance event broadcasting

2. **Redis Pub/Sub** (recommended):
   - Replace in-memory event bus with Redis
   - All instances share same event channel
   - Clients can connect to any instance
   - Events broadcast across all instances

3. **External Message Broker**:
   - Use RabbitMQ, NATS, or Kafka
   - More complex but more scalable

---

## 📦 Storage Requirements Analysis

### Current Volumes:
1. **postgres_data** - Database files (CRITICAL)
2. **redis_data** - Can be removed (Redis not used)
3. **uploads** - User uploaded files (REQUIRED)
4. **media** - Media assets (REQUIRED)
5. **logs** - Application logs (OPTIONAL - better to use log aggregation)

### Kubernetes Storage Strategy:
- **Database**: PersistentVolume with StatefulSet OR managed service
- **Uploads/Media**: ReadWriteMany PVC (NFS or cloud storage)
- **Logs**: Use stdout/stderr + log aggregation (Fluentd/Loki)

### Docker on Server Storage Strategy:
- **Database**: Named Docker volume with backup strategy
- **Uploads/Media**: Bind mount to host directory (e.g., /var/kiosk/uploads, /var/kiosk/media)
- **Logs**: Bind mount to host directory (e.g., /var/log/kiosk) OR use Docker logging driver

---

# 🐳 DOCKER ON VIRTUAL/DEDICATED SERVER DEPLOYMENT

## Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│              Virtual/Dedicated Server                    │
│                  (Ubuntu/Debian/CentOS)                  │
├─────────────────────────────────────────────────────────┤
│                                                           │
│  ┌──────────────────────────────────────────────────┐  │
│  │         Reverse Proxy (Nginx/Traefik)            │  │
│  │         - SSL/TLS termination                     │  │
│  │         - Port 80/443 → containers                │  │
│  └──────────────────────────────────────────────────┘  │
│                         │                                │
│         ┌───────────────┼───────────────┐               │
│         │               │               │               │
│  ┌──────▼──────┐ ┌─────▼──────┐ ┌─────▼──────┐        │
│  │  Frontend   │ │  Backend   │ │ PostgreSQL │        │
│  │  Container  │ │ Container  │ │ Container  │        │
│  │  (Nginx)    │ │ (FastAPI)  │ │            │        │
│  │  Port: 8080 │ │ Port: 8001 │ │ Port: 5433 │        │
│  └─────────────┘ └────────────┘ └────────────┘        │
│                         │                                │
│                         │                                │
│  ┌─────────────────────────────────────────────────┐   │
│  │         Host Filesystem Mounts                   │   │
│  │  /var/kiosk/uploads  → Backend uploads          │   │
│  │  /var/kiosk/media    → Backend media            │   │
│  │  /var/kiosk/postgres → Database data            │   │
│  │  /var/log/kiosk      → Application logs         │   │
│  └─────────────────────────────────────────────────┘   │
│                                                           │
└─────────────────────────────────────────────────────────┘
```

## Production-Ready Docker Compose Structure

### File Structure:
```
/opt/kiosk/
├── docker-compose.prod.yml
├── .env.prod
├── nginx/
│   ├── nginx.conf
│   └── ssl/
│       ├── cert.pem
│       └── key.pem
├── backend/
│   └── Dockerfile.prod
├── frontend/
│   └── Dockerfile.prod
└── scripts/
    ├── backup-db.sh
    ├── restore-db.sh
    └── deploy.sh
```

## Key Differences from Development Setup

### 1. **Remove Development Tools**
- ❌ Remove pgAdmin
- ❌ Remove Redis (not used)
- ❌ Remove volume mounts for hot-reload
- ❌ Remove debug ports

### 2. **Add Production Components**
- ✅ Reverse proxy (Nginx or Traefik)
- ✅ SSL/TLS certificates
- ✅ Proper logging configuration
- ✅ Health checks
- ✅ Restart policies
- ✅ Resource limits

### 3. **Security Hardening**
- ✅ Non-root users in containers
- ✅ Read-only root filesystems where possible
- ✅ Secrets management (not in docker-compose file)
- ✅ Network isolation
- ✅ Firewall rules (UFW/iptables)

### 4. **Networking**
```yaml
networks:
  frontend:
    # Only reverse proxy and frontend
  backend:
    # Frontend, backend, database
    internal: true  # No external access
```

### 5. **Volumes Strategy**
```yaml
volumes:
  postgres_data:
    driver: local
    driver_opts:
      type: none
      o: bind
      device: /var/kiosk/postgres
  
  uploads:
    driver: local
    driver_opts:
      type: none
      o: bind
      device: /var/kiosk/uploads
```

## Deployment Checklist for Docker on Server

### Pre-Deployment:
- [ ] Server provisioned (Ubuntu 22.04 LTS recommended)
- [ ] Docker and Docker Compose installed
- [ ] Domain name configured (DNS A record)
- [ ] SSL certificate obtained (Let's Encrypt)
- [ ] Firewall configured (ports 80, 443, 22 only)
- [ ] Create application user (non-root)
- [ ] Create directory structure (/var/kiosk/*)

### Configuration:
- [ ] Create .env.prod with production values
- [ ] Configure database credentials (strong passwords)
- [ ] Set JWT secret keys (random, secure)
- [ ] Configure external API endpoints
- [ ] Set up backup script with cron job
- [ ] Configure log rotation

### Deployment:
- [ ] Build production Docker images
- [ ] Push images to registry (optional)
- [ ] Deploy with docker-compose up -d
- [ ] Run database migrations
- [ ] Verify health checks
- [ ] Test SSL certificate
- [ ] Test application functionality

### Post-Deployment:
- [ ] Set up monitoring (Prometheus + Grafana)
- [ ] Configure log aggregation
- [ ] Set up automated backups
- [ ] Document rollback procedure
- [ ] Create maintenance runbook

## Resource Requirements

### Minimum Server Specs:
- **CPU**: 2 cores
- **RAM**: 4 GB
- **Disk**: 50 GB SSD
- **Network**: 100 Mbps

### Recommended Server Specs:
- **CPU**: 4 cores
- **RAM**: 8 GB
- **Disk**: 100 GB SSD
- **Network**: 1 Gbps

### Container Resource Limits:
```yaml
services:
  backend:
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 2G
        reservations:
          cpus: '0.5'
          memory: 512M
  
  postgres:
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 2G
        reservations:
          cpus: '1'
          memory: 1G
```

## Backup Strategy

### Database Backups:
```bash
#!/bin/bash
# /opt/kiosk/scripts/backup-db.sh
docker exec kiosk_postgres pg_dump -U kiosk_user kiosk_db | \
  gzip > /var/backups/kiosk/db-$(date +%Y%m%d-%H%M%S).sql.gz

# Keep last 7 days
find /var/backups/kiosk/ -name "db-*.sql.gz" -mtime +7 -delete
```

### Cron Job:
```cron
# Daily backup at 2 AM
0 2 * * * /opt/kiosk/scripts/backup-db.sh
```

## Monitoring

### Health Checks:
```yaml
services:
  backend:
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
```

### Log Monitoring:
```bash
# View logs
docker-compose logs -f backend

# Log rotation via Docker
services:
  backend:
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
```

## Scaling Considerations

### Single Server Limitations:
- ✅ Good for: 10-50 concurrent kiosks
- ⚠️ Limited by: Single point of failure
- ⚠️ No horizontal scaling
- ⚠️ SSE events limited to single backend instance

### When to Move to Kubernetes:
- Need for high availability (99.9%+ uptime)
- More than 50 concurrent kiosks
- Multiple geographic locations
- Auto-scaling requirements
- Zero-downtime deployments

---

# 🎯 KUBERNETES DEPLOYMENT

## Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│                    Kubernetes Cluster                    │
├─────────────────────────────────────────────────────────┤
│                                                           │
│  ┌──────────────┐      ┌──────────────┐                │
│  │   Ingress    │──────│   Frontend   │                │
│  │  Controller  │      │  (Kiosk UI)  │                │
│  │  + SSL/TLS   │      │  2-5 pods    │                │
│  └──────────────┘      └──────────────┘                │
│         │                                               │
│         │              ┌──────────────┐                │
│         └──────────────│   Backend    │                │
│                        │   (FastAPI)  │                │
│                        │  2-10 pods   │                │
│                        │  + HPA       │                │
│                        └──────────────┘                │
│                               │                         │
│                               │                         │
│                        ┌──────────────┐                │
│                        │  PostgreSQL  │                │
│                        │ StatefulSet  │                │
│                        │   + PVC      │                │
│                        └──────────────┘                │
│                                                          │
│  ┌──────────────┐      ┌──────────────┐               │
│  │ Uploads PVC  │      │  Media PVC   │               │
│  │ (ReadWriteMany)     │ (ReadWriteMany)              │
│  └──────────────┘      └──────────────┘               │
│                                                          │
│  ┌─────────────────────────────────────────────────┐  │
│  │         Monitoring & Logging                     │  │
│  │  Prometheus │ Grafana │ Loki │ Fluentd          │  │
│  └─────────────────────────────────────────────────┘  │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

## Kubernetes Advantages

### High Availability:
- Multiple replicas of each service
- Automatic pod rescheduling on node failure
- Rolling updates with zero downtime
- Health checks and automatic restarts

### Scalability:
- Horizontal Pod Autoscaler (HPA)
- Cluster autoscaling
- Load balancing across pods
- Resource optimization

### Management:
- Declarative configuration
- GitOps workflows
- Automated deployments
- Rollback capabilities

## Kubernetes Components

### 1. **Namespaces**
```yaml
- kiosk-prod
- kiosk-staging
- kiosk-monitoring
```

### 2. **ConfigMaps**
- Application configuration
- Kiosk device configuration
- Nginx configuration

### 3. **Secrets**
- Database credentials
- JWT keys
- API keys
- SSL certificates

### 4. **Deployments**
- Frontend (2-5 replicas)
- Backend (2-10 replicas with HPA)

### 5. **StatefulSets**
- PostgreSQL (1 replica, can add read replicas)

### 6. **Services**
- ClusterIP for internal communication
- LoadBalancer for external access (or use Ingress)

### 7. **Ingress**
- SSL/TLS termination
- Path-based routing
- Host-based routing

### 8. **PersistentVolumeClaims**
- Database storage (ReadWriteOnce)
- Uploads/Media (ReadWriteMany)

## Resource Requirements

### Minimum Cluster:
- **Nodes**: 3 (for HA)
- **CPU per node**: 2 cores
- **RAM per node**: 4 GB
- **Total**: 6 cores, 12 GB RAM

### Recommended Cluster:
- **Nodes**: 5 (3 for app, 2 for monitoring)
- **CPU per node**: 4 cores
- **RAM per node**: 8 GB
- **Total**: 20 cores, 40 GB RAM

## Deployment Strategy

### 1. **Rolling Update**
```yaml
strategy:
  type: RollingUpdate
  rollingUpdate:
    maxSurge: 1
    maxUnavailable: 0
```

### 2. **Health Checks**
```yaml
livenessProbe:
  httpGet:
    path: /health
    port: 8000
  initialDelaySeconds: 30
  periodSeconds: 10

readinessProbe:
  httpGet:
    path: /health
    port: 8000
  initialDelaySeconds: 5
  periodSeconds: 5
```

### 3. **Auto-Scaling**
```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: backend-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: backend
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
```

## Migration Path: Docker → Kubernetes

### Phase 1: Preparation
1. Optimize Docker images for production
2. Externalize configuration
3. Implement health checks
4. Test backup/restore procedures

### Phase 2: Kubernetes Setup
1. Provision Kubernetes cluster
2. Set up kubectl and helm
3. Configure storage classes
4. Set up ingress controller

### Phase 3: Migration
1. Deploy database to Kubernetes
2. Migrate data from Docker
3. Deploy backend services
4. Deploy frontend services
5. Configure ingress and SSL

### Phase 4: Validation
1. Test all functionality
2. Load testing
3. Failover testing
4. Backup/restore testing

### Phase 5: Cutover
1. Update DNS records
2. Monitor closely
3. Keep Docker deployment as fallback
4. Decommission Docker after stability

---

## 🎯 Recommendation

### For Small to Medium Deployments (< 50 kiosks):
**Start with Docker on a dedicated server**
- Simpler to manage
- Lower operational overhead
- Easier to troubleshoot
- Cost-effective
- Can migrate to Kubernetes later

### For Large Deployments (> 50 kiosks) or Enterprise:
**Go directly to Kubernetes**
- Better scalability
- High availability
- Professional operations
- Future-proof architecture

### Hybrid Approach:
**Start with Docker, plan for Kubernetes**
- Build Docker images production-ready
- Use same images for both platforms
- Externalize all configuration
- Implement proper health checks
- This makes migration easier later

---

## 🚀 Next Steps

Would you like me to:

1. **Create production-ready Docker Compose files** for server deployment?
2. **Create Kubernetes manifests** for cluster deployment?
3. **Both** - so you have flexibility to choose?

Please let me know which deployment path you'd like to pursue, and I'll create the detailed implementation plan and configuration files.
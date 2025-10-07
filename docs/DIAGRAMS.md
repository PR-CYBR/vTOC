# vTOC Architecture Diagram

```
                                    ╔═══════════════════════════════════════╗
                                    ║         External Users / Clients       ║
                                    ╚═══════════════════════════════════════╝
                                                     │
                                                     ▼
                                    ┌─────────────────────────────────────┐
                                    │    Traefik Reverse Proxy            │
                                    │    - Load Balancer                  │
                                    │    - SSL/TLS Termination            │
                                    │    - Service Discovery              │
                                    │    Port: 80, 443, 8080 (dashboard)  │
                                    └─────────────────────────────────────┘
                                         │              │              │
                    ┌────────────────────┴──────┬───────┴─────────────┘
                    │                           │
                    ▼                           ▼
        ┌──────────────────────┐   ┌──────────────────────────────┐
        │   Frontend (React)   │   │   Backend API (FastAPI)       │
        │   - SPA UI           │   │   - REST API                  │
        │   - 6 Pages          │   │   - 5 Routers                 │
        │   - Responsive       │   │   - Business Logic            │
        │   Port: 80 (internal)│   │   Port: 8000 (internal)       │
        └──────────────────────┘   └──────────────────────────────┘
                                                   │
                                                   │ Database Queries
                                                   ▼
                                    ┌──────────────────────────────┐
                                    │   PostgreSQL Database        │
                                    │   - 5 Tables                 │
                                    │   - Data Persistence         │
                                    │   - ACID Transactions        │
                                    │   Port: 5432 (internal)      │
                                    └──────────────────────────────┘
                                                   │
        ┌──────────────────────────────────────────┼───────────────────────────────┐
        │                                          │                               │
        ▼                                          ▼                               ▼
┌────────────────────┐              ┌────────────────────────┐    ┌─────────────────────┐
│ Automation Agents  │              │  n8n Workflows         │    │  Wazuh Security     │
│ - Monitor Agent    │              │  - Operations Monitor  │    │  - Intrusion Detect │
│ - Analyzer Agent   │              │  - Security Handler    │    │  - Log Analysis     │
│ - Executor Agent   │              │  - Event Processing    │    │  - File Integrity   │
│ Port: N/A (cron)   │              │  Port: 5678 (internal) │    │  Port: 1514, 1515   │
└────────────────────┘              └────────────────────────┘    └─────────────────────┘

═════════════════════════════════════════════════════════════════════════════════════════
                                  Docker Network (vtoc-network)
═════════════════════════════════════════════════════════════════════════════════════════

┌─────────────────────────────────────────────────────────────────────────────────────┐
│                              Docker Volumes (Persistent Storage)                     │
│                                                                                       │
│   postgres_data        n8n_data           wazuh_logs        wazuh_etc               │
│   (Database)           (Workflows)        (Security Logs)   (Config)                │
└─────────────────────────────────────────────────────────────────────────────────────┘

═════════════════════════════════════════════════════════════════════════════════════════
                            Infrastructure Management Layer
═════════════════════════════════════════════════════════════════════════════════════════

┌──────────────────────┐    ┌──────────────────────┐    ┌─────────────────────────┐
│   Terraform          │    │   Ansible            │    │   GitHub Actions        │
│   - Infrastructure   │    │   - Configuration    │    │   - CI/CD Pipeline      │
│   - Provisioning     │    │   - Deployment       │    │   - Testing             │
│   - Resource Mgmt    │    │   - Orchestration    │    │   - Security Scanning   │
└──────────────────────┘    └──────────────────────┘    └─────────────────────────┘
```

## Data Flow Diagrams

### User Request Flow

```
User → Frontend → Traefik → Backend API → Database
                                ↓
                            Response
                                ↓
User ← Frontend ← Traefik ← Backend API
```

### Agent Automation Flow

```
Scheduler → Agent Service → Backend API → Database
               ↓
          Log/Action
               ↓
         n8n Workflow (optional)
               ↓
         Backend API (update)
```

### Security Alert Flow

```
Wazuh → Alert Generated → n8n Webhook → Backend API → Database
                                             ↓
                                     Intelligence Report Created
                                             ↓
                                      Frontend (display)
```

## Service Communication Matrix

```
┌──────────┬─────────┬──────────┬──────────┬─────┬────────┬────────┐
│ Service  │ Traefik │ Backend  │ Database │ n8n │ Agents │ Wazuh  │
├──────────┼─────────┼──────────┼──────────┼─────┼────────┼────────┤
│ Frontend │    ✓    │          │          │     │        │        │
│ Backend  │    ✓    │    ✓     │    ✓     │  ✓  │   ✓    │   ✓    │
│ Database │         │    ✓     │    ✓     │     │   ✓    │        │
│ n8n      │    ✓    │    ✓     │          │  ✓  │        │        │
│ Agents   │         │    ✓     │          │     │   ✓    │        │
│ Wazuh    │         │    ✓     │          │  ✓  │        │   ✓    │
└──────────┴─────────┴──────────┴──────────┴─────┴────────┴────────┘
```

## Port Mapping

```
External Port → Internal Port → Service
─────────────────────────────────────────
80            → 80             → Traefik (HTTP)
443           → 443            → Traefik (HTTPS)
8080          → 8080           → Traefik (Dashboard)
              → 8000           → Backend API
              → 80             → Frontend (Nginx)
              → 5432           → PostgreSQL
              → 5678           → n8n
              → 1514           → Wazuh (Syslog)
              → 1515           → Wazuh (API)
```

## Technology Stack Layers

```
┌──────────────────────────────────────────────────────────┐
│                    Presentation Layer                     │
│                                                           │
│  React 18 │ React Router │ Axios │ Custom CSS            │
└──────────────────────────────────────────────────────────┘
                            │
┌──────────────────────────────────────────────────────────┐
│                    Application Layer                      │
│                                                           │
│  FastAPI │ Pydantic │ Python 3.11 │ Uvicorn              │
└──────────────────────────────────────────────────────────┘
                            │
┌──────────────────────────────────────────────────────────┐
│                    Data Access Layer                      │
│                                                           │
│  SQLAlchemy │ psycopg2 │ Alembic Migrations              │
└──────────────────────────────────────────────────────────┘
                            │
┌──────────────────────────────────────────────────────────┐
│                      Data Layer                           │
│                                                           │
│  PostgreSQL 15 │ JSON │ Indexes │ Constraints            │
└──────────────────────────────────────────────────────────┘
```

## Deployment Architecture

```
┌─────────────────────────────────────────────────────────┐
│                   Development                            │
│                                                          │
│  Local Machine → docker-compose up -d                   │
└─────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────┐
│                    CI/CD Pipeline                        │
│                                                          │
│  GitHub → Actions → Test → Build → Security Scan        │
└─────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────┐
│                   Production                             │
│                                                          │
│  Terraform → Ansible → Docker Swarm/K8s (optional)      │
└─────────────────────────────────────────────────────────┘
```

## Security Layers

```
┌──────────────────────────────────────────────────────────┐
│ Layer 1: Network Security                                │
│ - Docker Network Isolation                               │
│ - Traefik as Single Entry Point                          │
│ - Internal Service Communication Only                    │
└──────────────────────────────────────────────────────────┘
                            │
┌──────────────────────────────────────────────────────────┐
│ Layer 2: Application Security                            │
│ - Environment Variables                                   │
│ - CORS Configuration                                      │
│ - Input Validation (Pydantic)                            │
│ - SQL Injection Prevention (SQLAlchemy)                  │
└──────────────────────────────────────────────────────────┘
                            │
┌──────────────────────────────────────────────────────────┐
│ Layer 3: Runtime Security                                │
│ - Wazuh Monitoring                                       │
│ - Log Analysis                                           │
│ - Intrusion Detection                                    │
│ - File Integrity Monitoring                              │
└──────────────────────────────────────────────────────────┘
                            │
┌──────────────────────────────────────────────────────────┐
│ Layer 4: Supply Chain Security                           │
│ - Snyk Vulnerability Scanning                            │
│ - Dependency Checking                                    │
│ - Container Image Scanning                               │
│ - Automated Updates                                      │
└──────────────────────────────────────────────────────────┘
```

## Scalability Architecture

```
                  ┌─────────────────┐
                  │  Load Balancer  │
                  │    (Traefik)    │
                  └────────┬────────┘
                           │
        ┌──────────────────┼──────────────────┐
        │                  │                  │
        ▼                  ▼                  ▼
  ┌──────────┐      ┌──────────┐      ┌──────────┐
  │ Backend  │      │ Backend  │      │ Backend  │
  │ Instance │      │ Instance │      │ Instance │
  │    #1    │      │    #2    │      │    #3    │
  └─────┬────┘      └─────┬────┘      └─────┬────┘
        │                  │                  │
        └──────────────────┼──────────────────┘
                           │
                    ┌──────▼──────┐
                    │  PostgreSQL │
                    │   Primary   │
                    └──────┬──────┘
                           │
                    ┌──────▼──────┐
                    │  PostgreSQL │
                    │   Replica   │
                    │  (Optional) │
                    └─────────────┘
```

---

**Legend:**
- `│` `─` `┌` `└` `┐` `┘` : Box drawing
- `→` : Data/Request flow
- `▼` : Downward flow
- `✓` : Communication enabled

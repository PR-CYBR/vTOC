# vTOC Architecture Overview

## System Architecture

vTOC follows a microservice architecture pattern with the following components:

```
┌─────────────────────────────────────────────────────────────┐
│                        Traefik Proxy                         │
│                   (Reverse Proxy / Load Balancer)           │
└────────┬─────────────────────────────────────────┬──────────┘
         │                                         │
         │                                         │
    ┌────▼─────┐                            ┌─────▼──────┐
    │ Frontend │                            │  Backend   │
    │  React   │◄───────────────────────────┤   FastAPI  │
    │   SPA    │      API Calls             │    API     │
    └──────────┘                            └─────┬──────┘
                                                  │
                                                  │
                                            ┌─────▼──────┐
                                            │ PostgreSQL │
                                            │  Database  │
                                            └─────┬──────┘
                                                  │
    ┌─────────────────────────────────────────────┤
    │                                             │
┌───▼────────┐  ┌──────────────┐  ┌─────────────▼─┐
│   n8n      │  │    Wazuh     │  │     Agents    │
│ Workflows  │  │   Security   │  │   Automation  │
└────────────┘  └──────────────┘  └───────────────┘
```

## Component Details

### 1. Frontend (React)

**Technology Stack:**
- React 18.x
- React Router for navigation
- Axios for API communication
- Custom CSS for styling

**Key Features:**
- Single Page Application (SPA)
- Responsive design
- Real-time data updates
- Intuitive dashboard

**Pages:**
- Dashboard: Overview and statistics
- Operations: Manage tactical operations
- Missions: Track mission objectives
- Assets: Resource management
- Intelligence: Reports and analysis
- Agents: Automation control

### 2. Backend (FastAPI)

**Technology Stack:**
- Python 3.11
- FastAPI framework
- SQLAlchemy ORM
- Pydantic for data validation
- Uvicorn ASGI server

**Database Models:**
- Operations
- Missions
- Assets
- Intelligence Reports
- Agents

**API Features:**
- RESTful endpoints
- Automatic OpenAPI documentation
- Data validation
- Database transactions
- Error handling

### 3. Database (PostgreSQL)

**Features:**
- Relational data storage
- ACID compliance
- Connection pooling
- Automatic backups via volumes

**Tables:**
- operations
- missions
- assets
- intel_reports
- agents

### 4. Reverse Proxy (Traefik)

**Features:**
- Automatic service discovery
- Load balancing
- SSL/TLS termination
- Dashboard monitoring
- Middleware support

**Routing:**
- `/` → Frontend
- `/api/*` → Backend API
- `/n8n/*` → n8n workflows
- `:8080` → Traefik dashboard

### 5. Workflow Automation (n8n)

**Purpose:**
- Automate repetitive tasks
- Integrate external services
- Schedule operations
- Process webhooks

**Pre-configured Workflows:**
- Operations monitoring
- Security alert handling
- Data synchronization

### 6. Security (Wazuh)

**Features:**
- Intrusion detection
- Log analysis
- File integrity monitoring
- Vulnerability detection
- Security compliance

### 7. Automation Agents

**Agent Types:**

1. **Monitor Agent**
   - System health checks
   - Metrics collection
   - Status monitoring
   - Runs every 5 minutes

2. **Analyzer Agent**
   - Data analysis
   - Pattern recognition
   - Intelligence correlation
   - Runs every 10 minutes

3. **Executor Agent**
   - Task execution
   - Workflow automation
   - Resource allocation
   - Runs every 15 minutes

## Data Flow

### 1. User Request Flow

```
User → Frontend → Traefik → Backend API → Database
                                ↓
                            Response
                                ↓
User ← Frontend ← Traefik ← Backend API
```

### 2. Agent Automation Flow

```
Schedule → Agent Service → Backend API → Database
              ↓
         Log/Action
              ↓
          n8n Workflow (optional)
```

### 3. Security Alert Flow

```
Wazuh → Security Alert → n8n Webhook → Backend API → Database
                                            ↓
                                    Intelligence Report
```

## Deployment Architecture

### Docker Compose Stack

All services run as Docker containers orchestrated by Docker Compose:

1. **Networks**: Single bridge network for inter-service communication
2. **Volumes**: Persistent storage for database and n8n data
3. **Health Checks**: Automatic service health monitoring
4. **Dependencies**: Proper startup order with depends_on

### Infrastructure as Code

**Terraform:**
- Docker network provisioning
- Volume management
- Resource configuration

**Ansible:**
- System package installation
- Docker deployment
- Configuration management
- Service orchestration

## Security Architecture

### Network Security

- All services on isolated Docker network
- Traefik as single entry point
- Internal service communication only

### Application Security

- Environment variable management
- API authentication (ready for implementation)
- CORS configuration
- Input validation

### Monitoring & Alerting

- Wazuh for runtime security
- Snyk for dependency scanning
- Traefik for access logs
- n8n for alert automation

## Scalability Considerations

### Horizontal Scaling

- Stateless backend services
- Load balancing via Traefik
- Database connection pooling
- Shared session storage (Redis ready)

### Vertical Scaling

- Resource limits in Docker Compose
- Database tuning
- Connection pool sizing
- Cache implementation

## High Availability

### Data Persistence

- PostgreSQL volume backups
- n8n workflow exports
- Configuration as code

### Service Recovery

- Docker restart policies
- Health check monitoring
- Automatic failover (Traefik)

## Performance Optimization

### Backend

- Async/await patterns
- Database query optimization
- Connection pooling
- Caching strategy (ready)

### Frontend

- Code splitting
- Lazy loading
- Asset optimization
- CDN ready

### Database

- Indexed columns
- Query optimization
- Connection pooling
- Read replicas (future)

## Monitoring & Observability

### Logs

- Centralized logging
- Structured log format
- Log aggregation ready
- Real-time log streaming

### Metrics

- API endpoint metrics
- Service health metrics
- Agent execution metrics
- Database performance

### Tracing

- Request tracing ready
- Performance profiling
- Error tracking
- User analytics ready

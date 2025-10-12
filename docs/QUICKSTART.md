# Quick Start Guide

## Overview

This guide will help you get vTOC up and running in 5 minutes.

## Prerequisites

Ensure you have:
- Docker (version 20.10+)
- Docker Compose (version 2.0+)
- Git

## Installation Steps

### 1. Clone Repository

```bash
git clone https://github.com/PR-CYBR/vTOC.git
cd vTOC
```

### 2. Configure Environment

```bash
# Copy example environment file
cp .env.example .env

# Edit .env and change default passwords
nano .env  # or use your preferred editor
```

**Important:** Change these values in `.env`:
- `POSTGRES_PASSWORD`
- `API_SECRET_KEY`
- `TRAEFIK_DASHBOARD_PASSWORD`
- `N8N_BASIC_AUTH_PASSWORD`
- `WAZUH_API_PASSWORD`

### 3. Start Services

```bash
# Using Docker Compose
docker-compose up -d

# Or using Makefile
make up
```

### 4. Verify Installation

Wait 30 seconds for services to start, then check:

```bash
# Check service status
docker-compose ps

# Check API health
curl http://localhost/api/health
```

### 5. Access Applications

Open your browser and visit:

- **Frontend**: http://localhost
- **API Docs**: http://localhost/api/docs
- **Traefik Dashboard**: http://localhost:8080
- **n8n Workflows**: http://localhost/n8n

## First Steps

### Create Your First Operation

1. Go to http://localhost/operations
2. Click "New Operation"
3. Fill in the details:
   - Name: "Operation Alpha"
   - Code Name: "ALPHA-001"
   - Priority: "High"
4. Click "Create"

### Add Assets

1. Go to http://localhost/assets
2. Click "New Asset"
3. Register equipment or personnel

### Create Missions

1. Go to http://localhost/missions
2. Click "New Mission"
3. Link to an operation
4. Assign team members

### Monitor Agents

1. Go to http://localhost/agents
2. View automation agents
3. Start/stop agents as needed

## Common Commands

### Using Makefile

```bash
# View all available commands
make help

# View logs
make logs

# Restart services
make restart

# Backup database
make backup-db

# Check health
make health
```

### Using Docker Compose

```bash
# View logs
docker-compose logs -f

# Stop services
docker-compose down

# Restart a specific service
docker-compose restart backend

# Scale backend
docker-compose up -d --scale backend=3
```

## Troubleshooting

### Services Won't Start

```bash
# Check logs
docker-compose logs

# Restart services
docker-compose down
docker-compose up -d
```

### Port Already in Use

Edit `docker-compose.yml` and change the port mappings:

```yaml
ports:
  - "8080:80"  # Change 80 to 8080 if port 80 is in use
```

### Database Connection Error

```bash
# Check database is running
docker-compose ps postgres

# Check database logs
docker-compose logs postgres

# Restart database
docker-compose restart postgres
```

### Cannot Access Frontend

```bash
# Check frontend logs
docker-compose logs frontend

# Check Traefik routing
docker-compose logs traefik

# Verify containers are running
docker-compose ps
```

## Next Steps

After installation:

1. **Configure Security**
   - Change all default passwords
   - Review security settings
   - Configure SSL/TLS for production

2. **Explore Features**
   - Create operations and missions
   - Register assets
   - Generate intelligence reports
   - Configure automation agents

3. **Set Up Workflows**
   - Access n8n at http://localhost/n8n
   - Import workflow templates
   - Create custom workflows

4. **Monitor Security**
   - Check Wazuh dashboard
   - Review security alerts
   - Configure alert notifications

5. **Customize**
   - Modify agent configurations
   - Add custom automation
   - Integrate external systems

## Additional Resources

- [Full Documentation](README.md)
- [Architecture Guide](docs/ARCHITECTURE.md)
- [API Documentation](docs/API.md)
- [Deployment Guide](docs/DEPLOYMENT.md)

## Getting Help

If you encounter issues:

1. Check the logs: `docker-compose logs`
2. Review documentation in `/docs`
3. Search GitHub issues
4. Create a new issue with details

## Production Deployment

For production deployment, see the [Deployment Guide](docs/DEPLOYMENT.md).

Key considerations:
- Enable SSL/TLS
- Configure firewall
- Set up backups
- Implement monitoring
- Use strong passwords
- Configure authentication

## Updating

To update to the latest version:

```bash
# Pull latest changes
git pull

# Update and restart
docker-compose pull
docker-compose up -d --build
```

## Uninstalling

To completely remove vTOC:

```bash
# Stop and remove all containers, networks, and volumes
docker-compose down -v

# Remove images
docker rmi $(docker images -q 'vtoc*')

# Remove project directory
cd ..
rm -rf vTOC
```

**Warning:** This will delete all data!

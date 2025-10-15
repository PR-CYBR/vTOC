# vTOC - Virtual Tactical Operations Center

A modular, cloud-native tactical operations management platform built with microservice architecture.

## 🏗️ Architecture

vTOC is built using a modern microservice architecture with the following components:

- **Backend API**: Python/FastAPI microservices for business logic
- **Frontend**: React single-page application
- **Database**: PostgreSQL for persistent data storage
- **Reverse Proxy**: Traefik for routing and load balancing
- **Workflow Automation**: n8n for automated workflows
- **Security Monitoring**: Wazuh for runtime security
- **Agent System**: Python-based automation agents
- **Infrastructure as Code**: Terraform for provisioning
- **Configuration Management**: Ansible for deployment automation

## 🚀 Quick Start

### Prerequisites

- Docker and Docker Compose
- Git
- (Optional) Terraform and Ansible for infrastructure management

### Installation

1. Clone the repository:
```bash
git clone https://github.com/PR-CYBR/vTOC.git
cd vTOC
```

2. Copy the environment variables:
```bash
cp .env.example .env
```

3. Edit `.env` and configure your environment variables (especially change default passwords)

4. Start the services:
```bash
docker-compose up -d
```

5. Access the application:
   - **Frontend**: http://localhost
   - **API Documentation**: http://localhost/api/docs
   - **Traefik Dashboard**: http://localhost:8080
   - **n8n Workflows**: http://localhost/n8n

## 📦 Services

### Backend API

The backend is built with FastAPI and provides RESTful APIs for:

- **Operations**: Manage tactical operations
- **Missions**: Track mission objectives
- **Assets**: Manage resources and equipment
- **Intelligence**: Store and analyze intelligence reports
- **Agents**: Control automation agents

API Documentation is available at `/api/docs` (Swagger UI) and `/api/redoc` (ReDoc).

### Frontend

React-based single-page application with:

- Dashboard with real-time statistics
- Operations management
- Mission tracking
- Asset inventory
- Intelligence reports
- Agent monitoring and control

### Database

PostgreSQL database with:

- Automated initialization scripts
- Data persistence via Docker volumes
- Connection pooling
- Database migrations support

### Traefik Reverse Proxy

- Automatic service discovery
- Load balancing
- SSL/TLS termination support
- Dashboard for monitoring routes

### n8n Workflow Automation

Pre-configured workflows:

- **Operations Monitor**: Scheduled monitoring of active operations
- **Security Alert Handler**: Automated security alert processing

### Automation Agents

Three types of agents:

1. **Monitor Agent**: System health and metrics monitoring
2. **Analyzer Agent**: Intelligence and mission data analysis
3. **Executor Agent**: Automated task execution

## 🛠️ Development

### Backend Development

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### Frontend Development

```bash
cd frontend
npm install
npm start
```

#### Mock data mode

The frontend can operate without the backend by enabling the built-in mock API provider. This is useful for offline demos or showcasing the UI without provisioning the complete stack.

```bash
cd frontend
npm install
npm run start:mock
```

The `start:mock` script sets `REACT_APP_USE_MOCKS=true`, which activates an in-memory data service backed by `localStorage`. Any create or update actions performed in the UI are persisted locally so that state survives page reloads during the session. To reset the mock data, clear the browser's local storage for the application domain.

> **Windows tip:** If you prefer running the command manually, use `set REACT_APP_USE_MOCKS=true && npm start` in `cmd.exe` or `$Env:REACT_APP_USE_MOCKS="true"; npm start` in PowerShell.

### Running Tests

Backend:
```bash
cd backend
pytest
```

Frontend:
```bash
cd frontend
npm test
```

## 🏗️ Infrastructure as Code

### Terraform

Deploy infrastructure:

```bash
cd infrastructure/terraform
terraform init
terraform plan
terraform apply
```

### Ansible

Deploy using Ansible:

```bash
cd infrastructure/ansible
ansible-playbook -i inventory.ini playbooks/deploy.yml
```

## 🔒 Security

### Built-in Security Features

- **Wazuh**: Runtime security monitoring and intrusion detection
- **Snyk**: Vulnerability scanning in CI/CD pipeline
- **Traefik**: Secure routing with middleware support
- **Environment Variables**: Sensitive data management
- **CORS Configuration**: Controlled cross-origin access

### Security Best Practices

1. Change all default passwords in `.env`
2. Use strong API secret keys
3. Enable SSL/TLS in production
4. Regularly update dependencies
5. Review security alerts from Wazuh and Snyk

## 🔄 CI/CD

GitHub Actions workflows:

- **CI/CD Pipeline**: Automated testing and deployment
- **Security Scan**: Daily security vulnerability scanning
- **Dependency Review**: Automated dependency updates

## 📊 Monitoring

- **Traefik Dashboard**: Service health and routing
- **n8n Dashboard**: Workflow execution status
- **Wazuh Manager**: Security events and alerts
- **Agent Logs**: Automation agent activities

## 📚 API Endpoints

### Operations
- `GET /api/operations/` - List all operations
- `POST /api/operations/` - Create new operation
- `GET /api/operations/{id}` - Get operation details
- `PUT /api/operations/{id}` - Update operation
- `DELETE /api/operations/{id}` - Delete operation

### Missions
- `GET /api/missions/` - List all missions
- `POST /api/missions/` - Create new mission
- `GET /api/missions/{id}` - Get mission details
- `PUT /api/missions/{id}` - Update mission
- `DELETE /api/missions/{id}` - Delete mission

### Assets
- `GET /api/assets/` - List all assets
- `POST /api/assets/` - Register new asset
- `GET /api/assets/{id}` - Get asset details
- `PUT /api/assets/{id}` - Update asset
- `DELETE /api/assets/{id}` - Delete asset

### Intelligence
- `GET /api/intel/` - List intelligence reports
- `POST /api/intel/` - Create intelligence report
- `GET /api/intel/{id}` - Get report details
- `DELETE /api/intel/{id}` - Delete report

### Agents
- `GET /api/agents/` - List all agents
- `POST /api/agents/` - Register new agent
- `GET /api/agents/{id}` - Get agent details
- `POST /api/agents/{id}/start` - Start agent
- `POST /api/agents/{id}/stop` - Stop agent
- `DELETE /api/agents/{id}` - Delete agent

## 🤝 Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

For issues and questions:
- Open an issue on GitHub
- Check the documentation in `/docs`
- Review API documentation at `/api/docs`

## 🗺️ Roadmap

- [ ] Advanced analytics dashboard
- [ ] Real-time WebSocket updates
- [ ] Mobile application
- [ ] Multi-tenancy support
- [ ] Advanced reporting features
- [ ] Integration with external systems
- [ ] Machine learning-based threat detection
- [ ] Geographic information system (GIS) integration

## 📝 Notes

- This is a development setup. For production deployment, ensure proper security configurations.
- Update all default passwords and secrets before deploying to production.
- Configure SSL/TLS certificates for secure communication.
- Set up proper backup and disaster recovery procedures.
- Implement proper access control and authentication mechanisms.

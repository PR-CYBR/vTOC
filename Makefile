# Makefile for vTOC

.PHONY: help build up down restart logs ps clean test

help: ## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Available targets:'
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  %-15s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

build: ## Build all Docker images
	docker-compose build

up: ## Start all services
	docker-compose up -d

down: ## Stop all services
	docker-compose down

restart: ## Restart all services
	docker-compose restart

logs: ## View logs from all services
	docker-compose logs -f

ps: ## Show status of all services
	docker-compose ps

clean: ## Stop and remove all containers, volumes, and images
	docker-compose down -v
	docker system prune -f

test-backend: ## Run backend tests
	docker-compose exec backend pytest

test-frontend: ## Run frontend tests
	docker-compose exec frontend npm test

install: ## Install dependencies and start services
	@echo "Installing vTOC..."
	@cp .env.example .env
	@echo "Please edit .env file with your configuration"
	@echo "Then run: make up"

backup-db: ## Backup PostgreSQL database
	@mkdir -p backups
	docker exec vtoc-postgres pg_dump -U vtoc_user vtoc_db > backups/backup-$$(date +%Y%m%d-%H%M%S).sql
	@echo "Database backed up to backups/"

restore-db: ## Restore PostgreSQL database (usage: make restore-db FILE=backup.sql)
	@if [ -z "$(FILE)" ]; then echo "Usage: make restore-db FILE=backup.sql"; exit 1; fi
	docker exec -i vtoc-postgres psql -U vtoc_user vtoc_db < $(FILE)
	@echo "Database restored from $(FILE)"

scale-backend: ## Scale backend service (usage: make scale-backend N=3)
	@if [ -z "$(N)" ]; then echo "Usage: make scale-backend N=3"; exit 1; fi
	docker-compose up -d --scale backend=$(N)

health: ## Check health of all services
	@echo "Checking service health..."
	@curl -s http://localhost/api/health | jq . || echo "Backend: Not responding"
	@curl -s -I http://localhost | grep "200 OK" && echo "Frontend: OK" || echo "Frontend: Not responding"

dev-backend: ## Run backend in development mode
	cd backend && uvicorn app.main:app --reload --host 0.0.0.0

dev-frontend: ## Run frontend in development mode
	cd frontend && npm install && npm start

init-terraform: ## Initialize Terraform
	cd infrastructure/terraform && terraform init

apply-terraform: ## Apply Terraform configuration
	cd infrastructure/terraform && terraform apply

deploy-ansible: ## Deploy using Ansible
	cd infrastructure/ansible && ansible-playbook -i inventory.ini playbooks/deploy.yml

security-scan: ## Run security scan
	docker run --rm -v $(PWD):/project aquasec/trivy fs --security-checks vuln /project

update: ## Update all services
	git pull
	docker-compose pull
	docker-compose up -d --build

shell-backend: ## Open shell in backend container
	docker-compose exec backend /bin/bash

shell-frontend: ## Open shell in frontend container
	docker-compose exec frontend /bin/sh

shell-db: ## Open PostgreSQL shell
	docker-compose exec postgres psql -U vtoc_user vtoc_db

prune: ## Remove unused Docker resources
	docker system prune -a --volumes

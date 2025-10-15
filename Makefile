.PHONY: help setup-local setup-container setup-cloud compose-up compose-down \
    backend-test frontend-test scraper-run backend-lint station-migrate station-seed

help: ## Show help
	@echo 'Usage: make <target>'
	@echo ''
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  %-20s %s\\n", $$1, $$2}' $(MAKEFILE_LIST)

setup-local: ## Run setup script in local mode
	./scripts/setup.sh --mode local

setup-container: ## Run setup script in container mode
	./scripts/setup.sh --mode container --apply

setup-cloud: ## Generate Terraform/Ansible scaffolding
	./scripts/setup.sh --mode cloud

compose-up: ## Start dev stack using generated compose file
	docker compose -f docker-compose.generated.yml up -d

compose-down: ## Stop dev stack started from generated compose file
	docker compose -f docker-compose.generated.yml down

backend-test: ## Run backend pytest suite
	cd backend && pytest -q

frontend-test: ## Run frontend tests
	cd frontend && pnpm test -- --watch=false --passWithNoTests

scraper-run: ## Run scraper locally
	cd agents/scraper && python main.py

backend-lint: ## Lint backend application with ruff
	cd backend && ruff check app

station-migrate: ## Run Alembic migrations for all station schemas
	./stations/TOC-S1/onboard.sh
	./stations/TOC-S2/onboard.sh
	./stations/TOC-S3/onboard.sh
	./stations/TOC-S4/onboard.sh

station-seed: ## Seed baseline telemetry for each station
	python stations/TOC-S1/seed.py
	python stations/TOC-S2/seed.py
	python stations/TOC-S3/seed.py
	python stations/TOC-S4/seed.py

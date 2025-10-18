.PHONY: help setup-local setup-container setup-cloud compose-up compose-down \
    backend-test frontend-test scraper-run backend-lint station-migrate station-seed \
    dev-shell

help: ## Show help
	@echo 'Usage: make <target>'
	@echo ''
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  %-20s %s\\n", $$1, $$2}' $(MAKEFILE_LIST)

setup-local: ## Run setup script in local mode
	python -m scripts.bootstrap_cli setup local

setup-container: ## Run setup script in container mode
	python -m scripts.bootstrap_cli setup container --apply

setup-cloud: ## Generate Terraform/Ansible scaffolding
	python -m scripts.bootstrap_cli setup cloud

compose-up: ## Start dev stack using generated compose file
	python -m scripts.bootstrap_cli compose up

compose-down: ## Stop dev stack started from generated compose file
	python -m scripts.bootstrap_cli compose down

backend-test: ## Run backend pytest suite
	python -m scripts.bootstrap_cli backend test

frontend-test: ## Run frontend tests
	python -m scripts.bootstrap_cli frontend test

scraper-run: ## Run scraper locally
	python -m scripts.bootstrap_cli scraper run

backend-lint: ## Lint backend application with ruff
	python -m scripts.bootstrap_cli backend lint

station-migrate: ## Run Alembic migrations for all station schemas
	python -m scripts.bootstrap_cli station migrate

station-seed: ## Seed baseline telemetry for each station
        python -m scripts.bootstrap_cli station seed

dev-shell: ## Launch the Docker-based developer shell (pass ARGS="--setup" to bootstrap)
	./scripts/dev_shell.sh $(ARGS)

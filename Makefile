.PHONY: help setup-local setup-container setup-cloud compose-up compose-down \
    backend-test frontend-test scraper-run backend-lint station-migrate station-seed \
    dev-shell
.PHONY: help setup-local setup-container setup-cloud setup-pi compose-up compose-down \
    backend-test frontend-test scraper-run backend-lint station-migrate station-seed \
    spec-constitution spec-plan spec-tasks spec-implement spec-specify

help: ## Show help
	@echo 'Usage: make <target>'
	@echo ''
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  %-20s %s\\n", $$1, $$2}' $(MAKEFILE_LIST)

setup-local: ## Run setup script in local mode
	python -m scripts.bootstrap_cli setup local

setup-container: ## Run setup script in container mode
        python -m scripts.bootstrap_cli setup container --apply

setup-pi: ## Run setup script in Raspberry Pi mode
        python -m scripts.bootstrap_cli setup pi

setup-cloud: ## Generate Terraform/Ansible scaffolding
        python -m scripts.bootstrap_cli setup cloud

compose-up: ## Start dev stack using generated compose file
	python -m scripts.bootstrap_cli compose up

compose-down: ## Stop dev stack started from generated compose file
	python -m scripts.bootstrap_cli compose down

backend-test: ## Run backend pytest suite
        python -m scripts.bootstrap_cli backend test

backend-install: ## Install backend runtime and dev dependencies
	python -m pip install -r backend/requirements.runtime.txt -r backend/requirements.dev.txt

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
spec-constitution: ## Run Spec Kit constitution workflow
        python -m scripts.bootstrap_cli spec constitution

spec-plan: ## Generate a Spec Kit implementation plan
        python -m scripts.bootstrap_cli spec plan

spec-tasks: ## Expand tasks using Spec Kit
        python -m scripts.bootstrap_cli spec tasks

spec-implement: ## Follow Spec Kit implementation guidance
        python -m scripts.bootstrap_cli spec implement

spec-specify: ## Run arbitrary Spec Kit commands via specify
        python -m scripts.bootstrap_cli spec specify

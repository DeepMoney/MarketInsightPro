.PHONY: help install test coverage lint format clean run docker-build docker-up docker-down docker-logs

# Default target
.DEFAULT_GOAL := help

# Variables
PYTHON := python3
PIP := pip
STREAMLIT := streamlit
DOCKER_COMPOSE := docker-compose
APP_FILE := app.py

help: ## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Available targets:'
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  %-20s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

install: ## Install Python dependencies
	$(PIP) install --upgrade pip
	$(PIP) install -r requirements.txt

install-dev: ## Install development dependencies
	$(PIP) install --upgrade pip
	$(PIP) install -r requirements.txt
	$(PIP) install pytest pytest-cov pytest-mock flake8 black isort

test: ## Run tests
	pytest

test-verbose: ## Run tests with verbose output
	pytest -v

coverage: ## Run tests with coverage report
	pytest --cov --cov-report=term-missing --cov-report=html
	@echo "Coverage report generated in htmlcov/index.html"

coverage-xml: ## Generate XML coverage report (for CI)
	pytest --cov --cov-report=xml

lint: ## Run linters (flake8)
	flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics
	flake8 . --count --exit-zero --max-complexity=10 --max-line-length=127 --statistics

format: ## Format code with black and isort
	black .
	isort .

format-check: ## Check code formatting without modifying files
	black --check --diff .
	isort --check-only --diff .

clean: ## Remove Python cache files and test artifacts
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.coverage" -delete
	rm -rf .pytest_cache
	rm -rf htmlcov
	rm -rf .coverage
	rm -rf coverage.xml
	rm -rf *.egg-info
	rm -rf build
	rm -rf dist

run: ## Run the Streamlit application locally
	$(STREAMLIT) run $(APP_FILE) --server.port=5000

run-debug: ## Run with debug logging
	$(STREAMLIT) run $(APP_FILE) --server.port=5000 --logger.level=debug

docker-build: ## Build Docker image
	docker build -t market-insight-pro:latest .

docker-up: ## Start Docker containers
	$(DOCKER_COMPOSE) up -d

docker-up-build: ## Build and start Docker containers
	$(DOCKER_COMPOSE) up -d --build

docker-down: ## Stop Docker containers
	$(DOCKER_COMPOSE) down

docker-down-volumes: ## Stop Docker containers and remove volumes
	$(DOCKER_COMPOSE) down -v

docker-logs: ## View Docker container logs
	$(DOCKER_COMPOSE) logs -f

docker-logs-app: ## View app container logs
	$(DOCKER_COMPOSE) logs -f app

docker-logs-db: ## View database container logs
	$(DOCKER_COMPOSE) logs -f db

docker-shell-app: ## Open shell in app container
	$(DOCKER_COMPOSE) exec app /bin/bash

docker-shell-db: ## Open PostgreSQL shell
	$(DOCKER_COMPOSE) exec db psql -U postgres -d trading_analytics

docker-test: ## Run tests in Docker container
	$(DOCKER_COMPOSE) run --rm app pytest

docker-restart: ## Restart Docker containers
	$(DOCKER_COMPOSE) restart

docker-ps: ## Show running Docker containers
	$(DOCKER_COMPOSE) ps

docker-with-pgadmin: ## Start containers including pgAdmin
	$(DOCKER_COMPOSE) --profile tools up -d

verify: format-check lint test ## Run all verification steps (format, lint, test)

ci: clean install-dev verify ## Run complete CI pipeline locally

init-db: ## Initialize database (run app once to trigger init)
	@echo "Database initialization happens automatically on first app run"
	@echo "Run 'make run' or 'make docker-up' to initialize"

backup-db: ## Backup database (Docker)
	@echo "Creating database backup..."
	$(DOCKER_COMPOSE) exec -T db pg_dump -U postgres trading_analytics > backup_$$(date +%Y%m%d_%H%M%S).sql
	@echo "Backup created"

restore-db: ## Restore database from backup (usage: make restore-db FILE=backup.sql)
	@if [ -z "$(FILE)" ]; then \
		echo "Error: Please specify FILE=backup.sql"; \
		exit 1; \
	fi
	@echo "Restoring database from $(FILE)..."
	cat $(FILE) | $(DOCKER_COMPOSE) exec -T db psql -U postgres trading_analytics
	@echo "Restore completed"

stats: ## Show project statistics
	@echo "=== Project Statistics ==="
	@echo "Python files:"
	@find . -name "*.py" -not -path "./venv/*" -not -path "./.venv/*" | wc -l
	@echo "Lines of code:"
	@find . -name "*.py" -not -path "./venv/*" -not -path "./.venv/*" -exec wc -l {} + | tail -1
	@echo "Test files:"
	@find tests -name "test_*.py" 2>/dev/null | wc -l || echo "0"
	@echo ""

dev: ## Start development environment
	@echo "Starting development environment..."
	@$(MAKE) docker-up
	@echo "Containers started. Access app at http://localhost:5000"
	@echo "Access pgAdmin at http://localhost:5050 (use --profile tools)"

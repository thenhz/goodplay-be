# GoodPlay Backend - Development Makefile
# Quick commands for development, testing, and deployment

# Variables
PYTHON = python3
PIP = pip3
PYTEST = pytest
FLASK_APP = app.py
TEST_RUNNER = python run_tests.py

# Colors for output
RED = \033[0;31m
GREEN = \033[0;32m
YELLOW = \033[1;33m
BLUE = \033[0;34m
NC = \033[0m # No Color

.PHONY: help install install-dev install-test clean test test-unit test-integration test-api test-coverage lint format run dev setup-db docker-build docker-run deploy-heroku

# Default target
help: ## Show this help message
	@echo "$(BLUE)GoodPlay Backend - Available Commands$(NC)"
	@echo "===================================="
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "$(GREEN)%-20s$(NC) %s\n", $$1, $$2}' $(MAKEFILE_LIST)

# Installation targets
install: ## Install production dependencies
	@echo "$(YELLOW)Installing production dependencies...$(NC)"
	$(PIP) install -r requirements.txt

install-dev: ## Install development dependencies
	@echo "$(YELLOW)Installing development dependencies...$(NC)"
	$(PIP) install -r requirements.txt
	$(PIP) install -r test_requirements.txt

install-test: ## Install only test dependencies
	@echo "$(YELLOW)Installing test dependencies...$(NC)"
	$(PIP) install -r test_requirements.txt

# Testing targets
test: ## Run all unit tests with coverage
	@echo "$(BLUE)Running all unit tests...$(NC)"
	$(TEST_RUNNER)

test-working: ## Run only working tests (guaranteed to pass)
	@echo "$(BLUE)Running working test suite...$(NC)"
	$(TEST_RUNNER) --working

test-unit: ## Run unit tests only
	@echo "$(BLUE)Running unit tests...$(NC)"
	$(TEST_RUNNER) --no-coverage

test-module: ## Run tests for specific module (usage: make test-module MODULE=auth)
	@echo "$(BLUE)Running tests for module: $(MODULE)$(NC)"
	$(TEST_RUNNER) --module $(MODULE)

test-integration: ## Run integration tests
	@echo "$(BLUE)Running integration tests...$(NC)"
	$(TEST_RUNNER) --integration

test-api: ## Run API endpoint tests
	@echo "$(BLUE)Running API tests...$(NC)"
	$(TEST_RUNNER) --api

test-coverage: ## Generate detailed coverage report
	@echo "$(BLUE)Generating coverage report...$(NC)"
	$(TEST_RUNNER) --coverage

test-pipeline: ## Run tests suitable for CI/CD pipeline
	@echo "$(BLUE)Running pipeline tests...$(NC)"
	$(TEST_RUNNER) --pipeline

test-auth: ## Run authentication tests
	@echo "$(BLUE)Running authentication tests...$(NC)"
	$(TEST_RUNNER) --module auth

test-preferences: ## Run preferences tests
	@echo "$(BLUE)Running preferences tests...$(NC)"
	$(TEST_RUNNER) --module preferences

test-social: ## Run social features tests
	@echo "$(BLUE)Running social tests...$(NC)"
	$(TEST_RUNNER) --module social

test-games: ## Run game engine tests
	@echo "$(BLUE)Running game engine tests...$(NC)"
	$(TEST_RUNNER) --module games

test-class: ## Run specific test class (usage: make test-class CLASS=TestAuth)
	@echo "$(BLUE)Running test class: $(CLASS)$(NC)"
	$(TEST_RUNNER) --class $(CLASS)

test-check: ## Check test environment
	@echo "$(BLUE)Checking test environment...$(NC)"
	$(TEST_RUNNER) --check

test-install: ## Install test dependencies
	@echo "$(BLUE)Installing test dependencies...$(NC)"
	$(TEST_RUNNER) --install

test-clean: ## Clean test artifacts
	@echo "$(BLUE)Cleaning test artifacts...$(NC)"
	$(TEST_RUNNER) --cleanup

# Code quality targets
lint: ## Run code linting
	@echo "$(BLUE)Running code linting...$(NC)"
	flake8 app tests
	mypy app

format: ## Format code with black and isort
	@echo "$(BLUE)Formatting code...$(NC)"
	black app tests
	isort app tests

security: ## Run security checks
	@echo "$(BLUE)Running security checks...$(NC)"
	bandit -r app

# Development targets
run: ## Run development server
	@echo "$(BLUE)Starting development server...$(NC)"
	$(PYTHON) $(FLASK_APP)

dev: ## Run development server with auto-reload
	@echo "$(BLUE)Starting development server with auto-reload...$(NC)"
	FLASK_ENV=development $(PYTHON) $(FLASK_APP)

# Database targets
setup-db: ## Setup development database (if needed)
	@echo "$(BLUE)Setting up development database...$(NC)"
	@echo "$(YELLOW)Note: Ensure MongoDB is running on localhost:27017$(NC)"

db-seed: ## Seed database with test data
	@echo "$(BLUE)Seeding database with test data...$(NC)"
	$(PYTHON) -c "from scripts.seed_db import main; main()"

# Docker targets
docker-build: ## Build Docker image
	@echo "$(BLUE)Building Docker image...$(NC)"
	docker build -t goodplay-backend .

docker-run: ## Run Docker container
	@echo "$(BLUE)Running Docker container...$(NC)"
	docker run -p 5000:5000 --env-file .env goodplay-backend

# Deployment targets
deploy-heroku: ## Deploy to Heroku
	@echo "$(BLUE)Deploying to Heroku...$(NC)"
	git push heroku main

# Utility targets
clean: ## Clean temporary files and caches
	@echo "$(BLUE)Cleaning temporary files...$(NC)"
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	rm -rf .coverage htmlcov .pytest_cache test-results.xml

setup: install-dev ## Setup development environment
	@echo "$(GREEN)Development environment setup complete!$(NC)"
	@echo "$(YELLOW)Next steps:$(NC)"
	@echo "1. Copy .env.example to .env and configure"
	@echo "2. Start MongoDB: brew services start mongodb (macOS)"
	@echo "3. Run tests: make test"
	@echo "4. Start development server: make dev"

# CI/CD targets
ci-install: ## Install dependencies for CI
	@echo "$(BLUE)Installing CI dependencies...$(NC)"
	$(PIP) install --upgrade pip
	$(PIP) install -r requirements.txt
	$(PIP) install -r test_requirements.txt

ci-test: ## Run tests for CI/CD
	@echo "$(BLUE)Running CI tests...$(NC)"
	$(TEST_RUNNER) --pipeline

ci-lint: ## Run linting for CI/CD
	@echo "$(BLUE)Running CI linting...$(NC)"
	flake8 app tests --max-line-length=88 --extend-ignore=E203,W503
	black --check app tests
	isort --check-only app tests

# Release targets
version: ## Show current version
	@echo "$(BLUE)Current version:$(NC)"
	@grep -E '^version = ' setup.py || echo "Version not found"

release: test lint ## Prepare release (run tests and linting)
	@echo "$(GREEN)Release checks passed!$(NC)"

# Monitoring and logs
logs: ## Show application logs
	@echo "$(BLUE)Showing recent logs...$(NC)"
	tail -f logs/app.log 2>/dev/null || echo "No log file found"

status: ## Show application status
	@echo "$(BLUE)Application Status$(NC)"
	@echo "=================="
	@curl -s http://localhost:5000/api/core/health | python -m json.tool || echo "Application not running"

# Database management
db-migrate: ## Run database migrations (if applicable)
	@echo "$(BLUE)Running database migrations...$(NC)"
	@echo "$(YELLOW)Note: MongoDB doesn't require traditional migrations$(NC)"

db-backup: ## Backup database
	@echo "$(BLUE)Creating database backup...$(NC)"
	mongodump --db goodplay_db --out backups/$(shell date +%Y%m%d_%H%M%S)

db-restore: ## Restore database from backup (usage: make db-restore BACKUP=path/to/backup)
	@echo "$(BLUE)Restoring database from: $(BACKUP)$(NC)"
	mongorestore --db goodplay_db $(BACKUP)/goodplay_db

# Performance testing
benchmark: ## Run performance benchmarks
	@echo "$(BLUE)Running performance benchmarks...$(NC)"
	$(PYTEST) tests/ -m benchmark --benchmark-only

# Security scanning
audit: ## Run security audit
	@echo "$(BLUE)Running security audit...$(NC)"
	pip-audit
	bandit -r app -f json -o security-report.json

# Documentation
docs: ## Generate documentation
	@echo "$(BLUE)Generating documentation...$(NC)"
	@echo "$(YELLOW)Documentation available in:$(NC)"
	@echo "- README.md"
	@echo "- CLAUDE.md"
	@echo "- CONTRIBUTING.md"
	@echo "- POSTMAN_TESTING.md"

# Health checks
health-check: ## Perform health checks
	@echo "$(BLUE)Performing health checks...$(NC)"
	@curl -f http://localhost:5000/api/core/health || echo "Health check failed"
	@echo "$(YELLOW)MongoDB status:$(NC)"
	@mongosh --eval "db.adminCommand('ping')" --quiet || echo "MongoDB connection failed"
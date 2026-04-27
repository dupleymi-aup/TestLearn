# TestLearn Makefile
# Simplified commands for local development

.PHONY: help install run test clean docker-dev docker-prod lint format

help: ## Show this help message
@echo "TestLearn - Available commands:"
@echo ""
@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'
@echo ""

install: ## Install dependencies
pip install -r requirements.txt

run: ## Run the application locally
python main.py

test: ## Run all tests
python -m pytest tests/ -v

test-cov: ## Run tests with coverage
python -m pytest tests/ -v --cov=app --cov-report=html

clean: ## Clean up cache and database files
rm -rf __pycache__/ .pytest_cache/ .coverage htmlcov/
find . -type d -name "__pycache__" -exec rm -rf {} +
find . -type f -name "*.pyc" -delete
@echo "Cleanup complete!"

lint: ## Run linter (if configured)
@echo "Running linter..."
python -m flake8 app/ tests/ main.py --max-line-length=100 || echo "flake8 not installed, skipping..."

format: ## Format code with black
@echo "Formatting code..."
python -m black app/ tests/ main.py || echo "black not installed, skipping..."

docker-dev: ## Build and run Docker containers for development
docker-compose -f docker-compose.dev.yml up --build

docker-prod: ## Build and run Docker containers for production
docker-compose -f docker-compose.prod.yml up --build

db-reset: ## Reset database (WARNING: deletes all data!)
@echo "WARNING: This will delete all data in the database!"
@read -p "Are you sure? (y/N): " confirm && [ "$$confirm" = "y" ] || exit 1
rm -f testlearn.db
python main.py
@echo "Database reset complete!"

init-db: ## Initialize database with test data
python -c "from app.database.db import init_database; init_database()"
@echo "Database initialized!"

dev: install run ## Install dependencies and run (shortcut)

# AWS GenAI RAG Workshop Makefile

.PHONY: help install dev-install test lint format localstack-up localstack-down clean

PYTHON := python3
UV := uv
PANDOC := pandoc

# File dependencies
README.md: README.org
	@echo "Generating README.md from README.org..."
	@if command -v $(PANDOC) >/dev/null 2>&1; then \
		$(PANDOC) -f org -t gfm -o $@ $<; \
	else \
		echo "Warning: pandoc not found, creating simple README.md"; \
		echo "# AWS GenAI RAG Workshop 2025" > $@; \
		echo "" >> $@; \
		echo "This project requires pandoc to generate the full README.md from README.org." >> $@; \
		echo "Install pandoc or view README.org directly." >> $@; \
	fi

.venv: README.md
	@echo "Creating virtual environment with uv..."
	$(UV) venv

help: ## Show this help message
	@echo "AWS GenAI RAG Workshop - Available targets:"
	@awk 'BEGIN {FS = ":.*##"; printf "\nUsage:\n  make \033[36m<target>\033[0m\n"} /^[a-zA-Z_-]+:.*?##/ { printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2 } /^##@/ { printf "\n\033[1m%s\033[0m\n", substr($$0, 5) } ' $(MAKEFILE_LIST)

##@ Setup

install: .venv ## Install production dependencies with uv
	$(UV) pip sync
	$(UV) pip install -e .

dev-install: .venv ## Install all dependencies including dev tools
	$(UV) pip install -e ".[dev,sagemaker]"

##@ LocalStack

localstack-up: ## Start LocalStack and initialize AWS services
	docker-compose up -d localstack
	@echo "Waiting for LocalStack to be ready..."
	@sleep 10
	chmod +x localstack/init-aws.sh
	./localstack/init-aws.sh

localstack-down: ## Stop LocalStack
	docker-compose down

localstack-logs: ## Show LocalStack logs
	docker-compose logs -f localstack

##@ Development

test: ## Run tests with pytest
	$(UV) run pytest tests/ -v

test-cov: ## Run tests with coverage
	$(UV) run pytest tests/ --cov=src --cov-report=html --cov-report=term

lint: py-lint org-lint ## Run all linting (Python and Org-mode)

py-lint: ## Run Python linting with ruff
	$(UV) run ruff check src/ tests/

org-lint: ## Run Org-mode linting with Emacs
	@echo "Running org-lint on all .org files..."
	@find . -maxdepth 2 -name "*.org" -not -path "./.tmp/*" -not -path "./.support/*" | \
		xargs emacs --batch -l make-support.el -f batch-org-lint 2>&1 | \
		grep -v "^Loading"

format: ## Format code with black and ruff
	$(UV) run black src/ tests/
	$(UV) run ruff check --fix src/ tests/

typecheck: ## Run type checking with mypy
	$(UV) run mypy src/

##@ Notebooks

notebook: ## Start Jupyter notebook server
	$(UV) run jupyter notebook notebooks/

convert-notebooks: ## Convert org notebooks to Python scripts (deprecated, use 'make tangle')
	@echo "This target is deprecated. Please use 'make tangle' instead."
	@$(MAKE) tangle

tangle: ## Extract code from org notebooks into subdirectories
	@echo "Tangling code from org notebooks..."
	@find . -maxdepth 2 -name "*.org" -not -path "./.tmp/*" -not -path "./.support/*" | \
		xargs emacs --batch -l make-support.el -f batch-org-tangle 2>&1 | \
		grep -v "^Loading"

##@ Workshop

run-rag-pipeline: ## Run the RAG pipeline demo
	$(UV) run python -m src.rag.pipeline

run-sql-agent: ## Run the SQL agent demo
	$(UV) run python -m src.agents.sql_agent

calculate-costs: ## Calculate workshop costs
	$(UV) run python -m src.utils.cost_calculator

##@ Cleanup

clean: ## Clean generated files and caches
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name ".DS_Store" -delete
	rm -rf .ruff_cache .mypy_cache .pytest_cache
	rm -rf htmlcov/ .coverage

clean-all: clean ## Clean everything including LocalStack data
	docker-compose down -v
	rm -rf localstack/volume/

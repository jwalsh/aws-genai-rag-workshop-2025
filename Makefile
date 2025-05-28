# AWS GenAI RAG Workshop Makefile

.PHONY: help install dev-install test lint format localstack-up localstack-down clean

PYTHON := python3
UV := uv
PANDOC := pandoc

# File dependencies
README.md: README.org
	@echo "Generating README.md from README.org..."
	@emacs --batch --eval "(require 'ox-md)" --eval "(find-file \"$<\")" --eval "(org-md-export-to-markdown)"

.venv: README.md
	@echo "Creating virtual environment with uv..."
	$(UV) venv

help: ## Show this help message
	@echo "AWS GenAI RAG Workshop - Available targets:"
	@awk 'BEGIN {FS = ":.*##"; printf "\nUsage:\n  make \033[36m<target>\033[0m\n"} /^[a-zA-Z_-]+:.*?##/ { printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2 } /^##@/ { printf "\n\033[1m%s\033[0m\n", substr($$0, 5) } ' $(MAKEFILE_LIST)

##@ Setup

setup: README.md ## Run initial setup (creates venv and installs all dependencies)
	@bash scripts/setup.sh

deps: dev-install ## Install all dependencies (alias for dev-install)

install: .venv ## Install production dependencies with uv
	$(UV) pip sync
	$(UV) pip install -e .

dev-install: .venv ## Install all dependencies including dev tools
	$(UV) pip install -e ".[dev,sagemaker]"

dev: dev-install ## Alias for dev-install
develop: dev-install ## Alias for dev-install

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

##@ OS Compatibility Testing

test-compatibility: ## Test Python-only compatibility (Level 1)
	@echo "Testing Python-only compatibility..."
	$(UV) run python test_compatibility.py

test-level1: test-compatibility ## Run Level 1 tests (Python-only, all OSes)
	@echo "Running Level 1 (Python-only) tests..."
	$(UV) run pytest tests/test_rag.py -v -k "not aws and not docker"

test-level2: ## Run Level 2 tests (with PostgreSQL)
	@echo "Testing Level 2 (with PostgreSQL)..."
	docker compose up -d postgres
	@sleep 5
	$(UV) run pytest tests/test_text_to_sql.py -v

test-level3: ## Run Level 3 tests (with LocalStack)
	@echo "Testing Level 3 (with LocalStack)..."
	docker compose up -d
	@sleep 10
	awslocal s3 ls
	$(UV) run pytest tests/ -v -k "localstack"

test-level4: ## Run Level 4 tests (with real AWS)
	@echo "Testing Level 4 (with real AWS)..."
	@echo "Ensure AWS_PROFILE=dev is set"
	aws s3 ls
	$(UV) run pytest tests/ -v -k "aws" --aws-integration

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

data:
	@mkdir -p $@

data/rogets_thesaurus.pdf: | data ## Download Roget's Thesaurus PDF for RAG examples
	@echo "📥 Downloading Roget's Thesaurus PDF..."
	@curl -L "https://ia903407.us.archive.org/30/items/thesaurusofengli00roge_1/thesaurusofengli00roge_1.pdf" -o $@
	@echo "✅ Downloaded: $@"

download-data: data/rogets_thesaurus.pdf ## Download all sample data

run-rag-pipeline: ## Run the RAG pipeline demo
	$(UV) run python -m src.rag.pipeline

run-sql-agent: ## Run the SQL agent demo
	$(UV) run python -m src.agents.sql_agent

calculate-costs: ## Calculate workshop costs
	$(UV) run python -m src.utils.cost_calculator

##@ Documentation

presentation.pdf: presentation.org ## Generate presentation PDF from org file
	@echo "Generating presentation PDF..."
	@emacs --batch --eval "(require 'ox-beamer)" \
		--eval "(find-file \"presentation.org\")" \
		--eval "(org-beamer-export-to-pdf)"

presentation.html: presentation.org ## Generate presentation HTML (standard HTML export)
	@echo "Generating presentation HTML..."
	@emacs --batch --eval "(require 'ox-html)" \
		--eval "(find-file \"presentation.org\")" \
		--eval "(org-html-export-to-html)"

presentation-html: presentation.html ## Alias for presentation.html target

##@ Cleanup

clean: ## Clean generated files and caches
	@bash scripts/clean-cache.sh

clean-all: clean ## Clean everything including LocalStack data
	docker-compose down -v
	rm -rf localstack/volume/

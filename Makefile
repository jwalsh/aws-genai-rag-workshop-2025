# AWS GenAI RAG Workshop Makefile

.PHONY: help install dev-install test lint format localstack-up localstack-down clean

UV := uv

# Default target
help: ## Show this help message
	@echo "AWS GenAI RAG Workshop - Available targets:"
	@awk 'BEGIN {FS = ":.*##"; printf "\nUsage:\n  make \033[36m<target>\033[0m\n"} /^[a-zA-Z_-]+:.*?##/ { printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2 } /^##@/ { printf "\n\033[1m%s\033[0m\n", substr($$0, 5) } ' $(MAKEFILE_LIST)

# File dependencies
README.md: README.org
	@echo "Generating README.md from README.org..."
	@emacs --batch --eval "(require 'ox-md)" --eval "(find-file \"$<\")" --eval "(org-md-export-to-markdown)"

.venv: README.md
	@echo "Creating virtual environment with uv..."
	$(UV) venv

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

##@ Environment Management

check-env: ## Check which AWS environment is active
	@$(UV) run python scripts/check-env.py

aws-test: check-env ## Quick test of AWS connectivity (real or LocalStack)
	@echo ""

use-aws: ## Configure environment for real AWS (prints commands to run)
	@echo "Run these commands to use real AWS:"
	@echo "  export AWS_PROFILE=dev"
	@echo "  unset AWS_ENDPOINT_URL"
	@echo "Or for this session only:"
	@echo "  AWS_PROFILE=dev AWS_ENDPOINT_URL= make <target>"

use-localstack: ## Configure environment for LocalStack (prints commands to run)
	@echo "Run these commands to use LocalStack:"
	@echo "  unset AWS_PROFILE"
	@echo "  export AWS_ENDPOINT_URL=http://localhost:4566"
	@echo "Or use the default .env settings"

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
	@echo "Using AWS_PROFILE=dev and unsetting LocalStack endpoint"
	@AWS_PROFILE=dev AWS_ENDPOINT_URL= $(UV) run aws s3 ls
	@AWS_PROFILE=dev AWS_ENDPOINT_URL= $(UV) run pytest tests/ -v -k "aws" --aws-integration

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

data/consolation_of_philosophy.txt: | data ## Download Boethius' Consolation of Philosophy
	@echo "📜 Downloading Consolation of Philosophy..."
	@curl -L "https://ia600205.us.archive.org/8/items/theconsolationof14328gut/14328-8.txt" -o $@
	@echo "✅ Downloaded: $@"

data/critique_of_pure_reason.txt: | data ## Download Kant's Critique of Pure Reason
	@echo "🧠 Downloading Critique of Pure Reason..."
	@curl -L "https://ia600206.us.archive.org/27/items/thecritiqueofpur04280gut/cprrn10.txt" -o $@
	@echo "✅ Downloaded: $@"

data/wittgenstein_philosophical_grammar.pdf: | data ## Download Wittgenstein's Philosophical Grammar
	@echo "🔍 Downloading Wittgenstein's Philosophical Grammar..."
	@curl -L "https://dn721807.ca.archive.org/0/items/ludwig-wittgenstein-philosophical-grammar/Ludwig%20Wittgenstein%20-%20Philosophical%20Grammar.pdf" -o $@
	@echo "✅ Downloaded: $@"

download-philosophy: data/consolation_of_philosophy.txt data/critique_of_pure_reason.txt data/wittgenstein_philosophical_grammar.pdf ## Download philosophical texts

download-data: data/rogets_thesaurus.pdf ## Download all sample data

download-all: download-data download-philosophy ## Download all texts (thesaurus + philosophy)

run-rag-pipeline: ## Run the RAG pipeline demo
	$(UV) run python -m src.rag.pipeline

run-sql-agent: ## Run the SQL agent demo
	$(UV) run python -m src.agents.sql_agent

run-philosophical-rag: download-philosophy ## Run the philosophical RAG demo
	$(UV) run python -m src.demos.philosophical_rag

calculate-costs: ## Calculate workshop costs
	$(UV) run python -m src.utils.cost_calculator

validate-level1: ## Run Level 1 RAG validation (no AWS required)
	@echo "Running Level 1 RAG validation..."
	$(UV) run python scripts/validate_rag_level1.py

validate-workshop: ## Run full workshop validation script
	@echo "Running workshop validation..."
	@bash scripts/validate-workshop.sh

validate-ci: ## Run CI-friendly validation
	$(UV) run python scripts/validate_rag_level1.py --ci

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

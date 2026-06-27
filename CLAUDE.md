* CLAUDE.org

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

** Development Commands

*** Setup
#+begin_src bash
make init-repo        # Initialize repository structure
make dev-install      # Install all dependencies including dev tools
make localstack-up    # Start LocalStack with AWS services
#+end_src

*** Testing & Quality
#+begin_src bash
make test            # Run pytest
make test-cov        # Run tests with coverage
make lint            # Run ruff linting
make format          # Format code with black and ruff
make typecheck       # Run mypy type checking
#+end_src

*** Running Examples
#+begin_src bash
make run-rag-pipeline    # Run RAG pipeline demo
make run-sql-agent       # Run SQL agent demo
make notebook            # Start Jupyter notebook server
#+end_src

*** Cleanup
#+begin_src bash
make localstack-down     # Stop LocalStack
make clean              # Clean generated files
#+end_src

** Architecture Overview

This is an AWS GenAI RAG Workshop that demonstrates various RAG patterns using AWS services (via LocalStack for local development).

*** Core Components

**** RAG Pipeline (=src/rag/pipeline.py=)
- Orchestrates document processing, embedding, storage, and retrieval
- Uses DynamoDB for metadata and S3 for document/embedding storage
- Supports multiple chunking strategies and embedding models

**** Key Classes
- =DocumentChunker=: Splits documents (default: 512 chars, 50 overlap)
- =EmbeddingGenerator=: Creates embeddings via Bedrock or sentence-transformers
- =VectorRetriever=: FAISS-based retrieval with optional reranking
- =SQLAgent=: Natural language to SQL conversion using Bedrock

**** AWS Services Used
- S3: Document and embedding storage
- DynamoDB: Vector metadata with GSI for doc_type queries
- Bedrock: LLMs (Claude, Titan) and embeddings
- SageMaker: Fine-tuning support
- PostgreSQL: Sample database for SQL agent

*** Workshop Structure

The workshop consists of 5 progressive modules in =notebooks/=:
1. *01_rag_basics.org*: Introduction to RAG concepts
2. *02_advanced_rag.org*: Reranking, hybrid search, evaluation
3. *03_text_to_sql.org*: Natural language database queries
4. *04_fine_tuning.org*: Model customization with SageMaker
5. *05_cost_analysis.org*: AWS cost optimization strategies

*** LocalStack Configuration

LocalStack runs on port 4566 with these pre-configured resources:
- S3 buckets: workshop-rag-documents, workshop-embeddings, workshop-model-artifacts
- DynamoDB table: workshop-vector-metadata
- PostgreSQL database: workshop_db (port 5432)

** Testing Guidelines

- Tests are in =tests/= directory
- Run individual tests: =pytest tests/test_rag.py::test_specific_function=
- Mock AWS services using moto or LocalStack endpoints
- Test data should use the sample-data directory

** Git Commit Guidelines

When making commits:
- Use conventional commit format: =<type>(<scope>): <description>=
- Use =--trailer= for Co-Authored-By instead of in the commit body
- Never include "Generated with" in the commit message body
- Always use =--no-gpg-sign= flag

*** Correct commit format:
#+begin_src bash
git commit --no-gpg-sign -m "feat(rag): add document chunking optimization" \
  --trailer "Co-Authored-By: Claude <noreply@anthropic.com>"
#+end_src

*** Incorrect format (avoid):
#+begin_src bash
# Don't put co-authorship in the message body
git commit -m "feat(rag): add chunking

Generated with Claude Code
Co-Authored-By: Claude <noreply@anthropic.com>"
#+end_src
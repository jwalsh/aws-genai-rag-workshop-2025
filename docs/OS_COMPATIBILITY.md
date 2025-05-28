# OS Compatibility Guide

This workshop is designed to work across multiple operating systems with different levels of functionality.

## Quick Compatibility Matrix

| Feature | FreeBSD | Linux (ARM64) | macOS |
|---------|---------|---------------|--------|
| Python exercises | ✓ | ✓ | ✓ |
| PostgreSQL | ⚠️ | ✓ | ✓ |
| LocalStack | ❌ | ⚠️ | ✓ |
| AWS Integration | ❌ | ❌ | ✓ |

## Setup by OS

### All Operating Systems (Level 1 - Python Only)

```bash
# Clone the repository
git clone https://github.com/jwalsh/aws-genai-rag-workshop-2025.git
cd aws-genai-rag-workshop-2025

# Install Python dependencies with uv
curl -LsSf https://astral.sh/uv/install.sh | sh
uv venv
source .venv/bin/activate  # or .venv/bin/activate.fish for fish shell
uv sync

# Test compatibility
python test_compatibility.py
```

### FreeBSD 14.2

```bash
# Install required packages
pkg install python311 py311-pip

# Use uv for dependency management
curl -LsSf https://astral.sh/uv/install.sh | sh

# Focus on Python-only exercises:
# - notebooks/01_rag_basics.org (skip AWS sections)
# - notebooks/05_cost_analysis.org
```

### Linux on Raspberry Pi (via Tailscale)

```bash
# Ensure you have Docker if you want Level 2 features
sudo apt-get update
sudo apt-get install docker.io docker-compose

# For Python packages on ARM64
uv sync

# Can run Levels 1-2:
# - All Python exercises
# - PostgreSQL-based examples
# - Limited LocalStack (resource constraints)
```

### macOS (Apple Silicon)

```bash
# Install Docker Desktop for Mac (Apple Silicon version)
# Install AWS CLI
brew install awscli

# For LocalStack
docker compose up -d localstack

# For full AWS (ensure ~/.aws/credentials has [dev] profile)
export AWS_PROFILE=dev
aws bedrock list-foundation-models --region us-east-1
```

## Exercise Levels

### Level 1: Python Only (All OSes)
- Basic RAG concepts
- Local embeddings with sentence-transformers
- Text chunking and processing
- Cost analysis and estimation
- FAISS vector operations

### Level 2: With PostgreSQL
- Text-to-SQL demonstrations
- Database introspection
- Query generation examples

### Level 3: With LocalStack
- S3 storage simulation
- Mock Bedrock API calls
- Full RAG pipeline locally

### Level 4: Real AWS
- Bedrock API integration
- CloudWatch monitoring
- Production cost tracking

## Troubleshooting

### FreeBSD Issues
- No Docker: Use jails or bhyve for containerization
- Alternative: Connect to remote PostgreSQL

### ARM64 Issues
- Some packages may need compilation
- Use pre-built wheels when available
- Monitor memory usage on Raspberry Pi

### General Issues
- Run `python test_compatibility.py` to diagnose
- Check `uv.lock` for exact versions
- See `WIP.org` for current testing status

## Minimal Requirements

- Python 3.11+
- 2GB RAM minimum (4GB recommended)
- 5GB disk space
- Internet connection for model downloads
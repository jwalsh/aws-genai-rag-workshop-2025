#!/bin/bash
# Initial setup script for AWS GenAI RAG Workshop

set -e  # Exit on error

echo "🚀 AWS GenAI RAG Workshop - Initial Setup"
echo "========================================"

# Check prerequisites
echo "📋 Checking prerequisites..."

# Check Python version
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.11 or higher."
    exit 1
fi

PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
REQUIRED_VERSION="3.11"
if [ "$(printf '%s\n' "$REQUIRED_VERSION" "$PYTHON_VERSION" | sort -V | head -n1)" != "$REQUIRED_VERSION" ]; then
    echo "❌ Python $PYTHON_VERSION found, but Python $REQUIRED_VERSION or higher is required."
    exit 1
fi
echo "✅ Python $PYTHON_VERSION"

# Check uv
if ! command -v uv &> /dev/null; then
    echo "❌ uv is not installed. Installing..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.cargo/bin:$PATH"
fi
echo "✅ uv is installed"

# Check Docker
if ! command -v docker &> /dev/null; then
    echo "⚠️  Docker is not installed. You'll need Docker for LocalStack."
else
    echo "✅ Docker is installed"
fi

# Check AWS CLI
if ! command -v aws &> /dev/null; then
    echo "⚠️  AWS CLI is not installed. Installing via uv..."
    uv pip install awscli
else
    echo "✅ AWS CLI is installed"
fi

# Clean up any existing environment
echo ""
echo "🧹 Cleaning up existing environment..."
rm -rf .venv
rm -f README.md  # Force regeneration

# Create virtual environment
echo ""
echo "🔧 Creating virtual environment..."
uv venv

# Install dependencies
echo ""
echo "📦 Installing dependencies..."
uv pip install -e ".[dev,sagemaker]"

# Verify installation
echo ""
echo "✨ Verifying installation..."
uv run python -c "import boto3, langchain, pandas; print('✅ Core packages installed successfully')"

echo ""
echo "🎉 Setup complete! Next steps:"
echo "   1. Activate the environment: source .venv/bin/activate"
echo "   2. Start LocalStack: make localstack-up"
echo "   3. Run tests: make test"
echo "   4. View all commands: make help"
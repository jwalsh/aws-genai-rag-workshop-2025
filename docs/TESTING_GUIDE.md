# Testing Guide for Multi-OS Compatibility

## Quick Start

```bash
# Test your system's compatibility
make test-compatibility

# Run tests appropriate for your OS
make test-level1  # All OSes (Python only)
make test-level2  # Linux/macOS (with Docker)
make test-level3  # macOS (with LocalStack)
make test-level4  # macOS (with AWS account)
```

## Testing Levels

### Level 1: Python-Only (All OSes)
- **Compatible with**: FreeBSD, Linux (ARM64), macOS
- **Requirements**: Python 3.11+, 2GB RAM
- **Tests**: Basic RAG, embeddings, chunking, cost analysis
- **Command**: `make test-level1`

### Level 2: With PostgreSQL
- **Compatible with**: Linux (ARM64), macOS
- **Requirements**: Docker, 4GB RAM
- **Tests**: Text-to-SQL, database operations
- **Command**: `make test-level2`

### Level 3: With LocalStack
- **Compatible with**: macOS (primary), Linux (limited)
- **Requirements**: Docker, 8GB RAM, LocalStack
- **Tests**: AWS service mocking, full RAG pipeline
- **Command**: `make test-level3`

### Level 4: With Real AWS
- **Compatible with**: macOS with AWS credentials
- **Requirements**: AWS account, configured profile
- **Tests**: Real Bedrock API, production features
- **Command**: `make test-level4`

## OS-Specific Instructions

### FreeBSD 14.2
```bash
# Install Python
pkg install python311 py311-pip

# Run compatibility test
python test_compatibility.py

# Run Python-only exercises
make test-level1
```

### Raspberry Pi (Linux ARM64)
```bash
# Via Tailscale connection
ssh pi@<tailscale-ip>

# Run levels 1-2
make test-level1
make test-level2  # If Docker is available
```

### macOS (Apple Silicon)
```bash
# Full testing suite
make test-level1  # Basic
make test-level2  # With PostgreSQL
make test-level3  # With LocalStack

# With AWS profile configured
export AWS_PROFILE=dev
make test-level4  # Real AWS
```

## Debugging

### Common Issues

1. **Import errors on FreeBSD**
   - Ensure all Python packages are installed
   - Some C extensions may need ports

2. **Memory issues on Raspberry Pi**
   - Reduce batch sizes in examples
   - Monitor with `htop`

3. **LocalStack connection errors**
   - Check Docker is running
   - Verify port 4566 is accessible
   - Run `docker compose logs localstack`

4. **AWS authentication errors**
   - Check `~/.aws/credentials`
   - Verify profile name matches
   - Test with `aws s3 ls --profile dev`

### Test Output

Each level produces a summary:
```
Testing Level 1...
✓ RAG Embeddings
✓ RAG Chunking
✓ Vector Store
✓ Cost Calculator
✓ Sentence Transformers
✓ FAISS
✓ Pandas

Summary: 7/7 tests passed
✓ This system is compatible with Level 1 exercises!
```

## Next Steps

1. Start with `notebooks/01_rag_basics.org`
2. Skip sections marked "Requires Docker" on FreeBSD
3. Use LocalStack sections only on supported OSes
4. AWS sections require Level 4 setup

See `WIP.org` for current testing status across all platforms.
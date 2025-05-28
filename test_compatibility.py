#!/usr/bin/env python3
"""
Compatibility test script for AWS GenAI RAG Workshop
Tests Level 1 (Python-only) functionality across different OSes
"""

import sys
import platform
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

def test_imports():
    """Test that all core Python modules can be imported."""
    print("Testing core imports...")
    
    tests = []
    
    # Test RAG modules
    try:
        from src.rag.embeddings import EmbeddingGenerator
        tests.append(("✓", "RAG Embeddings"))
    except Exception as e:
        tests.append(("✗", f"RAG Embeddings: {e}"))
    
    try:
        from src.rag.chunking import SimpleChunker
        tests.append(("✓", "RAG Chunking"))
    except Exception as e:
        tests.append(("✗", f"RAG Chunking: {e}"))
    
    try:
        from src.rag.vector_store import FAISSVectorStore
        tests.append(("✓", "Vector Store"))
    except Exception as e:
        tests.append(("✗", f"Vector Store: {e}"))
    
    try:
        from src.utils.cost_calculator import RAGCostEstimator
        tests.append(("✓", "Cost Calculator"))
    except Exception as e:
        tests.append(("✗", f"Cost Calculator: {e}"))
    
    # Test third-party dependencies
    try:
        import sentence_transformers
        tests.append(("✓", "Sentence Transformers"))
    except Exception as e:
        tests.append(("✗", f"Sentence Transformers: {e}"))
    
    try:
        import faiss
        tests.append(("✓", "FAISS"))
    except Exception as e:
        tests.append(("✗", f"FAISS: {e}"))
    
    try:
        import pandas
        tests.append(("✓", "Pandas"))
    except Exception as e:
        tests.append(("✗", f"Pandas: {e}"))
    
    return tests

def test_basic_functionality():
    """Test basic RAG functionality without external dependencies."""
    print("\nTesting basic functionality...")
    
    tests = []
    
    # Test text chunking
    try:
        from src.rag.chunking import SimpleChunker
        chunker = SimpleChunker(chunk_size=100, overlap=20)
        sample_text = "This is a test. " * 50
        chunks = chunker.chunk_text(sample_text)
        tests.append(("✓", f"Text chunking: {len(chunks)} chunks created"))
    except Exception as e:
        tests.append(("✗", f"Text chunking: {e}"))
    
    # Test cost calculation
    try:
        from src.utils.cost_calculator import RAGCostEstimator
        estimator = RAGCostEstimator()
        cost = estimator.estimate_embedding_cost(100, 500)
        tests.append(("✓", f"Cost estimation: ${cost['cost_usd']:.6f}"))
    except Exception as e:
        tests.append(("✗", f"Cost estimation: {e}"))
    
    # Test local embeddings (may download model on first run)
    try:
        from src.rag.embeddings import EmbeddingGenerator
        generator = EmbeddingGenerator()
        embedding = generator.generate("test text")
        tests.append(("✓", f"Embeddings: dimension {embedding.shape[1]}"))
    except Exception as e:
        tests.append(("✗", f"Embeddings: {e}"))
    
    return tests

def main():
    """Run all compatibility tests."""
    print("=" * 60)
    print("AWS GenAI RAG Workshop - Compatibility Test")
    print("=" * 60)
    
    # System information
    print(f"\nSystem Information:")
    print(f"  OS: {platform.system()}")
    print(f"  Version: {platform.version()}")
    print(f"  Machine: {platform.machine()}")
    print(f"  Python: {sys.version}")
    
    # Run import tests
    print("\n" + "-" * 40)
    import_results = test_imports()
    for status, message in import_results:
        print(f"  {status} {message}")
    
    # Run functionality tests
    print("\n" + "-" * 40)
    func_results = test_basic_functionality()
    for status, message in func_results:
        print(f"  {status} {message}")
    
    # Summary
    print("\n" + "=" * 60)
    all_results = import_results + func_results
    passed = sum(1 for status, _ in all_results if status == "✓")
    total = len(all_results)
    
    print(f"Summary: {passed}/{total} tests passed")
    
    if passed == total:
        print("✓ This system is compatible with Level 1 (Python-only) exercises!")
        return 0
    else:
        print("✗ Some components are not working. Check the errors above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
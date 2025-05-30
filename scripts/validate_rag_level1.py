#!/usr/bin/env python3
"""
Level 1 RAG Validation Script
Simple download/chunk/pickle RAG pipeline that requires no AWS services.
Can run in CI/CD environments.
"""

import os
import pickle
import requests
from pathlib import Path
import numpy as np
from typing import List, Dict
import sys
import argparse


class SimpleRAG:
    def __init__(self, cache_dir="./rag_cache"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        
    def download_sample_text(self) -> str:
        """Download a sample text file"""
        cache_file = self.cache_dir / "sample_text.txt"
        
        if cache_file.exists():
            print("✓ Using cached text")
            return cache_file.read_text()
        
        print("→ Downloading sample text...")
        url = "https://www.gutenberg.org/files/74/74-0.txt"  # Tom Sawyer
        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            text = response.text
        except Exception as e:
            print(f"❌ Download failed: {e}")
            # Fallback to minimal text
            text = """This is a sample text for RAG validation. 
            Tom Sawyer was a boy who lived along the Mississippi River. 
            He had many adventures with his friend Huckleberry Finn. 
            One famous scene involves Tom convincing others to paint a fence for him.""" * 10
        
        # Cache it
        cache_file.write_text(text)
        print("✓ Downloaded and cached")
        return text
    
    def chunk_text(self, text: str, chunk_size: int = 500) -> List[str]:
        """Simple chunking by character count"""
        print(f"→ Chunking text (size={chunk_size})...")
        chunks = []
        words = text.split()
        current_chunk = []
        current_size = 0
        
        for word in words:
            current_chunk.append(word)
            current_size += len(word) + 1
            
            if current_size >= chunk_size:
                chunks.append(' '.join(current_chunk))
                current_chunk = []
                current_size = 0
        
        if current_chunk:
            chunks.append(' '.join(current_chunk))
        
        print(f"✓ Created {len(chunks)} chunks")
        return chunks
    
    def create_embeddings(self, chunks: List[str]) -> np.ndarray:
        """Create simple embeddings (hash-based for demo)"""
        print("→ Creating embeddings...")
        embeddings = []
        
        for chunk in chunks:
            # Simple hash-based embedding (not ML, but deterministic)
            words = chunk.lower().split()
            embedding = np.zeros(128)  # 128-dim embedding
            
            for word in words:
                # Simple hash to position
                positions = [hash(word + str(i)) % 128 for i in range(3)]
                for pos in positions:
                    embedding[pos] += 1.0
            
            # Normalize
            norm = np.linalg.norm(embedding)
            if norm > 0:
                embedding = embedding / norm
                
            embeddings.append(embedding)
        
        embeddings = np.array(embeddings)
        print(f"✓ Created embeddings with shape {embeddings.shape}")
        return embeddings
    
    def pickle_index(self, chunks: List[str], embeddings: np.ndarray) -> str:
        """Pickle the RAG index"""
        index_file = self.cache_dir / "rag_index.pkl"
        
        index = {
            'chunks': chunks,
            'embeddings': embeddings,
            'metadata': {
                'chunk_size': 500,
                'num_chunks': len(chunks),
                'embedding_dim': embeddings.shape[1],
                'version': '1.0'
            }
        }
        
        with open(index_file, 'wb') as f:
            pickle.dump(index, f)
        
        file_size = os.path.getsize(index_file) / 1024  # KB
        print(f"✓ Pickled index to {index_file} ({file_size:.1f} KB)")
        return str(index_file)
    
    def search(self, query: str, index_file: str, top_k: int = 3) -> List[Dict]:
        """Search the RAG index"""
        # Load index
        with open(index_file, 'rb') as f:
            index = pickle.load(f)
        
        # Create query embedding
        query_embedding = self.create_embeddings([query])[0]
        
        # Calculate similarities
        similarities = np.dot(index['embeddings'], query_embedding)
        
        # Get top results
        top_indices = np.argsort(similarities)[-top_k:][::-1]
        
        results = []
        for idx in top_indices:
            results.append({
                'chunk': index['chunks'][idx][:200] + '...',
                'score': similarities[idx],
                'index': idx
            })
        
        return results


def main():
    parser = argparse.ArgumentParser(description='Level 1 RAG Validation')
    parser.add_argument('--cache-dir', default='./rag_cache', help='Cache directory')
    parser.add_argument('--chunk-size', type=int, default=500, help='Chunk size')
    parser.add_argument('--skip-download', action='store_true', help='Skip download if cached')
    parser.add_argument('--ci', action='store_true', help='CI mode (minimal output)')
    args = parser.parse_args()
    
    if args.ci:
        print("Running in CI mode...")
    
    print("=== Level 1 RAG Validation ===\n")
    
    try:
        rag = SimpleRAG(cache_dir=args.cache_dir)
        
        # Step 1: Download
        text = rag.download_sample_text()
        print(f"   Text length: {len(text)} chars")
        
        # Step 2: Chunk
        chunks = rag.chunk_text(text, chunk_size=args.chunk_size)
        
        # Step 3: Create embeddings
        embeddings = rag.create_embeddings(chunks)
        
        # Step 4: Pickle
        index_file = rag.pickle_index(chunks, embeddings)
        
        # Step 5: Test search
        print("\n→ Testing search...")
        test_queries = [
            "What did Tom Sawyer do?",
            "Who is Huckleberry Finn?",
            "Tell me about the fence painting."
        ]
        
        all_passed = True
        for query in test_queries:
            if not args.ci:
                print(f"\nQuery: {query}")
            
            results = rag.search(query, index_file, top_k=2)
            
            if len(results) > 0 and results[0]['score'] > 0:
                if not args.ci:
                    for i, result in enumerate(results):
                        print(f"{i+1}. Score: {result['score']:.3f}")
                        print(f"   {result['chunk']}\n")
            else:
                print(f"❌ No results for query: {query}")
                all_passed = False
        
        if all_passed:
            print("✅ Level 1 validation complete!")
            return 0
        else:
            print("❌ Some tests failed")
            return 1
            
    except Exception as e:
        print(f"❌ Validation failed: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
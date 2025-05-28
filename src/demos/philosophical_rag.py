#!/usr/bin/env python3
"""
Philosophical RAG Demo: Stitch together meaning using Roget's Thesaurus
to connect concepts from Boethius, Kant, and Wittgenstein.

This demonstrates how RAG can create interesting cross-document connections
between seemingly unrelated texts spanning medieval, enlightenment, and
modern philosophy.
"""

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent.parent))

from src.rag.chunking import SimpleChunker
from src.rag.embeddings import EmbeddingGenerator
from src.rag.vector_store import FAISSVectorStore
from src.utils.pdf_extractor import PDFExtractor


class PhilosophicalRAG:
    """RAG system for philosophical texts with thesaurus augmentation."""

    def __init__(self):
        self.chunker = SimpleChunker(chunk_size=300, overlap=50)
        self.embedder = EmbeddingGenerator()
        self.vector_store = FAISSVectorStore(self.embedder.dimension)
        self.documents = []
        self.metadata = []

    def load_texts(self):
        """Load all philosophical texts and thesaurus."""
        data_dir = Path("data")

        # Load Boethius
        boethius_path = data_dir / "consolation_of_philosophy.txt"
        if boethius_path.exists():
            print("📜 Loading Boethius - Consolation of Philosophy...")
            with open(boethius_path, encoding='utf-8') as f:
                text = f.read()
                # Skip Project Gutenberg header
                start = text.find("BOOK I.")
                if start > 0:
                    text = text[start:]
                self._add_text(text, "Boethius", "Consolation of Philosophy")

        # Load Kant
        kant_path = data_dir / "critique_of_pure_reason.txt"
        if kant_path.exists():
            print("🧠 Loading Kant - Critique of Pure Reason...")
            with open(kant_path, encoding='utf-8') as f:
                text = f.read()
                # Skip header
                start = text.find("PREFACE")
                if start > 0:
                    text = text[start:]
                self._add_text(text[:200000], "Kant", "Critique of Pure Reason")  # First part only

        # Load Wittgenstein's Philosophical Grammar (PDF)
        wittgenstein_path = data_dir / "wittgenstein_philosophical_grammar.pdf"
        if wittgenstein_path.exists():
            print("🔍 Loading Wittgenstein - Philosophical Grammar...")
            try:
                extractor = PDFExtractor()
                text = extractor.extract_text(str(wittgenstein_path), max_pages=30)
                self._add_text(text, "Wittgenstein", "Philosophical Grammar")
            except Exception as e:
                print(f"Could not load Wittgenstein: {e}")

        # Load Roget's Thesaurus (PDF)
        thesaurus_path = data_dir / "rogets_thesaurus.pdf"
        if thesaurus_path.exists():
            print("📚 Loading Roget's Thesaurus...")
            try:
                extractor = PDFExtractor()
                text = extractor.extract_text(str(thesaurus_path), max_pages=50)
                self._add_text(text, "Roget", "Thesaurus")
            except Exception as e:
                print(f"Could not load thesaurus: {e}")

        print(f"\n✅ Loaded {len(self.documents)} document chunks")

    def _add_text(self, text: str, author: str, title: str):
        """Add text to the vector store with metadata."""
        chunks = self.chunker.chunk_text(text)

        for chunk in chunks:
            self.documents.append(chunk['text'])
            self.metadata.append({
                'author': author,
                'title': title,
                'chunk_index': chunk['index']
            })

        # Generate embeddings and add to store
        embeddings = self.embedder.generate([c['text'] for c in chunks])
        self.vector_store.add(
            embeddings,
            [c['text'] for c in chunks],
            [{'author': author, 'title': title, 'chunk_index': c['index']} for c in chunks]
        )

    def philosophical_query(self, question: str, n_results: int = 5):
        """Query across philosophical texts with thesaurus connections."""
        print(f"\n🤔 Question: {question}")
        print("=" * 60)

        # Get query embedding
        query_emb = self.embedder.generate(question)[0]

        # Search across all texts
        results = self.vector_store.search(query_emb, k=n_results)

        # Group by source
        by_source = {}
        for result in results:
            source = f"{result['metadata']['author']} - {result['metadata']['title']}"
            if source not in by_source:
                by_source[source] = []
            by_source[source].append(result)

        # Display results
        print("\n📖 Found connections across texts:")
        for source, source_results in by_source.items():
            print(f"\n{source}:")
            for result in source_results[:2]:  # Show top 2 from each source
                text = result['document'][:150] + "..."
                print(f"  • {text}")
                print(f"    (Relevance: {1 - result['distance']:.3f})")

        # Try to find thesaurus connections
        self._find_thesaurus_connections(question, results)

    def _find_thesaurus_connections(self, question: str, results):
        """Find thesaurus entries that might connect the concepts."""
        # Extract key terms from results
        key_terms = set()
        for result in results[:3]:
            # Simple term extraction (in production, use NLP)
            words = result['document'].lower().split()
            for word in words:
                if len(word) > 6:  # Longer words are often more meaningful
                    key_terms.add(word)

        print(f"\n🔗 Looking for thesaurus connections for terms: {list(key_terms)[:5]}...")

        # Search thesaurus for these terms
        thesaurus_results = []
        for term in list(key_terms)[:3]:
            term_emb = self.embedder.generate(term)[0]
            results = self.vector_store.search(term_emb, k=10)

            for result in results:
                if result['metadata']['author'] == 'Roget':
                    thesaurus_results.append((term, result))

        if thesaurus_results:
            print("\n📔 Thesaurus bridges found:")
            for term, result in thesaurus_results[:3]:
                print(f"  • '{term}' → {result['document'][:100]}...")

def demo_philosophical_connections():
    """Run interesting philosophical queries."""
    rag = PhilosophicalRAG()
    rag.load_texts()

    # Interesting cross-philosophy queries
    queries = [
        "What is the nature of happiness and fortune?",
        "How do we know what is real versus appearance?",
        "What is the relationship between reason and consolation?",
        "Can synthetic knowledge provide true wisdom?",
        "What connects virtue, knowledge, and the good life?",
        "How does language shape our understanding of reality?",
        "What is the meaning of meaning itself?"
    ]

    for query in queries:
        rag.philosophical_query(query)
        input("\nPress Enter for next query...")

if __name__ == "__main__":
    print("🎓 Philosophical RAG Demo")
    print("Connecting Boethius, Kant, Wittgenstein, and Roget's Thesaurus")
    print("-" * 50)

    # Check if files exist
    data_dir = Path("data")
    files_needed = [
        "consolation_of_philosophy.txt",
        "critique_of_pure_reason.txt",
        "wittgenstein_philosophical_grammar.pdf",
        "rogets_thesaurus.pdf"
    ]

    missing = [f for f in files_needed if not (data_dir / f).exists()]
    if missing:
        print(f"\n⚠️  Missing files: {missing}")
        print("Run: make download-all")
        sys.exit(1)

    demo_philosophical_connections()

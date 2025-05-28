"""Document chunking utilities for RAG pipelines."""

import re
from typing import Any


class SimpleChunker:
    """A simple document chunker with overlapping windows."""

    def __init__(self, chunk_size: int = 512, overlap: int = 50):
        self.chunk_size = chunk_size
        self.overlap = overlap

    def chunk_text(self, text: str) -> list[dict[str, Any]]:
        """Split text into overlapping chunks."""
        chunks = []
        start = 0
        text_length = len(text)

        while start < text_length:
            end = min(start + self.chunk_size, text_length)
            chunk_text = text[start:end]

            chunks.append({
                'text': chunk_text,
                'start': start,
                'end': end,
                'index': len(chunks)
            })

            # Move to next chunk with overlap
            start += (self.chunk_size - self.overlap)

        return chunks


class SentenceChunker:
    """Chunk text by sentences while respecting size limits."""

    def __init__(self, max_chunk_size: int = 512, min_chunk_size: int = 100):
        self.max_chunk_size = max_chunk_size
        self.min_chunk_size = min_chunk_size

    def chunk_text(self, text: str) -> list[dict[str, Any]]:
        """Split text into sentence-aware chunks."""
        # Simple sentence splitting (could be improved with spaCy)
        sentences = re.split(r'(?<=[.!?])\s+', text)

        chunks = []
        current_chunk = []
        current_size = 0

        for sentence in sentences:
            sentence_size = len(sentence)

            if current_size + sentence_size > self.max_chunk_size and current_chunk:
                # Save current chunk
                chunk_text = ' '.join(current_chunk)
                chunks.append({
                    'text': chunk_text,
                    'index': len(chunks),
                    'sentence_count': len(current_chunk)
                })
                current_chunk = [sentence]
                current_size = sentence_size
            else:
                current_chunk.append(sentence)
                current_size += sentence_size

        # Don't forget the last chunk
        if current_chunk:
            chunk_text = ' '.join(current_chunk)
            chunks.append({
                'text': chunk_text,
                'index': len(chunks),
                'sentence_count': len(current_chunk)
            })

        return chunks

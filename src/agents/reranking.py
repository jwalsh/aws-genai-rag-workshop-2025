"""Reranking module for improving RAG retrieval quality."""


import numpy as np
from sentence_transformers import CrossEncoder


class CrossEncoderReranker:
    """Rerank documents using a cross-encoder model."""

    def __init__(self, model_name: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"):
        self.model = CrossEncoder(model_name)

    def rerank(self,
               query: str,
               documents: list[str],
               top_k: int | None = None) -> list[tuple[int, float, str]]:
        """
        Rerank documents based on relevance to query.
        
        Returns list of (index, score, document) tuples.
        """
        # Create query-document pairs
        pairs = [[query, doc] for doc in documents]

        # Get reranking scores
        scores = self.model.predict(pairs)

        # Sort by score (descending)
        sorted_indices = np.argsort(scores)[::-1]

        # Return top-k results
        results = []
        limit = top_k if top_k else len(documents)

        for i in range(min(limit, len(documents))):
            idx = sorted_indices[i]
            results.append((idx, float(scores[idx]), documents[idx]))

        return results

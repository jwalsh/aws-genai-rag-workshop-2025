"""Embedding generation for RAG pipelines."""

import logging

import numpy as np

logger = logging.getLogger(__name__)


class EmbeddingGenerator:
    """Generate embeddings using sentence transformers or Bedrock."""

    def __init__(self, model_name: str = "all-MiniLM-L6-v2", use_bedrock: bool = False):
        self.model_name = model_name
        self.use_bedrock = use_bedrock
        self.model = None
        self.dimension = None

        if not use_bedrock:
            self._init_sentence_transformer()

    def _init_sentence_transformer(self):
        """Initialize sentence transformer model."""
        try:
            from sentence_transformers import SentenceTransformer
            self.model = SentenceTransformer(self.model_name)
            self.dimension = self.model.get_sentence_embedding_dimension()
            logger.info(f"Loaded {self.model_name} with dimension {self.dimension}")
        except ImportError:
            logger.error("sentence-transformers not installed")
            raise

    def generate(self, texts: str | list[str]) -> np.ndarray:
        """Generate embeddings for text or list of texts."""
        if isinstance(texts, str):
            texts = [texts]

        if self.use_bedrock:
            return self._generate_bedrock_embeddings(texts)
        else:
            return self.model.encode(texts, convert_to_numpy=True)

    def _generate_bedrock_embeddings(self, texts: list[str]) -> np.ndarray:
        """Generate embeddings using AWS Bedrock."""
        import json

        from ..utils.aws_client import get_bedrock_runtime_client

        client = get_bedrock_runtime_client()
        embeddings = []

        for text in texts:
            body = json.dumps({"inputText": text})
            response = client.invoke_model(
                modelId="amazon.titan-embed-text-v1",
                body=body
            )
            result = json.loads(response['body'].read())
            embeddings.append(result['embedding'])

        return np.array(embeddings)

    def similarity(self, embedding1: np.ndarray, embedding2: np.ndarray) -> float:
        """Calculate cosine similarity between two embeddings."""
        dot_product = np.dot(embedding1, embedding2)
        norm1 = np.linalg.norm(embedding1)
        norm2 = np.linalg.norm(embedding2)
        return float(dot_product / (norm1 * norm2))

    def batch_similarity(self, query_embedding: np.ndarray,
                        embeddings: np.ndarray) -> np.ndarray:
        """Calculate similarity between query and multiple embeddings."""
        # Normalize query
        query_norm = query_embedding / np.linalg.norm(query_embedding)

        # Normalize all embeddings
        norms = np.linalg.norm(embeddings, axis=1)
        normalized = embeddings / norms[:, np.newaxis]

        # Compute similarities
        similarities = np.dot(normalized, query_norm)
        return similarities
